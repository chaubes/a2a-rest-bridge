#!/usr/bin/env bash
#
# Happy-path integration test.
#
# Sends a natural-language order to the Order Agent and verifies that it drives
# the full chain (intent -> inventory -> payment -> shipping -> order -> notify)
# to a confirmed OrderConfirmation, then checks the resulting state in the REST
# services directly.
#
# Requires the stack to be running (./scripts/run-all.sh) and, for the agents,
# a working LLM (OPENAI_API_KEY, or LLM_PROVIDER=ollama).
set -euo pipefail

ORDER_AGENT="${ORDER_AGENT_URL:-http://localhost:10010}"
PAYMENT_SVC="${PAYMENT_SERVICE_URL:-http://localhost:8082}"
ORDER_SVC="${ORDER_SERVICE_URL:-http://localhost:8080}"

pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; exit 1; }

echo "Happy path: placing an order via the Order Agent (this calls the LLM and"
echo "delegates across all five agents, so it can take a little while)..."

req='{"jsonrpc":"2.0","id":"happy","method":"message/send","params":{"message":{"role":"user","messageId":"happy-msg","parts":[{"kind":"text","text":"I am customer C-001. I would like to order 2 Blue Widgets delivered to my default address. Please charge my card token tok-test-visa."}]}}}'

resp="$(curl -s --max-time 300 -X POST "$ORDER_AGENT/" -H 'Content-Type: application/json' -d "$req")"

# Extract the OrderConfirmation JSON from the task artifact.
conf="$(python3 - "$resp" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
result = data.get("result", {})
for art in result.get("artifacts", []):
    for part in art.get("parts", []):
        if part.get("kind") == "text" or "text" in part:
            try:
                json.loads(part["text"])
                print(part["text"]); sys.exit(0)
            except Exception:
                pass
print("{}")
PY
)"

get() { python3 -c "import json,sys; print(json.loads(sys.argv[1]).get(sys.argv[2]) or '')" "$conf" "$1"; }

status="$(get status)"
txn="$(get transaction_id)"
trk="$(get tracking_id)"
order_id="$(get order_id)"
total="$(get total_amount)"

echo "Confirmation: status=$status order=$order_id txn=$txn tracking=$trk total=$total"

[ "$status" = "confirmed" ] && pass "order confirmed" || fail "expected status=confirmed, got '$status'"
[ -n "$txn" ] && pass "payment transaction id present ($txn)" || fail "no transaction id"
[ -n "$trk" ] && pass "shipping tracking id present ($trk)" || fail "no tracking id"
[ "$total" = "29.98" ] && pass "total amount is the catalog total (29.98)" || fail "unexpected total '$total'"

# Verify the charge is actually recorded in the payment service.
txn_status="$(curl -s "$PAYMENT_SVC/api/v1/payments/transactions/$txn" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")"
[ "$txn_status" = "SUCCESS" ] && pass "payment service confirms transaction SUCCESS" || fail "payment service did not confirm the transaction (status='$txn_status')"

# Verify the order is persisted in the order service.
order_http="$(curl -s -o /dev/null -w '%{http_code}' "$ORDER_SVC/api/v1/orders/$order_id")"
[ "$order_http" = "200" ] && pass "order service has the persisted order" || fail "order $order_id not found in order service (HTTP $order_http)"

echo
echo "Happy path passed."
