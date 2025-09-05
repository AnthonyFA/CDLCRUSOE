#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-http://localhost}"
TMP_DIR="$(mktemp -d)"
PASS=0
FAIL=0

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Falta '$1' en el PATH. Instálalo y reintenta."
    exit 1
  fi
}
need curl
need jq

hr() { printf '\n%s\n' "-------------------------------------------"; }

req() {
  # $1 = method, $2 = url, $3 = data(optional), $4 = extra curl opts(optional)
  local method="$1"; shift
  local url="$1"; shift
  local data="${1:-}"; shift || true
  local extra="${1:-}"; shift || true

  local body="$TMP_DIR/body.$$"
  local head="$TMP_DIR/head.$$"

  if [[ -n "$data" ]]; then
    code=$(curl -sS -X "$method" "$url" \
      -H 'Content-Type: application/json' \
      --max-time 15 \
      -D "$head" -o "$body" -w '%{http_code}' \
      --data "$data" $extra)
  else
    code=$(curl -sS -X "$method" "$url" \
      --max-time 15 \
      -D "$head" -o "$body" -w '%{http_code}' \
      $extra)
  fi

  echo "$head" > "$TMP_DIR/last_headers"
  echo "$body" > "$TMP_DIR/last_body_path"
  cat "$body" > "$TMP_DIR/last_body"
  echo -n "$code"
}

expect_code() { # $1 = actual, $2 = expected
  if [[ "$1" == "$2" ]]; then
    echo "✅ HTTP $2"
    ((PASS++)) || true
  else
    echo "❌ Esperaba HTTP $2, obtuve $1"
    ((FAIL++)) || true
  fi
}

expect_contains() { # $1 = file, $2 = pattern
  if grep -qi -- "$2" "$1"; then
    echo "✅ Contiene: $2"
    ((PASS++)) || true
  else
    echo "❌ No contiene: $2"
    ((FAIL++)) || true
  fi
}

expect_jq() { # $1 = jq expr devuelve true (exit 0)
  if jq -e "$1" "$TMP_DIR/last_body" >/dev/null 2>&1; then
    echo "✅ JSON cumple: $1"
    ((PASS++)) || true
  else
    echo "❌ JSON no cumple: $1"
    echo "Body:"; cat "$TMP_DIR/last_body" | sed 's/^/  /'
    ((FAIL++)) || true
  fi
}

expect_header_contains() { # $1 = header (regex), $2 = value (regex)
  if grep -Eiq "^$1:.*$2" "$TMP_DIR/last_headers"; then
    echo "✅ Header $1 incluye $2"
    ((PASS++)) || true
  else
    echo "❌ Header $1 no incluye $2"
    echo "Headers:"; cat "$TMP_DIR/last_headers" | sed 's/^/  /'
    ((FAIL++)) || true
  fi
}

hr; echo "🔎 Probando SPA ($BASE/)"
code=$(req GET "$BASE/"); expect_code "$code" 200
expect_header_contains "Content-Type" "text/html"
expect_contains "$TMP_DIR/last_body" "<app-root" || true
expect_contains "$TMP_DIR/last_body" "<base" || true

hr; echo "🔎 /rest/missions (neo4j-rest vía Nginx)"
code=$(req GET "$BASE/rest/missions"); expect_code "$code" 200
expect_header_contains "Content-Type" "application/json"
expect_jq 'type== "array" and length>0'
expect_jq '.[0] | has("name")'

hr; echo "🔎 /rest/ vacío redirige a /rest/missions"
code=$(req GET "$BASE/rest/" "" "-L -s -o /dev/null -w '%{http_code}'")
expect_code "$code" 200  # tras seguir -L debe terminar en 200
# comprobamos que sin -L devuelve 302 y Location correcto
code=$(req GET "$BASE/rest/"); expect_code "$code" 302
expect_header_contains "Location" "/rest/missions"

hr; echo "🔎 /graphql (POST __typename)"
code=$(req POST "$BASE/graphql" '{"query":"{ __typename }"}')
expect_code "$code" 200
expect_jq '.data.__typename == "Query"'

hr; echo "🔎 Preflight OPTIONS /graphql (CORS)"
code=$(req OPTIONS "$BASE/graphql"); expect_code "$code" 204
expect_header_contains "Access-Control-Allow-Methods" "POST|GET|OPTIONS"
expect_header_contains "Access-Control-Allow-Headers" "Content-Type"

hr; echo "🔎 /act/treshold (ACT overseer)"
code=$(req GET "$BASE/act/treshold"); expect_code "$code" 200
expect_jq 'has("security_treshold")'

hr; echo "🔎 /firewall/capacity (PAO firewall)"
code=$(req GET "$BASE/firewall/capacity"); expect_code "$code" 200
expect_jq 'has("maxCapacity") and has("usedCapacity") and has("freeCapacity")'
# coherencia: used + free == max
if jq -e '(.usedCapacity + .freeCapacity) == .maxCapacity' "$TMP_DIR/last_body" >/dev/null; then
  echo "✅ used + free == max"
  ((PASS++)) || true
else
  echo "❌ used + free != max"; ((FAIL++)) || true
fi

hr; echo "🔎 /flower/ (opcional: HTML de Flower)"
code=$(req GET "$BASE/flower/" "" "--max-time 10") || true
if [[ "$code" == "200" ]]; then
  echo "✅ Flower responde 200"
  ((PASS++)) || true
else
  echo "ℹ️ Flower no respondió 200 (código $code). Si no usas Flower en UI, ignora esto."
fi

hr
echo "✅ PASSES: $PASS   ❌ FAILS: $FAIL"
[[ $FAIL -eq 0 ]] && echo "🎉 Smoke OK" || { echo "🚑 Revisa los FAILS arriba."; exit 1; }
