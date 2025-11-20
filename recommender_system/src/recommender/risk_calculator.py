from recommender.comparators import *
from recommender.model.path_type import PathType
import math

class RiskCalculator:
    """
    Calculates risk scores between attacked host and host found in close
    proximity.
    """

    def __init__(self, db_client, config):
        self.__db_client = db_client
        self.__config = config
        self.__comparators = []

        self.__path_coefficients = {
            PathType.Subnet: self.__config["path"]["subnet"],
            PathType.Organization: self.__config["path"]["organization_unit"],
            PathType.Contact: self.__config["path"]["contact"],
        }

        self.__available_comparators = [
            "os",
            "antivirus",
            "cms",
            "cve_cumulative",
            "event_cumulative",
            "net_service"
        ]

        self.__initialize_comparators()

    def calculate_risk_scores(self, attacked_host, compared_hosts):
        """
        Calculates and sets risk score for every host in compared_hosts list.
        :param attacked_host: Attacked host to which hosts are compared to
        :param compared_hosts: List of hosts which risk should be calculated
        :return: None
        """
        self.__set_reference_host(attacked_host)

        for host in compared_hosts:
            host.risk = self._calculate_risk_score(host)

    def calculate_similarities(self, host1, host2):
        """
        Calculates similarity of two hosts. Returns result similarity and dictionary of all partial similarities.
        :param host1: First host
        :param host2: Second host
        :return: Similarity and dictionary of partial similarities
        """
        self.__set_reference_host(host1)

        similarity = 1
        partial_similarity_vector = dict()

        for comparator in self.__comparators:
            partial_similarity = comparator.calc_partial_similarity(host2)
            partial_similarity_vector[comparator.get_name()] = partial_similarity
            similarity *= partial_similarity

        return similarity, partial_similarity_vector

    def __initialize_comparators(self):
        """
        Initialize comparators that should be applied by config.
        :return: None
        """
        self.__comparators = []

        for comparator in self.__available_comparators:
            if self.__config["comparators"][comparator]["apply"]:
                config = self.__config["comparators"][comparator]
                comp = None
                match comparator:
                    case "os":
                        comp = OsComparator(config)
                    case "antivirus":
                        comp = AntivirusComparator(config)
                    case "cms":
                        comp = CmsComparator(config)
                    case "cve_cumulative":
                        comp = CveComparator(
                            config, self.__db_client.get_total_cve_count())
                    case "event_cumulative":
                        comp = EventComparator(
                            config, self.__db_client.get_total_event_count())
                    case "net_service":
                        comp = NetServicesComparator(config)

                if comp is not None:
                    self.__comparators.append(comp)

    def explain_risk(self, attacked_host, compared_host, log: bool = False):
        """
        Devuelve el desglose del cálculo de riesgo entre attacked_host (referencia)
        y compared_host (candidato): similitudes parciales por comparador, multiplicador
        de path, distancia, similitud total y riesgo final.

        :param attacked_host: Host de referencia (atacado)
        :param compared_host: Host comparado
        :param log: si True, hace logging INFO del cálculo
        :return: dict con {ip, distance, path_types, path_multiplier, partials, similarity, risk}
        """
        import logging

        # Fija host de referencia para todos los comparadores
        self.__set_reference_host(attacked_host)

        parts = {}
        similarity = 1.0

        for comparator in self.__comparators:
            ps = comparator.calc_partial_similarity(compared_host)

            # sanea valores inválidos
            if ps is None or math.isnan(ps) or math.isinf(ps):
                ps = 0.0

            parts[comparator.get_name()] = float(ps)
            similarity *= ps

        path_multiplier = 1.0
        path_types = getattr(compared_host, "path_types", []) or []
        if self.__config["path"]["apply"]:
            for pt in path_types:
                path_multiplier *= float(self.__path_coefficients.get(pt, 1.0))

        distance = getattr(compared_host, "distance", 1) or 1
        if distance <= 0:
            distance = 1

        # Riesgo final
        risk = (similarity * path_multiplier) / distance

        out = {
            "ip": getattr(compared_host, "ip", getattr(compared_host, "id", "?")),
            "distance": int(distance),
            "path_types": [pt.name if hasattr(pt, "name") else str(pt) for pt in path_types],
            "path_multiplier": path_multiplier,
            "partials": parts,
            "similarity": similarity,
            "risk": risk,
        }

        if log:
            logging.getLogger(__name__).info("EXPLAIN %s", out)

        return out

    def explain_risk_from_ips(self, ref_ip: str, cmp_ip: str, log: bool = False):
        """
        Helper: obtiene los hosts desde Neo4j y llama a explain_risk().
        """
        ref = self.__db_client.get_host_by_ip(ref_ip)
        cmp_ = self.__db_client.get_host_by_ip(cmp_ip)
        return self.explain_risk(ref, cmp_, log=log)

    def __set_reference_host(self, attacked_host):
        """
        Sets reference host to every comparator in the comparator list.
        :return: None
        """
        for comparator in self.__comparators:

            comparator.set_reference_host(attacked_host)
            
    def _calculate_risk_score(self, compared_host):
        """
        Compares attacked host with given host by applying the list
        of comparators. Result similarity is divided by distance between hosts
        and multiplied by path coefficient.
        :param compared_host: Host to be compared with attacked host
        :return: Risk score between attacked host and compared host
        """
        import math
        import logging

        logger = logging.getLogger(__name__)


        if hasattr(compared_host, 'id') and hasattr(self, '_RiskCalculator__reference_host'):
            if compared_host.id == self.__reference_host.id:
                logger.warning(f"Host {compared_host.id} comparado consigo mismo. Riesgo ignorado.")
                return 0.0 

        similarity = 1.0

        for comparator in self.__comparators:
            partial_similarity = comparator.calc_partial_similarity(compared_host)

            if partial_similarity is None or math.isnan(partial_similarity) or math.isinf(partial_similarity):
                logger.warning(f"Similitud inválida ({partial_similarity}) en {comparator.get_name()} — usando 0.0")
                partial_similarity = 0.0

            similarity *= partial_similarity

        if self.__config["path"]["apply"]:
            for path_type in compared_host.path_types:
                coefficient = self.__path_coefficients.get(path_type, 1.0)
                similarity *= coefficient

        distance = compared_host.distance

        if distance is None or distance <= 0:
            logger.warning(f"Distancia inválida ({distance}) para host {compared_host.id}. Ajustando a 1.0")
            distance = 1.0  # Valor mínimo forzado

        if similarity is None or math.isnan(similarity) or math.isinf(similarity):
            logger.warning(f"Similitud global inválida ({similarity}) — riesgo = 0.0")
            return 0.0

        risk_score = similarity / distance

        if math.isnan(risk_score) or math.isinf(risk_score):
            logger.warning(f"Riesgo inválido calculado (S={similarity}, D={distance}) => R={risk_score}")
            return 0.0

        return min(max(risk_score, 0.0), 100.0)
