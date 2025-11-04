import os
import time
import json
import logging
from typing import Dict, List, Optional

import requests

log = logging.getLogger(__name__)
DEFAULT_TIMEOUT = int(os.getenv("RECS_TIMEOUT_SEC", "4"))

# Cache muy sencilla en memoria (PID local). Para prod, cambia a Redis.
_CACHE: Dict[str, Dict] = {}
_CACHE_TTL = int(os.getenv("RECS_CACHE_TTL", "86400"))  # 24h

def _cache_get(key: str) -> Optional[Dict]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["_ts"] > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return entry["data"]

def _cache_set(key: str, data: Dict):
    _CACHE[key] = {"_ts": time.time(), "data": data}

def cvss_to_severity(score: Optional[float]) -> str:
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "info"
    if s >= 9.0:  return "critical"
    if s >= 7.0:  return "high"
    if s >= 4.0:  return "medium"
    if s > 0:     return "low"
    return "info"

class CveEnricher:
    """
    Agrega señales de varias fuentes: KEV (CISA), NVD, OSV.
    Devuelve un dict con: actions[], references[], notes[], severity_override?
    Todo 'best-effort' y con timeouts cortos.
    """
    def __init__(self):
        self.nvd_api_key = os.getenv("NVD_API_KEY")  # opcional

    def enrich(self, cve_id: str) -> Dict:
        key = f"cve_enrich::{cve_id}"
        cached = _cache_get(key)
        if cached:
            return cached

        agg_actions: List[str] = []
        agg_refs: List[Dict] = []
        notes: List[str] = []
        severity_override: Optional[str] = None

        # 1) CISA KEV
        try:
            kev = self._from_cisa_kev(cve_id)
            if kev:
                agg_refs.append({"type": "CISA_KEV", "id": cve_id, "url": kev.get("url")})
                notes.append("Listed in CISA KEV (known exploited).")
                # subir severidad al menos a HIGH si está en KEV
                severity_override = "high"
                # acción típica
                agg_actions.append("Prioritize remediation: CVE is in CISA KEV (known exploited).")
        except Exception as e:
            log.debug("CISA KEV enrich failed: %s", e)

        # 2) NVD (si hay API key mejor; si no, público con rate-limit)
        try:
            nvd = self._from_nvd(cve_id)
            if nvd:
                agg_refs.append({"type": "NVD", "id": cve_id, "url": nvd.get("url")})
                # sugerencias genéricas si NVD trae configuration/workaround
                if nvd.get("workarounds"):
                    agg_actions.extend(nvd["workarounds"])
                if nvd.get("vendor_fixes"):
                    agg_actions.extend([f"Apply vendor fix: {x}" for x in nvd["vendor_fixes"]])
                if not severity_override and nvd.get("cvss"):
                    sev = cvss_to_severity(nvd["cvss"])
                    # no pisar KEV 'high' con algo menor
                    if sev in ("critical", "high"):
                        severity_override = sev
        except Exception as e:
            log.debug("NVD enrich failed: %s", e)

        # 3) OSV (útil para ecos OSS: libs, frameworks)
        try:
            osv = self._from_osv(cve_id)
            if osv:
                agg_refs.append({"type": "OSV", "id": cve_id, "url": osv.get("url")})
                if osv.get("fixes"):
                    agg_actions.extend([f"Upgrade package: {p}" for p in osv["fixes"]])
        except Exception as e:
            log.debug("OSV enrich failed: %s", e)

        # Limpieza y dedupe
        actions = []
        seen = set()
        for a in agg_actions:
            a2 = (a or "").strip()
            if not a2 or a2 in seen:
                continue
            seen.add(a2)
            actions.append(a2)

        out = {
            "actions": actions,
            "references": agg_refs,
            "notes": notes,
        }
        if severity_override:
            out["severity_override"] = severity_override

        _cache_set(key, out)
        return out

    def _from_cisa_kev(self, cve_id: str) -> Optional[Dict]:
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        r = requests.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for item in data.get("vulnerabilities", []):
            if item.get("cveID") == cve_id:
                return {"url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"}
        return None

    def _from_nvd(self, cve_id: str) -> Optional[Dict]:
        headers = {}
        if self.nvd_api_key:
            headers["apiKey"] = self.nvd_api_key
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
        r = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        items = data.get("vulnerabilities") or data.get("result", {}).get("CVE_Items")
        if not items:
            return None

        # CVSS y referencias básicas
        cvss = None
        vendor_fixes = []
        workarounds = []
        url_first = f"https://nvd.nist.gov/vuln/detail/{cve_id}"

        v = items[0]
        metrics = (v.get("cve", {}).get("metrics") or v.get("cve", {}).get("impact")) or {}
        # v3.1 -> cvssMetricV31, v3.0 -> cvssMetricV30
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            arr = (v.get("cve", {}).get("metrics") or {}).get(key) if v.get("cve") else (v.get("impact") or {}).get(key)
            if isinstance(arr, list) and arr:
                cvss = arr[0].get("cvssData", {}).get("baseScore")
                break

        # Pistas de soluciones (ligeras; NVD no siempre trae claro 'workaround')
        refs = (v.get("cve", {}).get("references", {}).get("referenceData") if v.get("cve") else None) or []
        for ref in refs:
            urlref = ref.get("url", "")
            if "advisories" in urlref or "security" in urlref or "vendor" in urlref:
                vendor_fixes.append(urlref)
            if "workaround" in (ref.get("name", "").lower() + urlref.lower()):
                workarounds.append(f"See workaround at {urlref}")

        return {"cvss": cvss, "vendor_fixes": vendor_fixes, "workarounds": workarounds, "url": url_first}

    def _from_osv(self, cve_id: str) -> Optional[Dict]:
        url = "https://api.osv.dev/v1/query"
        r = requests.post(url, json={"query": {"ids": [cve_id]}}, timeout=DEFAULT_TIMEOUT)
        if r.status_code >= 400:
            # fallback a /v1/vulns/<CVE>
            r2 = requests.get(f"https://api.osv.dev/v1/vulns/{cve_id}", timeout=DEFAULT_TIMEOUT)
            if r2.status_code >= 400:
                return None
            data = r2.json()
        else:
            data = r.json()
        fixes = []
        url_first = None
        vulns = data.get("vulns") if isinstance(data, dict) else None
        if vulns:
            v = vulns[0]
            url_first = f"https://osv.dev/vulnerability/{v.get('id', cve_id)}"
            for a in v.get("affected", []):
                for r in a.get("ranges", []):
                    for ev in r.get("events", []):
                        if ev.get("fixed"):
                            fixes.append(f"{a.get('package', {}).get('name')}@{ev['fixed']}")
        return {"fixes": fixes, "url": url_first}
