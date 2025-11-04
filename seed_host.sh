#!/usr/bin/env bash
# Seed mínimo para el recommender de CRUSOE
# Uso:
#   NEO4J_PASS='tu_pass' ./seed_host.sh 10.1.4.44
# Variables opcionales:
#   NEO4J_CONT (nombre contenedor), NEO4J_USER, NEO4J_PASS
#   SUBNET, DOMAIN, CONTACT_NAME, CONTACT_EMAIL, OS_VER, AV_VER, CMS_VER

set -euo pipefail

NEO4J_CONT="${NEO4J_CONT:-cdlcrusoe-neo4j-1}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASS="${NEO4J_PASS:-neo4j}"

IP="${1:?Uso: $0 <IP> [SUBNET] [DOMAIN] [CONTACT_NAME] [CONTACT_EMAIL] [OS_VER] [AV_VER] [CMS_VER]}"
SUBNET="${2:-10.1.4.0/24}"
DOMAIN="${3:-srv-${IP//./-}.example.org}"
CONTACT_NAME="${4:-NetOps 10.1.4}"
CONTACT_EMAIL="${5:-netops@example.org}"
OS_VER="${6:-Ubuntu 22.04}"
AV_VER="${7:-ClamAV 0.103}"
CMS_VER="${8:-WordPress 6.6}"

docker exec -i "$NEO4J_CONT" cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASS" \
  --param ip="$IP" \
  --param subnet="$SUBNET" \
  --param domain="$DOMAIN" \
  --param contact_name="$CONTACT_NAME" \
  --param contact_email="$CONTACT_EMAIL" \
  --param os_ver="$OS_VER" \
  --param av_ver="$AV_VER" \
  --param cms_ver="$CMS_VER" <<'CYPHER'

/* === Esqueleto Host–IP === */
MERGE (n:Node {node_id:'node-'+$ip})
MERGE (h:Host {host_id:'host-'+$ip})
MERGE (n)-[:IS_A]->(h)
MERGE (ip:IP {address:$ip})
MERGE (n)-[:HAS_ASSIGNED]->(ip);

/* === Dominio (domain_name debe ser LISTA) === */
MERGE (d:DomainName {domain_name: [$domain]})
MERGE (ip:IP {address:$ip})-[:RESOLVES_TO]->(d);

/* === Contacto por Subred === */
MERGE (s:Subnet {cidr:$subnet})
MERGE (ip:IP {address:$ip})-[:PART_OF]->(s)
MERGE (c:Contact {name:$contact_name, email:$contact_email})
MERGE (s)-[:HAS]->(c);

/* === Software: OS (ventana activa) + AV (solape) + CMS === */
MATCH (h:Host {host_id:'host-'+$ip})
MERGE (os:SoftwareVersion {tag:'os_component',        version:$os_ver})
MERGE (av:SoftwareVersion {tag:'services_component',  version:$av_ver})
MERGE (cms:SoftwareVersion {tag:'cms_client',         version:$cms_ver})

MERGE (os)-[ros:ON]->(h)
SET   ros.start = timestamp() - 24*60*60*1000,
      ros.end   = timestamp() + 24*60*60*1000;

MERGE (av)-[rav:ON]->(h)
SET   rav.start = timestamp() - 12*60*60*1000,
      rav.end   = timestamp() + 12*60*60*1000;

MERGE (cms)-[:ON]->(h);

/* === Servicios de red (se filtran por ventana OS en el backend) === */
MATCH (h:Host {host_id:'host-'+$ip})
MERGE (svc80:NetworkService {port:80, protocol:'tcp', service:'http'})
MERGE (svc80)-[r80:ON]->(h)
SET   r80.start = timestamp() -  6*60*60*1000,
      r80.end   = timestamp() +  6*60*60*1000;

/* === Vulnerabilidades y eventos === */
MATCH (h:Host {host_id:'host-'+$ip})
MATCH (os:SoftwareVersion {tag:'os_component', version:$os_ver})-[:ON]->(h)
MERGE (v1:Vulnerability {id:'CVE-2021-44228'})
MERGE (v1)-[:IN]->(os);

MERGE (ip:IP {address:$ip})
MERGE (e:SecurityEvent {type:'IDS', description:'Exploit attempt', confirmed:true})
MERGE (ip)-[:SOURCE_OF]->(e);

/* === Salida resumen (útil para validar) === */
MATCH (h:Host)<-[:IS_A]-(:Node)-[:HAS_ASSIGNED]->(ip:IP {address:$ip})
OPTIONAL MATCH (ip)-[:RESOLVES_TO]->(d:DomainName)
OPTIONAL MATCH (ip)-[:PART_OF]-(:Subnet)-[:HAS]->(cnt:Contact)
OPTIONAL MATCH (os:SoftwareVersion {tag:'os_component'})-[ros:ON]->(h)
OPTIONAL MATCH (av:SoftwareVersion {tag:'services_component'})-[rav:ON]->(h)
OPTIONAL MATCH (cms:SoftwareVersion {tag:'cms_client'})-[rc:ON]->(h)
RETURN ip.address AS ip,
       d.domain_name AS domains,
       cnt.name AS contact,
       os.version AS os,
       av.version AS antivirus,
       cms.version AS cms
LIMIT 1;
CYPHER

echo "[OK] Seed aplicado para $IP (subnet=$SUBNET, domain=$DOMAIN)"
