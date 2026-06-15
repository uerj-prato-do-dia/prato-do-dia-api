#!/usr/bin/env bash
set -euo pipefail

echo "tests/run-api-tests.sh is deprecated; use tests/run-hurl-smoke.sh." >&2
exec "$(dirname "$0")/run-hurl-smoke.sh" "$@"
