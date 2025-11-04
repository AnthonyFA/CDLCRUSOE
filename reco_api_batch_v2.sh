#!/usr/bin/env bash
set -euo pipefail

# 1) Detectar endpoint del recomendador (reverse-proxy vs puerto directo)
RECO_URL="${RECO_URL:-http://127.0.0.1}"
if ! curl -fsS "$RECO_URL/recommender/configuration" >/dev/null 2>&1; then
  RECO_URL="http://localhost:16005"
  curl -fsS "$RECO_URL/recommender/configuration" >/dev/null
fi
echo "Usando RECO_URL=$RECO_URL"

# 2) Semillas: fichero pasado como $1 (una IP por línea) o IP por defecto
SEED_FILE="${1:-}"
TMP_SEEDS="$(mktemp)"
if [ -n "$SEED_FILE" ]; then
  awk 'NF{print $1}' "$SEED_FILE" > "$TMP_SEEDS"
else
  echo "10.1.4.44" > "$TMP_SEEDS"
fi
echo "Semillas:"; cat "$TMP_SEEDS"

# 3) Salida
TS="$(date +%Y%m%d_%H%M%S)"
OUT="reco_api_$TS"
mkdir -p "$OUT/json"

# 4) Lista de IPs a testear: semillas + sus recomendados (top 10)
ALL_IPS="$(mktemp)"
cp "$TMP_SEEDS" "$ALL_IPS"
while read -r ip; do
  [ -n "$ip" ] || continue
  curl -fsS "$RECO_URL/recommender/recommended-hosts?ip=${ip}&limit=10" \
    | jq -r '.[].ip' >> "$ALL_IPS" || true
done < "$TMP_SEEDS"

sort -u "$ALL_IPS" | head -n 50 > "$OUT/ips.txt"
COUNT=$(wc -l < "$OUT/ips.txt")
echo "Total IPs a testear: $COUNT"

# 5) Cabecera CSV
echo "IP,reco_count,top1_ip,top1_risk,top1_distance,top1_paths,status_attacked,status_reco" > "$OUT/summary.csv"

# 6) Pruebas por IP
while read -r ip; do
  [ -n "$ip" ] || continue
  echo "== $ip =="

  status_attacked=$(curl -sS -w "%{http_code}" -o "$OUT/json/${ip}.attacked.json" \
    "$RECO_URL/recommender/attacked-host?ip=${ip}")

  status_reco=$(curl -sS -w "%{http_code}" -o "$OUT/json/${ip}.reco.json" \
    "$RECO_URL/recommender/recommended-hosts?ip=${ip}&limit=10")

  reco_count=$(jq 'length' "$OUT/json/${ip}.reco.json" 2>/dev/null || echo 0)
  top1_ip=$(jq -r '.[0].ip // empty' "$OUT/json/${ip}.reco.json" 2>/dev/null || true)
  # risk[0] si existe; si no, score; si no, vacío
  top1_risk=$(jq -r '
    if (.[0]|type=="object") then
      if (.[0]|has("risk") and (.[0].risk|type=="array") and (.[0].risk|length)>0)
        then .[0].risk[0]
      elif (.[0]|has("score"))
        then .[0].score
      else empty end
    else empty end
  ' "$OUT/json/${ip}.reco.json" 2>/dev/null || true)
  top1_distance=$(jq -r '.[0].distance // empty' "$OUT/json/${ip}.reco.json" 2>/dev/null || true)
  top1_paths=$(jq -r '.[0].path_types | join(";") // empty' "$OUT/json/${ip}.reco.json" 2>/dev/null || true)

  echo "$ip,$reco_count,${top1_ip:-},${top1_risk:-},${top1_distance:-},${top1_paths:-},$status_attacked,$status_reco" >> "$OUT/summary.csv"
done < "$OUT/ips.txt"

echo "✅ Hecho: $OUT/summary.csv"
head -n 5 "$OUT/summary.csv" || true
