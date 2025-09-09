#!/bin/bash
# Imprimir comandos
set -x
# Parar en caso de error
set -e 

docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "neo4j stop"
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "neo4j-admin load --from=/datasets/cyber-czech-neo4j-May-6-2024-16-41-30.dump --database=neo4j --force"
#docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "neo4j-admin load --from=/datasets/cyber-czech-neo4j-Jan-30-2025-16-36-11.dump --database=neo4j --force"
#docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "neo4j-admin load --from=/datasets/robot-use-case-neo4j-May-28-2024-16-02-01.dump --database=neo4j --force"
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "chown neo4j -R /var/lib/neo4j/data/databases/neo4j"
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "chgrp neo4j -R /var/lib/neo4j/data/databases/neo4j"

sleep 5
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "cat /var/log/neo4j/neo4j.log"
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "neo4j console"