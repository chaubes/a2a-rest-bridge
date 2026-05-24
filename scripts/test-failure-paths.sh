#!/usr/bin/env bash
#
# Failure-path integration tests.
#
# Exercises the deterministic guardrails at the REST layer (fast) and one
# agent-level failure that flows all the way back to a `failed` confirmation.
#
# Requires the stack to be running (./scripts/run-all.sh).
set -euo pipefail

INVENTORY_SVC="${INVENTORY_SERVICE_URL:-http://localhost:8081}"
PAYMENT_SVC="${PAYMENT_SERVICE_URL:-http://localhost:8082}"
ORDER_AGENT="${ORDER_AGENT_URL:-http://localhost:10010}"

pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; exit 1; }

code() {  # method url json -> http status
  if [ "$1" = "GET" ]; then curl -s -o /dev/null -w '%{http_code}' "$2"
  else curl -s -o /dev/null -w '%{http_code}' -X "$1" "$2" -H 'Content-Type: application/json' -d "$3"; fi
}

echo "Failure paths — REST guardrails (deterministic):"

# 1. Invalid currency -> Bean Validation rejects with 422.
c="$(code POST "$PAYMENT_SVC/api/v1/payments/charge" '{"customerId":"C-001","amount":10,"currency":"XYZ","paymentMethodToken":"tok","correlationId":"fail-1"}')"
[ "$c" = "422" ] && pass "invalid currency rejected with 422" || fail "expected 422 for bad currency, got $c"

# 2. Deterministic decline (test customer) -> 402.
c="$(code POST "$PAYMENT_SVC/api/v1/payments/charge" '{"customerId":"DECLINE-TEST","amount":10,"currency":"AUD","paymentMethodToken":"tok","correlationId":"fail-2"}')"
[ "$c" = "402" ] && pass "decline-test customer declined with 402" || fail "expected 402 for decline test, got $c"

# 3. Amount over the single-transaction limit -> 402.
c="$(code POST "$PAYMENT_SVC/api/v1/payments/charge" '{"customerId":"C-001","amount":20000,"currency":"AUD","paymentMethodToken":"tok","correlationId":"fail-3"}')"
[ "$c" = "402" ] && pass "over-limit charge declined with 402" || fail "expected 402 for over-limit amount, got $c"

# 4. Reserve more stock than exists (WR-001 has 25) -> 409.
c="$(code POST "$INVENTORY_SVC/api/v1/stock/reserve" '{"productId":"WR-001","quantity":9999,"correlationId":"fail-4"}')"
[ "$c" = "409" ] && pass "over-reservation rejected with 409" || fail "expected 409 for insufficient stock, got $c"

echo
echo "Failure path — agent level (insufficient stock flows to a failed order):"
echo "  (calls the LLM across agents — can take a little while)"

req='{"jsonrpc":"2.0","id":"fail-order","method":"message/send","params":{"message":{"role":"user","messageId":"fail-order-msg","parts":[{"kind":"text","text":"I am customer C-002. I want to order 500 Widget Racks to my address. Charge card tok-test-visa."}]}}}'
resp="$(curl -s --max-time 300 -X POST "$ORDER_AGENT/" -H 'Content-Type: application/json' -d "$req")"
status="$(python3 - "$resp" <<'PY'
import json, sys
result = json.loads(sys.argv[1]).get("result", {})
for art in result.get("artifacts", []):
    for part in art.get("parts", []):
        try:
            print(json.loads(part["text"]).get("status","")); sys.exit(0)
        except Exception:
            pass
# fall back to task status state
print(result.get("status", {}).get("state", ""))
PY
)"
case "$status" in
  failed|pending_review) pass "oversized order did not confirm (status=$status)";;
  *) fail "expected a non-confirmed status for an impossible order, got '$status'";;
esac

echo
echo "Failure paths passed."
