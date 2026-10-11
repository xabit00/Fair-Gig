#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8005}"
URL="http://localhost:${PORT}/health"

echo "Checking analytics-service health at ${URL}..."
response=$(curl -sf "${URL}")
echo "Response: ${response}"
echo "analytics-service smoke test passed!"
