#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

# 1) Asegurar que podemos importar 'recommender'
# Estás en: /home/csa/CDLCRUSOE/recommender_system/src/recommender
# El paquete real está en /home/csa/CDLCRUSOE/recommender_system/src
BASE = os.path.join(os.getcwd(), "..")          # subir un nivel desde /src/recommender
BASE = os.path.abspath(BASE)

if os.path.isdir(BASE) and BASE not in sys.path:
    sys.path.append(BASE)

# Ahora 'src' está en sys.path y el paquete 'recommender' funciona
from recommender.neo4j_client import Neo4jClient
from recommender.risk_calculator import RiskCalculator

logging.basicConfig(level=logging.INFO)

CFG = {
    "max_distance": 3,
    "path": { "apply": True, "subnet": 1.5, "organization_unit": 1.25, "contact": 1.8 },
    "comparators": {
        "os":  { "apply": True,  "critical_bound": 0.5, "diff_value": 0.3, "vendor": 0.5, "product": 0.3, "version": 0.2 },
        "cms": { "apply": True,  "critical_bound": 0.5, "diff_value": 0.4, "vendor": 0.8, "product": 0.15, "version": 0.05, "require_open_ports": False },
        "antivirus":   { "apply": False, "critical_bound": 0.5, "diff_value": 0.4, "vendor": 0.6, "product": 0.25, "version": 0.15 },
        "net_service": { "apply": True,  "critical_bound": 0.25, "diff_value": 0.7 },
        "cve_cumulative":   { "apply": False, "critical_bound": 0.29492334 },
        "event_cumulative": { "apply": False, "critical_bound": 0.036752 }  
    }
}

# 3) Entradas (overridable por entorno)
PIVOT = os.getenv("PIVOT", "10.1.4.44")
_targets_csv = os.getenv(
    "TARGETS_CSV",
    "10.1.4.45,10.1.4.48,10.1.4.49,10.1.2.26,10.1.2.25,10.1.2.29",
)
TARGETS = [t.strip() for t in _targets_csv.split(",") if t.strip()]

def main():
    # 4) Crear cliente Neo4j y RiskCalculator
    db = Neo4jClient(
        os.getenv("NEO4J_URL", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "password"),
        logging.getLogger(__name__),
    )

    rc = RiskCalculator(db, CFG)

    rows = []

    for t in TARGETS:
        try:
            exp = rc.explain_risk_from_ips(PIVOT, t, log=False)
            parts = exp.get("partials") or {}
            rows.append(
                {
                    "target": t,
                    "OS": parts.get("os") or parts.get("OS"),
                    "Antivirus": parts.get("antivirus") or parts.get("Antivirus"),
                    "CMS": parts.get("cms") or parts.get("CMS"),
                    "NetService": parts.get("net_service")
                    or parts.get("NetService"),
                    "CVE": parts.get("cve_cumulative") or parts.get("CVE"),
                    "Event": parts.get("event_cumulative") or parts.get("Event"),
                    "distance": exp.get("distance"),
                    "path_types": exp.get("path_types"),
                    "path_multiplier": exp.get("path_multiplier"),
                    "similarity": exp.get("similarity"),
                    "risk": exp.get("risk"),
                }
            )
        except Exception as e:
            rows.append({"target": t, "error": str(e)})

    db.close()

    # Ordenar por riesgo descendente
    rows.sort(
        key=lambda r: r.get("risk", 0.0) if isinstance(r, dict) else 0.0,
        reverse=True,
    )

    # 5) Salida "raw"
    print("ROWS:")
    print(rows)

    # 6) Salida JSON prettificada (para pegar en el TFM)
    print("\nJSON PRETTY:")
    print(json.dumps(rows, indent=2))

if __name__ == "__main__":
    main()
