set -e

# Directos (host -> contenedor)
curl -sf http://127.0.0.1:8086/firewall/capacity | jq .
curl -sf http://127.0.0.1:8080/act/threshold | jq .

# Vía dashboard (externo)
BASE=http://155.54.98.9:15580
curl -sf $BASE/act/threshold | jq .
curl -sf $BASE/firewall/capacity | jq .

# PUT correcto del threshold (clave 'security_treshold')
curl -sS -X PUT $BASE/act/threshold \
  -H 'Content-Type: application/json' \
  -d '{"security_treshold": 66}' | grep -q 'changed' && echo "PUT OK"

# Lectura posterior
curl -sf $BASE/act/threshold | jq .
echo "SMOKE OK"