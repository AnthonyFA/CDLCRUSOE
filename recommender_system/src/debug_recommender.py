#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

# Añadir src/ al path
base = os.path.abspath(os.path.dirname(__file__))
if base not in sys.path:
    sys.path.insert(0, base)

from recommender.neo4j_client import Neo4jClient
from recommender.recommender import Recommender

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s] %(message)s'
)

logger = logging.getLogger(__name__)

# CONFIGURACIÓN HARDCODEADA (igual que default_config.json)
CONFIG = {
    "max_distance": 2,
    "path": {
        "apply": True,
        "subnet": 1,
        "organization_unit": 1.25,
        "contact": 1.15
    },
    "comparators": {
        "os": {
            "apply": True,
            "critical_bound": 0.5,
            "diff_value": 0.3,
            "vendor": 0.6,
            "product": 0.3,
            "version": 0.1
        },
        "antivirus": {
            "apply": False,  # Desactivado para simplificar
            "critical_bound": 0.5,
            "diff_value": 0.4,
            "vendor": 0.6,
            "product": 0.25,
            "version": 0.15
        },
        "cms": {
            "apply": True,
            "require_open_ports": False,
            "critical_bound": 0.5,
            "diff_value": 0.4,
            "vendor": 0.6,
            "product": 0.25,
            "version": 0.15
        },
        "net_service": {
            "apply": True,
            "critical_bound": 0.25,
            "diff_value": 0.1
        },
        "cve_cumulative": {
            "apply": False,  # Desactivado temporalmente para debug
            "critical_bound": 0.29492334
        },
        "event_cumulative": {
            "apply": False,  # Desactivado temporalmente para debug
            "critical_bound": 0.036752
        }
    }
}

logger.info(f"Comparadores activos: {[k for k, v in CONFIG['comparators'].items() if v.get('apply')]}")

# Conectar a Neo4j
db = Neo4jClient(
    os.getenv("NEO4J_URL", "bolt://localhost:7687"),
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "password"),
    logger
)

# Crear recommender y buscar hosts cercanos al pivot
PIVOT_IP = "10.1.4.44"

recommender = Recommender(CONFIG, db, logger)

logger.info(f"\n{'='*60}")
logger.info(f"PIVOT: {PIVOT_IP}")
logger.info(f"{'='*60}\n")

try:
    recommender.get_attacked_host_by_ip(PIVOT_IP)
    logger.info(f"Pivot host encontrado: {recommender.attacked_host}")
    
    # Mostrar atributos del pivot
    pivot = recommender.attacked_host
    logger.info(f"  IP: {pivot.ip}")
    logger.info(f"  OS: {pivot.os_component}")
    logger.info(f"  CMS: {getattr(pivot, 'cms', None)}")
    logger.info(f"  Antivirus: {getattr(pivot, 'antivirus', None)}")
    logger.info(f"  CVE count: {getattr(pivot, 'cve_count', None)}")
    logger.info(f"  Event count: {getattr(pivot, 'security_event_count', None)}")
    
    # Buscar hosts cercanos
    logger.info(f"\n{'='*60}")
    logger.info("Buscando hosts cercanos...")
    logger.info(f"{'='*60}\n")
    
    recommender.recommend_hosts()
    
    logger.info(f"\nTotal hosts encontrados: {len(recommender.host_list)}")
    
    # Mostrar primeros 10 hosts con sus atributos y riesgo
    for i, host in enumerate(recommender.host_list[:10]):
        logger.info(f"\n--- Host {i+1}: {host.ip} ---")
        logger.info(f"  Risk: {host.risk}")
        logger.info(f"  Distance: {host.distance}")
        logger.info(f"  Path types: {host.path_types}")
        logger.info(f"  OS: {host.os_component}")
        logger.info(f"  CMS: {getattr(host, 'cms', None)}")
        logger.info(f"  Antivirus: {getattr(host, 'antivirus', None)}")
        logger.info(f"  CVE count: {getattr(host, 'cve_count', None)}")
        logger.info(f"  Event count: {getattr(host, 'security_event_count', None)}")

except Exception as e:
    logger.error(f"Error durante la recomendación: {e}", exc_info=True)

finally:
    db.close()
    logger.info("\nConexión a Neo4j cerrada.")
