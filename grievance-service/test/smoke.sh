#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8004}"
URL="http://localhost:${PORT}/health"

echo "Checking grievance-service health at ${URL}..."
response=$(curl -sf "${URL}")
echo "Response: ${response}"
echo "grievance-service smoke test passed!"
