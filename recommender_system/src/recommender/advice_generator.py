from typing import List, Dict, Any, Optional
from .cve_enricher import CveEnricher, cvss_to_severity

def _to_sc_dict(sc) -> Optional[Dict[str, Any]]:
    if sc is None:
        return None
    if isinstance(sc, dict):
        return sc
    try:
        return {
            "vendor": getattr(sc, "vendor", None),
            "product": getattr(sc, "product", None),
            "version": getattr(sc, "version", None),
        }
    except Exception:
        return None

def _base_actions_from_cve_row(cve_row: Dict[str, Any]) -> List[str]:
    actions = ["Apply vendor patch or update the affected software to a fixed version."]
    av = (cve_row.get("attack_vector") or "").upper()
    pr = (cve_row.get("privileges_required") or "").upper()
    ui = (cve_row.get("user_interaction") or "").upper()

    if av in ("NETWORK", "ADJACENT"):
        actions.append("Restrict exposure: tighten ingress ACLs/WAF rules to the affected service IP/port.")
        actions.append("Enable or raise logging around the vulnerable service to detect exploitation attempts.")
    if pr in ("NONE",):
        actions.append("Prioritize because no prior privileges are needed.")
    if ui in ("REQUIRED",):
        actions.append("User awareness: warn about the exploitation preconditions (opening files/links, etc.).")

    return actions

def _dedupe(seq: List[str]) -> List[str]:
    out, seen = [], set()
    for x in seq:
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out

class AdviceGenerator:
    """
    Genera recomendaciones combinando:
    - Heurísticas locales por CVE (según CVSS y vector).
    - Enriquecimiento externo (CISA KEV, NVD, OSV) cuando está disponible.
    - Contexto del host (servicios, CMS, AV) para hardening general.
    """

    enricher = CveEnricher()

    @staticmethod
    def _severity_from_cvss(base_score: Any, override: Optional[str] = None) -> str:
        if override:
            return override
        return cvss_to_severity(base_score)

    @staticmethod
    def _host_context_recs(host) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []

        # Normaliza componentes
        cms = _to_sc_dict(getattr(host, "cms", None))
        av  = _to_sc_dict(getattr(host, "antivirus", None))

        # 1) HTTPS/HSTS si hay 80/tcp
        try:
            has_http_80 = any(
                (ns.service or "").lower() == "http" and int(ns.port) == 80
                for ns in getattr(host, "network_services", []) or []
            )
        except Exception:
            has_http_80 = False

        if has_http_80:
            recs.append({
                "title": "Enforce HTTPS and validate certificates",
                "severity": "medium",
                "rationale": "Host exposes HTTP on TCP/80; cleartext increases exploit surface and credential leakage.",
                "actions": [
                    "Redirect HTTP→HTTPS and set HSTS.",
                    "Audit TLS certificate chain and expiration; prefer modern ciphers."
                ],
                "refs": []
            })

        # 2) CMS hardening
        if cms and (cms.get("vendor") or cms.get("product") or cms.get("version")):
            recs.append({
                "title": "Harden CMS stack",
                "severity": "high",
                "rationale": f"CMS detected ({cms}). CMS/plugins are frequent targets.",
                "actions": [
                    "Update core and all plugins/themes.",
                    "Restrict admin endpoints by IP/SSO; enable WAF virtual patching.",
                    "Daily backup & restore test."
                ],
                "refs": []
            })

        # 3) Antivirus sanity
        if av and (av.get("vendor") or av.get("product") or av.get("version")):
            recs.append({
                "title": "Verify AV engine and signature currency",
                "severity": "medium",
                "rationale": f"Antivirus detected ({av}). Ensure timely updates and on-access scanning.",
                "actions": [
                    "Check update schedule and last successful update time.",
                    "Enable on-access scanning for writable paths of exposed services."
                ],
                "refs": []
            })

        return recs

    @staticmethod
    def generate(host, cves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []

        # 1) Por cada CVE -> recomendación individual enriquecida
        for c in cves or []:
            cve_id = c.get("cve_id")
            base = c.get("base_score")
            severity = AdviceGenerator._severity_from_cvss(base)

            title = f"Mitigate {cve_id}" if cve_id else "Mitigate vulnerability"
            rationale = f"CVSS base={base or 'None'}, AV={c.get('attack_vector','n/a')}, PR={c.get('privileges_required','n/a')}, UI={c.get('user_interaction','n/a')}; {cve_id or ''}"

            actions = _base_actions_from_cve_row(c)
            refs = [{"type": "CVE", "id": cve_id}] if cve_id else []

            # Enriquecimiento externo (best-effort)
            ext = {}
            try:
                if cve_id:
                    ext = AdviceGenerator.enricher.enrich(cve_id)
            except Exception:
                ext = {}

            if ext.get("actions"):
                actions.extend(ext["actions"])
            if ext.get("references"):
                refs.extend(ext["references"])
            if ext.get("severity_override"):
                severity = ext["severity_override"]

            recommendations.append({
                "title": title,
                "severity": severity,
                "rationale": rationale,
                "actions": _dedupe(actions),
                "refs": refs,
            })

        # 2) Recs de contexto del host (HTTPS, CMS, AV…)
        recommendations.extend(AdviceGenerator._host_context_recs(host))

        return recommendations
