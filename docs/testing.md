# Testing

Use pytest for code-level behavior and Hurl for real HTTP behavior. Hurl should
prove that the running FastAPI API honors the public contract; it should not
replace Python tests that need mocks, isolated databases, failure injection, or
internal assertions.

## Pytest

Run:

```bash
uv run pytest
```

Keep pytest coverage for:

- unit tests;
- service-layer tests;
- Pydantic/schema tests;
- database and persistence tests;
- mocked ML behavior;
- edge cases that need monkeypatching or dependency overrides;
- upload validation and standardized error responses.

The existing `tests/test_health.py` and `tests/test_meals.py` should remain.
They are cheap, run in-process, isolate the database, and mock ML behavior.
The mocked happy path in `tests/test_meals.py` overlaps with Hurl at the HTTP
contract level, but it still verifies internal mapping and service behavior
without requiring ONNX models.

## Hurl

Run the local smoke suite against a running API:

```bash
uv run uvicorn prato_do_dia_api.main:app --host 0.0.0.0 --port 42917 --reload
./tests/run-hurl-smoke.sh
```

Useful overrides:

```bash
BASE_URL=http://localhost:42917 ./tests/run-hurl-smoke.sh
IMAGE_PATH=tests/fixtures/images/imagem1.jpg ./tests/run-hurl-smoke.sh
OUTPUT_DIR=tests/output ./tests/run-hurl-smoke.sh
RUN_WARMUP=1 ./tests/run-hurl-smoke.sh
RUN_BATCH=1 ./tests/run-hurl-smoke.sh
RUN_REAL_ML=1 ./tests/run-hurl-smoke.sh
```

Fast Hurl checks:

- `GET /v1/health`;
- `GET /v1/ml/status`.

`GET /v1/ml/status` is intentionally lightweight. It inspects ML configuration,
model files, and the model manifest without loading ONNX Runtime sessions or
running inference.

Real-ML Hurl checks:

- optional `POST /v1/ml/warmup` with `RUN_WARMUP=1`;
- `POST /v1/meals/analyze` with a real image file;
- fetch `image.overlay_url` when a successful analysis produced one.

`POST /v1/ml/warmup` is intentionally heavy and initializes the predictor/model
stack. The real-ML checks require the API process to have access to the ONNX models.
Do not put those checks in normal CI unless the CI environment explicitly
provisions the models and accepts the runtime cost. For CI smoke coverage, run
the default smoke script, which keeps `RUN_REAL_ML=0` and `RUN_WARMUP=0`.

Generated Hurl artifacts are local only:

- `tests/output/json/*.json`;
- `tests/output/overlays/*`;
- `tests/output/hurl-reports/*`;
- `tests/output/summary.csv`.

Those files are ignored by Git. Keep `tests/output/.gitkeep` so the directory
exists, but do not commit generated responses or overlays.

## Just

The project root has an optional `justfile` with shortcuts such as:

```bash
just api-check
just api-dev
just api-smoke
just api-smoke-real
just mobile-check
just smoke-mobile-usb
just check-all
```

`just` is only a command runner. The underlying `uv`, `flutter`, and shell
commands documented above still work directly if `just` is not installed.
