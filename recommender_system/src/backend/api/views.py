import logging
import sys
from json import load, dumps, loads
from os.path import exists
from collections import Counter

from django.http import JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.core.files.storage import default_storage

from recommender.neo4j_client import Neo4jClient
from recommender.recommender import Recommender
from recommender.advice_generator import AdviceGenerator

from utils.json_encoder import Encoder
from utils.mean_bound_calculator import MeanBoundCalculator
from utils.validator import Validator


def get_logger():
    """
    Initializes logger to output to stdout instead of a file.
    :return: Initialized logger
    """
    logger = logging.getLogger("neo4j")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    log_format = "[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s"
    handler.setFormatter(logging.Formatter(log_format))
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def get_db_client():
    """
    Returns a new Neo4j client initialized with connection details from
    Django settings file.
    :return: Neo4j client
    """
    return Neo4jClient(settings.DATABASES['default']['URL'],
                       settings.DATABASES['default']['USER'],
                       settings.DATABASES['default']['PASSWORD'],
                       get_logger())


def initialize_recommender(ip, domain, db_client):
    """
    Initializes recommender object for views. IP or domain must be given.
    :param ip: IP of the attacked host
    :param domain: Domain of the attacked host
    :param db_client: Neo4j database client
    :return: Initialized recommender or None if IP or domain is not given
    """
    with default_storage.open(settings.CONFIG) as config_stream:
        config = load(config_stream)

    recommend = Recommender(config, db_client, get_logger())

    if ip is not None:
        recommend.get_attacked_host_by_ip(ip)
    elif domain is not None:
        recommend.get_attacked_host_by_ip(domain)
    else:
        return None

    return recommend


def parse_query_params(query_params):
    """
    Parses query parameters for recommender endpoints (IP or domain name).
    :param query_params: Dictionary of query params from REST framework Request
    :return: Tuple of IP and domain (one can be None)
    """
    if "ip" not in query_params and "domain" not in query_params:
        raise ValueError("IP or domain parameter is required.")

    if "ip" in query_params and not Validator.validate_ip(query_params["ip"]):
        raise ValueError("Invalid IP.")

    if "domain" in query_params \
            and not Validator.validate_ip(query_params["domain"]):
        raise ValueError("Invalid domain.")

    return query_params.get("ip", None), query_params.get("domain", None)


def _is_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


@api_view(["GET"])
def attacked_host(request):
    """
    Returns host info and recommendations. Add ?pretty=1 to pretty-print JSON
    and include a 'meta' section with useful counters.
    """
    pretty = _is_truthy(request.query_params.get("pretty"))

    with get_db_client() as db_client:
        try:
            ip, domain = parse_query_params(request.query_params)
            recommend = initialize_recommender(ip, domain, db_client)

            if recommend is None or recommend.attacked_host is None:
                return JsonResponse({"error": "Attacked host not found"}, status=404)

            # --- CVEs + recomendaciones ---
            cves = db_client.get_cves_for_host(recommend.attacked_host.ip)
            recs = AdviceGenerator.generate(recommend.attacked_host, cves)

            # Serializa Host con tu Encoder existente
            host_payload = loads(dumps(recommend.attacked_host, cls=Encoder))

            # --- META: contadores y agregados útiles para UI ---
            # CVEs únicos referenciados en refs (en las recomendaciones)
            unique_cves = {
                r.get("id")
                for rec in recs
                for r in rec.get("refs", [])
                if r.get("type") == "CVE" and r.get("id")
            }
            severity_hist = Counter(rec.get("severity", "info") for rec in recs)

            meta = {
                "api_version": "1.1",
                "host_ip": recommend.attacked_host.ip,
                "cve_host_count": host_payload.get("cve_count"),
                "cve_refs_count": len(unique_cves),
                "recommendation_counts": {
                    "total": len(recs),
                    "by_severity": dict(severity_hist),
                },
            }

            # Construye el payload final colocando 'meta' primero
            payload = {"meta": meta, **host_payload, "recommendations": recs}

        except (ValueError, IOError) as e:
            return JsonResponse({"error": {"message": str(e)}}, status=400)

    # Pretty-print opcional sin romper contrato
    dumps_params = {"ensure_ascii": False}
    if pretty:
        dumps_params.update({"indent": 2, "sort_keys": False})

    return JsonResponse(payload, safe=False, json_dumps_params=dumps_params)


@api_view(["GET"])
def recommended_hosts(request):
    """
    Returns the recommended host list. Add ?pretty=1 to pretty-print JSON.
    Mantiene contrato: la respuesta es SIEMPRE un array JSON.
    """
    pretty = _is_truthy(request.query_params.get("pretty"))

    with get_db_client() as db_client:
        try:
            ip, domain = parse_query_params(request.query_params)
            recommend = initialize_recommender(ip, domain, db_client)

            if not recommend:
                return JsonResponse({"error": "Recommender initialization failed"}, status=500)

            recommend.recommend_hosts()

            if not recommend.host_list:
                return JsonResponse({"error": "No recommended hosts found"}, status=404)

            payload = loads(dumps(recommend.host_list, cls=Encoder))


            for item in payload:
                r = item.get("risk")
                if isinstance(r, list) and r:
                    item["risk"] = float(r[0])

        except (ValueError, IOError) as e:
            return JsonResponse({"error": {"message": str(e)}}, status=400)

    dumps_params = {"ensure_ascii": False}
    if pretty:
        dumps_params.update({"indent": 2, "sort_keys": False})

    return JsonResponse(payload, safe=False, json_dumps_params=dumps_params)



@api_view(["GET", "PUT", "PATCH"])
def configuration(request):
    """
    View for getting and updating the recommender configuration file. Supports
    three methods: GET for getting saved config, PUT for setting a new config
    and PATCH for calculating mean bounds in configuration.
    :param request: REST framework request
    :return: JsonResponse or Response
    """
    if request.method == "GET":
        if not default_storage.exists(settings.CONFIG):
            return JsonResponse(
                {"error": {"message": "Config file doesn't exist"}},
                status=404)

        with default_storage.open(settings.CONFIG, mode="r") as config_stream:
            config = load(config_stream)

        return JsonResponse(config, status=200)

    if request.method == "PUT":
        status_code = 201 if not exists(settings.CONFIG) else 200

        with default_storage.open(settings.CONFIG, mode="w") as config_stream:
            config_stream.write(dumps(request.data, indent=4))

        return JsonResponse(request.data, status=status_code)

    if request.method == "PATCH":
        if not exists(settings.CONFIG):
            return JsonResponse(
                {"error": {"message": "Config file doesn't exist"}},
                status=404)

        with default_storage.open(settings.CONFIG, mode="r") as config_stream:
            config = load(config_stream)

        with get_db_client() as db_client:
            MeanBoundCalculator.calculate_mean_bounds(db_client, config)

        with default_storage.open(settings.CONFIG, mode="w") as config_stream:
            config_stream.write(dumps(config, indent=4))

        return JsonResponse(config, status=200)

    return Response(status=500)
