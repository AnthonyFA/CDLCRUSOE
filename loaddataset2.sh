#!/bin/bash
set -e
set -x

SERVICE_NAME="crusoe_observe"
DATASET_FILE=${DATASET_FILE:-"/datasets/cyber-czech-neo4j-Jan-30-2025-16-36-11.dump"}
NEO4J_DB="neo4j"

echo "🚀 Iniciando carga condicional del dataset en Neo4j..."

# Arrancar el servicio
docker compose up -d $SERVICE_NAME

# Esperar a que el contenedor esté disponible
echo "⏳ Esperando a que el contenedor $SERVICE_NAME esté listo..."
for i in {1..10}; do
  DB_CONTAINER=$(docker compose ps -q $SERVICE_NAME)
  if [ -n "$DB_CONTAINER" ]; then
    echo "✅ Contenedor encontrado: $DB_CONTAINER"
    break
  fi
  echo "⏳ Intento $i/10: esperando..."
  sleep 3
done

if [ -z "$DB_CONTAINER" ]; then
  echo "❌ No se pudo encontrar el contenedor $SERVICE_NAME después de 30 segundos."
  exit 1
fi

# Verificar si la base de datos ya tiene datos
EXISTE=$(docker exec "$DB_CONTAINER" bash -c "test -d /var/lib/neo4j/data/databases/$NEO4J_DB && ls -A /var/lib/neo4j/data/databases/$NEO4J_DB | wc -l" || echo 0)

if [ "$EXISTE" -eq 0 ]; then
  echo "⚙️ No se encontró base de datos, cargando dump desde $DATASET_FILE..."
  docker exec "$DB_CONTAINER" neo4j-admin load --from=$DATASET_FILE --database=$NEO4J_DB --force
else
  echo "✅ Base de datos existente, no es necesario recargar el dump."
fi

# Mostrar logs para confirmar
docker exec "$DB_CONTAINER" bash -c "cat /var/log/neo4j/neo4j.log | tail -n 20"

# Levantar el resto de servicios
docker compose up -d