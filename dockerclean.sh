#!/bin/bash
# Imprimir comandos
set -x
# Parar en caso de error
set -e 


docker container prune -f
docker volume prune -af