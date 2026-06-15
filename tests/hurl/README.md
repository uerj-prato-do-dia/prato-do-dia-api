# Hurl smoke tests

These files exercise the running FastAPI service over real HTTP. They are not a
replacement for pytest unit, service, database, schema, or mocked-ML tests.

Variables:

- `base_url`: API base URL. Defaults to `http://localhost:42917` in
  `tests/run-hurl-smoke.sh`.
- `image_path`: local image used by `analyze_one_image.hurl`.
- `overlay_url`: URL captured from a successful analyze response and passed to
  `overlay.hurl`.
- `OUTPUT_DIR`: shell variable used by `tests/run-hurl-smoke.sh` for generated
  JSON, overlay images, Hurl reports, and `summary.csv`.

Fast checks:

- `health.hurl`
- `ml_status.hurl`

Real-ML checks:

- `ml_warmup.hurl`
- `analyze_one_image.hurl`
- `overlay.hurl`

Use `tests/run-hurl-smoke.sh` instead of invoking every file by hand; it checks
tooling, creates output directories, saves generated JSON/overlay files under
`tests/output/`, and writes a local summary CSV.

The default runner mode is lightweight: it runs health and ML status only.
Use `RUN_WARMUP=1` to explicitly initialize the model stack, and
`RUN_REAL_ML=1` to run real image analysis and overlay checks.
