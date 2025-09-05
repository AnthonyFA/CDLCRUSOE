from neo4j import GraphDatabase

from recommender.model import SoftwareComponent
from recommender.model.host import Host, HostWithScore
from recommender.model.network_service import NetworkService
from recommender.model.path_type import PathType
import logging
import os

log_path = "/tmp/recommender_debug.log"
logging.basicConfig(
    filename=log_path,
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


class Neo4jClient:
    """
    Manages connection with the Neo4j database.
    """

    def __init__(self, url, user, password, logger):
        self.__driver = GraphDatabase.driver(url, auth=(user, password))
        self.__logger = logger

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        """
        Closes connection with the Neo4j database.
        :return: None
        """
        self.__driver.close()

    def get_host_by_domain(self, domain):
        """
        Finds the host in the database by its domain address and initialize its
        properties. Throws ValueError when the given domain doesn't exist in
        the database.
        :param domain: Domain name string
        :return: Host object
        """

        with self.__driver.session() as session:
            result = session.read_transaction(self.__get_ip_query, domain)

            # Domain doesn't exist in the database
            if not result:
                self.__logger.critical(
                    "Given domain doesn't resolve to any IP")
                raise ValueError("Given domain doesn't resolve to any IP")
        return self.get_host_by_ip(result["ip"]["address"])

    def get_host_by_ip(self, ip):
        """
        Finds the host in the database by its IP address and initialize its
        properties. Throws ValueError when given IP doesn't exist in
        the database.
        :param ip: IP string
        :return: Host object or None if a host with given IP does not exist
        """

        with self.__driver.session() as session:
            result = session.read_transaction(self.__get_host_by_ip_query,
                                              str(ip))

            # IP doesn't exist in the database
            if not result:
                msg = f"Given IP ({str(ip)}) was not found in the database."
                self.__logger.critical(msg)
                raise ValueError(msg)

            # Create new host
            new_host = Host(ip, result["domains"], result["contacts"],
                            result["os"], result["antivirus"], result["cms"],
                            result["cve_count"], result["event_count"])

            # Get network services
            new_host.network_services = self.__get_network_services(
                ip, session, result["start"], result["end"])

        return new_host

    def find_close_hosts(self, ip, max_distance):
        self.__logger.info(f"▶️ find_close_hosts({ip}, {max_distance})")
        with open("/tmp/recommender_debug.txt", "a") as f:
            f.write(f"Entrando a find_close_hosts para IP: {ip}\n")

        try:
            with self.__driver.session() as session:
                path_types = {
                    "subnet": PathType.Subnet,
                    "organization": PathType.Organization,
                    "contact": PathType.Contact
                }

                result_list = []
                rows = session.read_transaction(self.__find_close_hosts_query, ip, max_distance)
                
                self.__logger.info(f"📦 {len(rows)} rows fetched from traverse.findCloseHosts")
                print(f"ENTRANDO EN find_close_hosts PARA {ip}")
                for row in rows:
                    try:
                        host_path_types = [path_types[path] for path in row["path_types"]]
                        new_host = HostWithScore(
                            row["ip"], row["domains"], row["contacts"],
                            row["os"], row["antivirus"], row["cms"],
                            row["cve_count"], row["event_count"],
                            row["distance"], host_path_types
                        )

                        new_host.network_services = self.__get_network_services(
                            row["ip"], session, row["start"], row["end"]
                        )
                        result_list.append(new_host)
                    except Exception as inner_ex:
                        self.__logger.warning(f"⚠️ Skipped one row due to: {inner_ex}")

                self.__logger.info(f"✅ find_close_hosts finished. Hosts: {len(result_list)}")
                return result_list

        except Exception as e:
            self.__logger.error(f"🔥 Exception in find_close_hosts: {e}", exc_info=True)
            return []

    def get_total_cve_count(self):
        """
        Counts the total number of CVEs that were identified in the software
        running on devices in the network.
        :return: Total number of CVEs
        """

        with self.__driver.session() as session:
            result = session.read_transaction(self.__get_total_cve_count_query)

        return result["cve_count"]

    def get_total_event_count(self):
        """
        Counts the total number of security events that happened in the
        network.
        :return: Total number of security events
        """

        with self.__driver.session() as session:
            result = session.read_transaction(
                self.__get_total_event_count_query)

        return result["event_count"]

    def get_distance(self, ip1, ip2, max_distance):
        """
        Returns distance between two ip addresses. Throws exception, if no path shorter or equal than max_distance
        exists.
        :param ip1: First IP address
        :param ip2: Second IP address
        :param max_distance: Upper bound for distance searching
        :return: Distance
        """
        with self.__driver.session() as session:
            result = session.read_transaction(
                self.__get_distance_query, ip1, ip2, max_distance)

            if result is None:
                raise ValueError(f"No path shorter or equal to {max_distance} exists between {ip1} and {ip2}.")

            return result["length"]

    def __get_network_services(self, ip, session, start, end):
        """
        Finds network services in the database which runs on a host with
        given IP.
        :param ip: IP address of a host
        :param session: Database session
        :param start: Start of latest OS runtime
        :param end: End of latest OS runtime
        :return: List of net services
        """

        result = session.read_transaction(self.__get_network_services_query,
                                          ip, start, end)

        services = []
        for row in result:
            service = NetworkService(row["port"],
                                     row["protocol"],
                                     row["service"])
            services.append(service)
        return services

    def get_all_os_versions(self):
        """
        Returns all OS versions from the database.
        :return: List of SoftwareComponent.
        """
        with self.__driver.session() as session:
            return session.read_transaction(self.__get_all_software_query,
                                            "os_component")

    def get_all_cms_versions(self):
        """
        Gets the average number of events that occurred on a host.
        :return: Average number of events
        """
        with self.__driver.session() as session:
            return session.read_transaction(self.__get_all_software_query,
                                            "cms_client")

    def get_all_antivirus_versions(self):
        """
        Returns all antivirus versions from the database.
        :return: List of SoftwareComponent.
        """
        with self.__driver.session() as session:
            return session.read_transaction(self.__get_all_software_query,
                                            "services_component")

    def get_average_event_count(self):
        """
        Gets the average number of events on a host.
        :return: Average number of events
        """
        with self.__driver.session() as session:
            return session.read_transaction(
                self.__get_average_event_count_query)["avg_event"]

    def get_average_cve_count(self):
        """
        Gets the average number of vulnerabilities on a host.
        :return: Average number of CVEs
        """
        with self.__driver.session() as session:
            return session.read_transaction(
                self.__get_average_cve_count_query)["avg_cve"]

    # CYPHER queries

    @staticmethod
    def __get_ip_query(tx, domain):
        query = (
            "MATCH (ip:IP)-[:RESOLVES_TO]->(domain:DomainName) "
            "WHERE $domain IN domain.domain_name "
            "RETURN ip"
        )
        result = tx.run(query, domain=domain)
        return result.single()

    @staticmethod
    def __get_network_services_query(tx, ip, start, end):
        query = (
            "MATCH (node:Node)-[:HAS_ASSIGNED]->(ip:IP) "
            "WHERE ip.address = $ip "
            "MATCH (node)-[:IS_A]->(host:Host) "
            "MATCH (service:NetworkService)-[r:ON]->(host) "
            "WHERE NOT (r.end < $start OR r.start > $end)"
            "RETURN service"
        )
        result = tx.run(query, ip=ip, start=start, end=end)
        return [row["service"] for row in result]

    @staticmethod
    def __find_close_hosts_query(tx, ip, max_distance):
        query = (
            # Traverse from given IP address node
            "CALL traverse.findCloseHosts($ip, $max_distance) "
            "YIELD ip AS ip_string, distance, path_types "

            # Obtain information about found hosts
            f"{Neo4jClient.__get_host_and_ip_subquery()}"
            f"{Neo4jClient.__get_os_subquery()}"
            f"{Neo4jClient.__get_antivirus_subquery()}"
            f"{Neo4jClient.__get_cms_subquery()}"
            f"{Neo4jClient.__get_host_event_count_subquery()}"
            f"{Neo4jClient.__get_host_cve_count_subquery()}"
            f"{Neo4jClient.__get_contacts_subquery()}"
            f"{Neo4jClient.__get_domains_subquery()}"

            "RETURN ip.address AS ip, domains, os, contacts, antivirus, cms, "
            "event_count, cve_count, start, end, distance, path_types"
        )
        result = tx.run(query, ip=ip, max_distance=max_distance)
        return [row for row in result]

    @staticmethod
    def __get_host_by_ip_query(tx, ip):
        query = (
            "WITH $ip AS ip_string "
            # Get operating system running on host + optional antivirus and cms
            f"{Neo4jClient.__get_host_and_ip_subquery()}"
            f"{Neo4jClient.__get_os_subquery()}"
            f"{Neo4jClient.__get_antivirus_subquery()}"
            f"{Neo4jClient.__get_cms_subquery()}"
            f"{Neo4jClient.__get_host_event_count_subquery()}"
            f"{Neo4jClient.__get_host_cve_count_subquery()}"
            f"{Neo4jClient.__get_contacts_subquery()}"
            f"{Neo4jClient.__get_domains_subquery()}"

            # Return found components + timestamp of OS for finding network 
            # services
            "RETURN domains, os, contacts, antivirus, cms, event_count, "
            "cve_count, start, end"
        )

        result = tx.run(query, ip=ip)
        return result.single()

    @staticmethod
    def __get_total_event_count_query(tx):
        query = (
            "MATCH (e:SecurityEvent) "
            "RETURN count(e) AS event_count"
        )

        result = tx.run(query)
        return result.single()

    @staticmethod
    def __get_total_cve_count_query(tx):
        query = (
            "MATCH (cve:Vulnerability) "
            "RETURN count(DISTINCT cve) AS cve_count"
        )

        result = tx.run(query)
        return result.single()

    @staticmethod
    def __get_all_software_query(tx, tag):
        query = (
            "MATCH (sw:SoftwareVersion) "
            "WHERE sw.tag = $tag "
            "RETURN DISTINCT sw.version"
        )
        result = tx.run(query, tag=tag)
        return [SoftwareComponent(tag, row["sw.version"]) for row in result]

    @staticmethod
    def __get_average_event_count_query(tx):
        query = (
            "MATCH (ip:IP)-[:SOURCE_OF]->(event:SecurityEvent) "
            "WITH ip, count(event) AS event_count "
            "RETURN avg(event_count) AS avg_event"
        )

        result = tx.run(query)
        return result.single()

    @staticmethod
    def __get_average_cve_count_query(tx):
        query = (
            "MATCH (sw:SoftwareVersion)-[:ON]->(host:Host) "
            "WITH DISTINCT sw, host "
            "MATCH (cve:Vulnerability)-[:IN]->(sw) "
            "WITH host, count(DISTINCT cve) AS cve_count "
            "RETURN avg(cve_count) AS avg_cve"
        )

        result = tx.run(query)
        return result.single()

    @staticmethod
    def __get_distance_query(tx, ip1, ip2, max_distance):
        query = (
            f"MATCH path = shortestPath( (ip1:IP)-[*..{max_distance}]-(ip2:IP )) "
            "WHERE ip1.address = $ip1 and ip2.address = $ip2 "
            "RETURN length(path) as length"
        )

        result = tx.run(query, ip1=ip1, ip2=ip2)
        return result.single()

    @staticmethod
    def __get_host_event_count_subquery():
        return (
            "CALL { "
            "   WITH ip "
            "   OPTIONAL MATCH (ip)-[:SOURCE_OF]->(event:SecurityEvent) "
            "   RETURN count(event) AS event_count "
            "} "
        )

    @staticmethod
    def __get_host_cve_count_subquery():
        return (
            "CALL { "
            "    WITH host "
            "    MATCH (sw:SoftwareVersion)-[:ON]->(host) "
            "    WITH DISTINCT sw "
            "    MATCH (cve:Vulnerability)-[:IN]->(sw:SoftwareVersion) "
            "    RETURN count(DISTINCT cve) AS cve_count "
            "} "
        )

    @staticmethod
    def __get_cms_subquery():
        return (
            "CALL { "
            "   WITH host "
            "   OPTIONAL MATCH (sw:SoftwareVersion)-[r:ON]->(host) "
            "   WHERE sw.tag = 'cms_client' "
            "   RETURN sw.version AS cms "
            "   ORDER BY id(r) DESC "
            "   LIMIT 1 "
            "} "
        )

    @staticmethod
    def __get_os_subquery():
        return (
            "CALL { "
            "   WITH host "
            "   OPTIONAL MATCH (sw:SoftwareVersion)-[r:ON]->(host) "
            # Get last OS running on host.
            "   WHERE sw.tag = 'os_component' "
            "   RETURN sw.version AS os, r.start AS start, r.end AS end"
            "   ORDER BY r.end DESC "
            "   LIMIT 1 "
            "} "
        )

    @staticmethod
    def __get_antivirus_subquery():
        return (
            "CALL { "
            "   WITH host, start, end "
            "   OPTIONAL MATCH (sw:SoftwareVersion)-[r:ON]->(host) "
            "   WHERE sw.tag = 'services_component' "
            # Assure that antivirus runs on the same computer (host might be 
            # a DHCP client).
            # negation of not overlapping condition
            # => time intervals are overlapping
            "   AND NOT (end < r.start OR start > r.end) "
            "   RETURN sw.version AS antivirus "
            "   LIMIT 1 "
            "} "
        )

    @staticmethod
    def __get_contacts_subquery():
        return (
            "CALL { "
            "    WITH ip "
            "    OPTIONAL MATCH (ip)-[:PART_OF]-(:Subnet)-[:HAS]->"
            "    (c:Contact) "
            "    RETURN collect(c.name) AS contacts "
            "} "
        )

    @staticmethod
    def __get_domains_subquery():
        return (
            "CALL { "
            "   WITH ip "
            "   OPTIONAL MATCH (ip)-[:RESOLVES_TO]->(domain:DomainName) "
            # Reduce all found domain names in one list
            "   RETURN REDUCE(s = [], domain_name IN "
            "   collect(domain.domain_name) | s + domain_name) AS domains "
            "} "
        )

    @staticmethod
    def __get_host_and_ip_subquery():
        return (
            "CALL { "
            "   WITH ip_string "
            "   MATCH (host:Host)<-[:IS_A]-(:Node)-[:HAS_ASSIGNED]->(ip:IP) "
            "   WHERE ip.address = ip_string "
            "   RETURN host, ip "
            "}"
        )
