#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:42917}"
IMAGE_PATH="${IMAGE_PATH:-tests/fixtures/images/imagem1.jpg}"
RUN_REAL_ML="${RUN_REAL_ML:-0}"
RUN_WARMUP="${RUN_WARMUP:-0}"
RUN_BATCH="${RUN_BATCH:-0}"
SAMPLES_DIR="${SAMPLES_DIR:-tests/fixtures/images}"
OUTPUT_DIR="${OUTPUT_DIR:-tests/output}"
JSON_DIR="$OUTPUT_DIR/json"
OVERLAY_DIR="$OUTPUT_DIR/overlays"
REPORT_DIR="$OUTPUT_DIR/hurl-reports"
SUMMARY_FILE="$OUTPUT_DIR/summary.csv"

HURL_DIR="tests/hurl"
HEALTH_HURL="$HURL_DIR/health.hurl"
ML_STATUS_HURL="$HURL_DIR/ml_status.hurl"
ML_WARMUP_HURL="$HURL_DIR/ml_warmup.hurl"
ANALYZE_HURL="$HURL_DIR/analyze_one_image.hurl"
OVERLAY_HURL="$HURL_DIR/overlay.hurl"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    echo "Install it and rerun this smoke test." >&2
    exit 127
  fi
}

run_hurl() {
  hurl --file-root . --variable "base_url=$BASE_URL" "$@"
}

check_api_reachable() {
  if ! run_hurl --no-output "$HEALTH_HURL" >/dev/null 2>&1; then
    cat >&2 <<EOF
API is not reachable at $BASE_URL.

Start it in another terminal, for example:
  uv run uvicorn prato_do_dia_api.main:app --host 0.0.0.0 --port 42917 --reload

Or override BASE_URL:
  BASE_URL=http://localhost:42917 ./tests/run-hurl-smoke.sh
EOF
    exit 1
  fi
}

csv_escape() {
  local value="${1:-}"
  value="${value//\"/\"\"}"
  printf '"%s"' "$value"
}

write_summary_row() {
  local image="$1"
  local json_file="$2"
  local duration_ms="$3"

  local status component_count overlay_url overlay_present
  status="$(jq -r '.status' "$json_file")"
  component_count="$(jq -r '.components | length' "$json_file")"
  overlay_url="$(jq -r '.image.overlay_url // ""' "$json_file")"
  overlay_present="false"
  if [[ -n "$overlay_url" ]]; then
    overlay_present="true"
  fi

  {
    csv_escape "$image"
    printf ','
    csv_escape "$status"
    printf ','
    csv_escape "$duration_ms"
    printf ','
    csv_escape "$component_count"
    printf ','
    csv_escape "$overlay_present"
    printf '\n'
  } >> "$SUMMARY_FILE"
}

validate_analyze_contract() {
  local json_file="$1"
  local status component_count overlay_url

  status="$(jq -r '.status' "$json_file")"
  component_count="$(jq -r '.components | length' "$json_file")"
  overlay_url="$(jq -r '.image.overlay_url // ""' "$json_file")"

  if [[ "$status" != "success" && "$status" != "empty" ]]; then
    echo "Unexpected analyze status in $json_file: $status" >&2
    return 1
  fi

  if [[ "$status" == "success" && "$component_count" -lt 1 ]]; then
    echo "Successful analyze response has no components: $json_file" >&2
    return 1
  fi

  if [[ "$status" == "empty" && -n "$overlay_url" ]]; then
    echo "Empty analyze response should not include an overlay URL: $json_file" >&2
    return 1
  fi
}

run_analyze_for_image() {
  local image_path="$1"
  local name stem json_file image_report_dir report_file overlay_url overlay_file duration_ms

  if [[ ! -f "$image_path" ]]; then
    echo "Image not found: $image_path" >&2
    return 1
  fi

  name="$(basename "$image_path")"
  stem="${name%.*}"
  json_file="$JSON_DIR/${stem}.json"
  image_report_dir="$REPORT_DIR/$stem"
  report_file="$image_report_dir/report.json"
  overlay_file="$OVERLAY_DIR/${stem}_overlay.jpg"

  echo "==> Analyze $image_path"
  run_hurl \
    --variable "image_path=$image_path" \
    --output "$json_file" \
    --report-json "$image_report_dir" \
    "$ANALYZE_HURL"

  validate_analyze_contract "$json_file"

  duration_ms="$(jq -r '.[0].entries[-1].time // ""' "$report_file" 2>/dev/null || true)"
  overlay_url="$(jq -r '.image.overlay_url // ""' "$json_file")"

  if [[ -n "$overlay_url" ]]; then
    echo "==> Fetch overlay $overlay_url"
    run_hurl \
      --variable "overlay_url=$overlay_url" \
      --output "$overlay_file" \
      "$OVERLAY_HURL"
  fi

  write_summary_row "$name" "$json_file" "$duration_ms"
}

require_command hurl
require_command jq

mkdir -p "$JSON_DIR" "$OVERLAY_DIR" "$REPORT_DIR"
echo "image,status,duration_ms,component_count,overlay_present" > "$SUMMARY_FILE"

echo "==> Checking API at $BASE_URL"
check_api_reachable

echo "==> Health"
run_hurl --no-output "$HEALTH_HURL"

echo "==> ML status"
run_hurl --no-output "$ML_STATUS_HURL"

if [[ "$RUN_WARMUP" == "1" ]]; then
  echo "==> ML warmup"
  run_hurl --no-output "$ML_WARMUP_HURL"
fi

if [[ "$RUN_REAL_ML" != "1" ]]; then
  echo "Skipping real-ML analyze checks because RUN_REAL_ML=$RUN_REAL_ML."
  echo "Summary saved to $SUMMARY_FILE"
  exit 0
fi

if [[ "$RUN_BATCH" == "1" ]]; then
  shopt -s nullglob
  images=("$SAMPLES_DIR"/*.jpg "$SAMPLES_DIR"/*.jpeg "$SAMPLES_DIR"/*.png)
  shopt -u nullglob
  if [[ "${#images[@]}" -eq 0 ]]; then
    echo "No images found in $SAMPLES_DIR" >&2
    exit 1
  fi
  for image in "${images[@]}"; do
    run_analyze_for_image "$image"
  done
else
  run_analyze_for_image "$IMAGE_PATH"
fi

echo "Summary saved to $SUMMARY_FILE"
