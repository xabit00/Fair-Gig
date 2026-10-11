#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8006}"
URL="http://localhost:${PORT}/health"

echo "Checking certificate-service health at ${URL}..."
response=$(curl -sf "${URL}")
echo "Response: ${response}"
echo "certificate-service smoke test passed!"
