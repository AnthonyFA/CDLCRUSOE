#!/usr/bin/env bash
set -euo pipefail

BASE=http://localhost
echo "== SMOKE $(date) =="

pass() { echo "OK   - $1"; }
fail() { echo "FAIL - $1"; exit 1; }

# 1) SPA (debe devolver HTML)
CT=$(curl -sI $BASE/ | awk -F': ' 'tolower($1)=="content-type"{print tolower($2)}' | tr -d '\r')
[[ "$CT" == text/html* || -z "$CT" ]] && pass "SPA / responde (Content-Type: $CT)" || fail "SPA / no es HTML"

# 2) REST /rest/missions (JSON array)
RESP=$(curl -s $BASE/rest/missions || true)
TYPE=$(printf '%s' "$RESP" | jq -r 'type' 2>/dev/null || echo "not-json")
[[ "$TYPE" == "array" ]] && pass "REST /rest/missions es JSON array" || { echo "$RESP" | head -c 200; echo; fail "REST no devolvió JSON array"; }

# 3) ACT /act/treshold (JSON con security_treshold)
RESP=$(curl -s $BASE/act/treshold || true)
VAL=$(printf '%s' "$RESP" | jq -r '.security_treshold' 2>/dev/null || echo "")
[[ "$VAL" =~ ^[0-9]+$ ]] && pass "ACT /act/treshold OK (security_treshold=$VAL)" || { echo "$RESP"; fail "ACT no devolvió JSON válido"; }

# 4) Firewall PAO /firewall/capacity (JSON con claves de capacidad)
RESP=$(curl -s $BASE/firewall/capacity || true)
MC=$(printf '%s' "$RESP" | jq -r 'keys|join(",")' 2>/dev/null || echo "")
grep -q 'maxCapacity' <<<"$MC" && grep -q 'usedCapacity' <<<"$MC" && grep -q 'freeCapacity' <<<"$MC" \
  && pass "PAO /firewall/capacity OK ($MC)" || { echo "$RESP"; fail "PAO no devolvió JSON esperado"; }

# 5) GraphQL __typename
RESP=$(curl -s -X POST $BASE/graphql -H 'Content-Type: application/json' \
  -d '{"query":"{ __typename }"}' || true)
TYP=$(printf '%s' "$RESP" | jq -r '.data.__typename' 2>/dev/null || echo "")
[[ -n "$TYP" && "$TYP" != "null" ]] && pass "GraphQL OK (__typename=$TYP)" || { echo "$RESP"; fail "GraphQL sin data.__typename"; }

echo "== FIN SMOKE =="
