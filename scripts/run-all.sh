#!/usr/bin/env bash
#
# Build and start the full AgentCart stack, then wait for it to become healthy.
#
# Usage:
#   ./scripts/run-all.sh          # build (if needed) and start everything
#   ./scripts/run-all.sh --build  # force a rebuild of all images
#   ./scripts/run-all.sh down     # stop and remove the stack
#
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "down" ]]; then
  docker compose down
  exit 0
fi

if [[ ! -f .env ]]; then
  echo "No .env found. Copy .env.example to .env and add your OPENAI_API_KEY:"
  echo "    cp .env.example .env"
  echo "(or set LLM_PROVIDER=ollama in .env to run fully local with no key)."
  exit 1
fi

BUILD_FLAG=""
if [[ "${1:-}" == "--build" ]]; then
  BUILD_FLAG="--build"
fi

echo "Starting the AgentCart stack (this builds Java, Python and web images on first run)..."
docker compose up -d ${BUILD_FLAG}

echo "Waiting for the Order Agent to report healthy..."
for _ in $(seq 1 60); do
  status=$(docker compose ps --format '{{.Service}} {{.Health}}' 2>/dev/null | awk '$1=="order-agent"{print $2}')
  if [[ "${status}" == "healthy" ]]; then
    break
  fi
  sleep 3
done

echo
echo "AgentCart is up:"
echo "  Chat UI            http://localhost:3000"
echo "  Order Agent card   http://localhost:10010/.well-known/agent.json"
echo "  Swagger (per svc)  http://localhost:8080-8084/swagger-ui.html"
echo
echo "Try the happy path:   ./scripts/test-happy-path.sh"
echo "Try the failures:     ./scripts/test-failure-paths.sh"
echo "Stop everything:      ./scripts/run-all.sh down"
