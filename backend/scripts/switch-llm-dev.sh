#!/usr/bin/env bash
#
# Switch the receipt-parsing vision LLM endpoint/model. LOCAL / DEV ONLY.
# Runnable from any cwd (anchors to repo root).
#
# Dev points the OpenAI-compatible parser at a self-hosted vision endpoint
# (noop key). Production instead uses an AUTHENTICATED cloud vision API,
# configured through the same RECEIPT_LLM_* env on the prod host — not this
# script. The parser code is identical; only the env (base_url/api_key/model)
# differs between environments.
#
#   bash backend/scripts/switch-llm-dev.sh <base_url> [model]
#
# Examples:
#   bash backend/scripts/switch-llm-dev.sh http://<llm-host>:<port>/v1
#       -> probes the endpoint, auto-detects the served model, wires it up
#   bash backend/scripts/switch-llm-dev.sh http://<llm-host>:<port>/v1 gemma-4-26B-A4B
#       -> uses the given model explicitly
#
# It edits backend/.env (gitignored) then force-recreates the receipt-worker so
# the new env is actually loaded (a plain `docker compose restart` does NOT
# reload env_file). Only receipt-worker calls the LLM, so only it is recreated.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."
ENV_FILE="backend/.env"

BASE_URL="${1:?usage: switch-llm.sh <base_url> [model]   e.g. http://<llm-host>:<port>/v1}"
MODEL="${2:-}"

echo "Probing ${BASE_URL}/models ..."
MODELS_JSON="$(curl -s --max-time 8 "${BASE_URL}/models" || true)"
if [ -z "$MODELS_JSON" ]; then
  echo "✗ endpoint not reachable: ${BASE_URL}  (is the LLM service up and listening?)"
  exit 1
fi

# Auto-detect the model (first one served) when not given explicitly.
if [ -z "$MODEL" ]; then
  MODEL="$(printf '%s' "$MODELS_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ms = d.get('models', d.get('data', []))
print((ms[0].get('name') or ms[0].get('id') or '') if ms else '')
")"
  [ -z "$MODEL" ] && { echo "✗ could not auto-detect a model — pass one explicitly"; exit 1; }
  echo "Auto-detected model: ${MODEL}"
fi

# Warn (don't fail) if the requested model isn't in the endpoint's list.
printf '%s' "$MODELS_JSON" | grep -q "$MODEL" \
  || echo "⚠  '${MODEL}' not found in the endpoint's model list — proceeding anyway"

# Rewrite the two lines in backend/.env (# delimiter so URL slashes are fine).
sed -i -E "s#^RECEIPT_LLM_BASE_URL=.*#RECEIPT_LLM_BASE_URL=${BASE_URL}#" "$ENV_FILE"
sed -i -E "s#^RECEIPT_LLM_MODEL=.*#RECEIPT_LLM_MODEL=${MODEL}#" "$ENV_FILE"
echo "Updated ${ENV_FILE}:  BASE_URL=${BASE_URL}  MODEL=${MODEL}"

echo "Recreating receipt-worker to load the new env ..."
docker compose up -d --force-recreate receipt-worker

echo "✓ done. Effective env in receipt-worker:"
docker compose exec -T receipt-worker sh -c 'env | grep "^RECEIPT_LLM_" | grep -v API_KEY'
