#!/bin/bash
# Imprimir comandos
set -x
# Parar en caso de error
set -e 

docker compose up -d crusoe_observe
docker exec -it cdlcrusoe-crusoe_observe-1 /bin/bash -c "cat /var/log/neo4j/neo4j.log"
bash loaddataset.sh 
docker compose logs -f 
docker compose up -d
