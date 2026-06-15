from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from prato_do_dia_api.api.routes import v1
from prato_do_dia_api.db.session import Base, get_db
from prato_do_dia_api.main import app
from prato_do_dia_api.services import meal_analysis_service as service_module


def _jpeg_bytes(size: tuple[int, int] = (32, 32)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color=(240, 160, 80)).save(output, format="JPEG")
    return output.getvalue()


def _png_bytes(size: tuple[int, int] = (32, 32)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color=(120, 180, 220)).save(output, format="PNG")
    return output.getvalue()


class FakePredictor:
    def __init__(self, *, instances: list[object] | None = None, fail: Exception | None = None) -> None:
        self.instances = instances or []
        self.fail = fail

    def predict_bytes(self, _image_bytes: bytes) -> object:
        if self.fail is not None:
            raise self.fail
        return SimpleNamespace(
            image_width=32,
            image_height=32,
            instances=self.instances,
            warnings=[],
            artifacts={},
            model_info=SimpleNamespace(pipeline="yolo11_sam2_onnx", version="baseline-2026-06-15"),
        )


class FakeFoodPredictor:
    predictor = FakePredictor()

    @classmethod
    def from_models_dir(cls, _models_dir: Path) -> FakePredictor:
        return cls.predictor


@pytest.fixture(autouse=True)
def isolated_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db: Session = session_local()
        try:
            yield db
        finally:
            db.close()

    uploads = tmp_path / "uploads"
    overlays = tmp_path / "overlays"
    uploads.mkdir()
    overlays.mkdir()
    monkeypatch.setattr(service_module, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(service_module, "OVERLAYS_DIR", overlays)
    monkeypatch.setitem(service_module.ASSET_DIRS, "uploads", uploads)
    monkeypatch.setitem(service_module.ASSET_DIRS, "overlays", overlays)
    monkeypatch.setitem(v1.ASSET_DIRS, "uploads", uploads)
    monkeypatch.setitem(v1.ASSET_DIRS, "overlays", overlays)
    monkeypatch.setattr(service_module, "FoodPredictor", FakeFoodPredictor)
    FakeFoodPredictor.predictor = FakePredictor()
    monkeypatch.setattr(service_module, "_PREDICTOR", None)
    app.dependency_overrides[get_db] = override_get_db
    yield tmp_path
    app.dependency_overrides.clear()
    monkeypatch.setattr(service_module, "_PREDICTOR", None)


async def _post_file(content: bytes, content_type: str = "image/jpeg") -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post("/v1/meals/analyze", files={"file": ("meal.jpg", content, content_type)})


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


async def _post(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path)


def _write_model_manifest(models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / "model_manifest.json").write_text(
        """
{
  "schema_version": "1.0",
  "models": [
    {"filename": "detector.onnx", "role": "detector", "size_bytes": 8, "sha256": "expected-detector"},
    {"filename": "encoder.onnx", "role": "sam_encoder", "size_bytes": 7, "sha256": "expected-encoder"},
    {"filename": "decoder.onnx", "role": "sam_decoder", "size_bytes": 7, "sha256": "expected-decoder"}
  ]
}
""".strip(),
        encoding="utf-8",
    )


def _use_models_dir(monkeypatch: pytest.MonkeyPatch, models_dir: Path) -> None:
    monkeypatch.setattr(
        service_module,
        "get_settings",
        lambda: service_module.Settings(ml_models_dir=str(models_dir)),
    )


def test_v1_health() -> None:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/v1/health")

    response = asyncio.run(request())

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ml_status_with_models_present_does_not_initialize_predictor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    models_dir = tmp_path / "models"
    _write_model_manifest(models_dir)
    (models_dir / "detector.onnx").write_bytes(b"detector")
    (models_dir / "encoder.onnx").write_bytes(b"encoder")
    (models_dir / "decoder.onnx").write_bytes(b"decoder")
    _use_models_dir(monkeypatch, models_dir)

    class PredictorShouldNotLoad:
        @classmethod
        def from_models_dir(cls, _models_dir: Path) -> object:
            raise AssertionError("status endpoint initialized the heavy predictor")

    monkeypatch.setattr(service_module, "FoodPredictor", PredictorShouldNotLoad)

    response = asyncio.run(_get("/v1/ml/status"))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["available"] is True
    assert data["loaded"] is False
    assert {model["filename"] for model in data["models"]} == {"detector.onnx", "encoder.onnx", "decoder.onnx"}
    assert all(model["present"] for model in data["models"])


def test_ml_status_with_models_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    _use_models_dir(monkeypatch, models_dir)

    response = asyncio.run(_get("/v1/ml/status"))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unavailable"
    assert data["available"] is False
    assert data["loaded"] is False
    assert all(not model["present"] for model in data["models"])
    assert "missing_model_files" in data["warnings"]
    assert "model_manifest_missing" in data["warnings"]


def test_ml_status_does_not_initialize_heavy_ml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    _use_models_dir(monkeypatch, models_dir)

    class PredictorShouldNotLoad:
        @classmethod
        def from_models_dir(cls, _models_dir: Path) -> object:
            raise RuntimeError("heavy initialization should not be called")

    monkeypatch.setattr(service_module, "FoodPredictor", PredictorShouldNotLoad)

    response = asyncio.run(_get("/v1/ml/status"))

    assert response.status_code == 200
    assert response.json()["loaded"] is False


def test_ml_warmup_initializes_predictor(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _use_models_dir(monkeypatch, tmp_path / "models")
    calls = []

    class CountingFoodPredictor:
        @classmethod
        def from_models_dir(cls, models_dir: Path) -> FakePredictor:
            calls.append(models_dir)
            return FakePredictor()

    monkeypatch.setattr(service_module, "FoodPredictor", CountingFoodPredictor)

    response = asyncio.run(_post("/v1/ml/warmup"))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["available"] is True
    assert data["loaded"] is True
    assert isinstance(data["load_duration_ms"], int)
    assert len(calls) == 1


def test_ml_warmup_maps_model_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _use_models_dir(monkeypatch, tmp_path / "models")

    class UnavailableFoodPredictor:
        @classmethod
        def from_models_dir(cls, _models_dir: Path) -> object:
            raise service_module.MLModelUnavailableError("missing models")

    monkeypatch.setattr(service_module, "FoodPredictor", UnavailableFoodPredictor)

    response = asyncio.run(_post("/v1/ml/warmup"))

    assert response.status_code == 503
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["status"] == "error"
    assert data["error"]["code"] == "model_unavailable"


def test_valid_image_upload_with_mocked_ml_success() -> None:
    FakeFoodPredictor.predictor = FakePredictor(
        instances=[
            SimpleNamespace(
                instance_id=1,
                proposal_class_id=4,
                label="4",
                bbox=(1.0, 2.0, 20.0, 22.0),
                confidence=0.82,
                area_px=300,
                polygon=((0.1, 0.1), (0.2, 0.2)),
            )
        ]
    )

    response = asyncio.run(_post_file(_jpeg_bytes()))

    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["status"] == "success"
    assert data["summary"]["is_estimated"] is True
    assert data["components"][0]["display_name"] == "Arroz"
    assert data["image"]["original_url"].startswith("/v1/assets/uploads/")


def test_valid_jpeg_with_octet_stream_upload_passes() -> None:
    FakeFoodPredictor.predictor = FakePredictor(
        instances=[
            SimpleNamespace(
                instance_id=1,
                proposal_class_id=4,
                label="4",
                bbox=(1.0, 2.0, 20.0, 22.0),
                confidence=0.82,
                area_px=300,
                polygon=(),
            )
        ]
    )

    response = asyncio.run(_post_file(_jpeg_bytes(), "application/octet-stream"))

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_valid_png_with_octet_stream_upload_passes() -> None:
    FakeFoodPredictor.predictor = FakePredictor(instances=[])

    response = asyncio.run(_post_file(_png_bytes(), "application/octet-stream"))

    assert response.status_code == 200
    assert response.json()["status"] == "empty"


def test_invalid_image_returns_400() -> None:
    response = asyncio.run(_post_file(b"not an image"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image"


def test_random_octet_stream_returns_invalid_image() -> None:
    response = asyncio.run(_post_file(b"not an image", "application/octet-stream"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image"


def test_heic_mime_returns_unsupported_media_type_without_server_heic_support() -> None:
    response = asyncio.run(_post_file(b"\x00\x00\x00\x18ftypheic", "image/heic"))

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_unsupported_mime_returns_415() -> None:
    response = asyncio.run(_post_file(_jpeg_bytes(), "text/plain"))

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_oversized_upload_returns_413() -> None:
    response = asyncio.run(_post_file(b"x" * (5 * 1024 * 1024 + 2)))

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_zero_detections_returns_empty() -> None:
    FakeFoodPredictor.predictor = FakePredictor(instances=[])

    response = asyncio.run(_post_file(_jpeg_bytes()))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "empty"
    assert data["summary"] is None
    assert data["components"] == []
    assert data["warnings"] == ["no_food_detected"]


def test_ml_failure_returns_standardized_error() -> None:
    FakeFoodPredictor.predictor = FakePredictor(fail=service_module.MLInferenceError("boom"))

    response = asyncio.run(_post_file(_jpeg_bytes()))

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "inference_failed"


def test_assets_reject_path_traversal() -> None:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/v1/assets/uploads/..%2Fprato_do_dia.db")

    response = asyncio.run(request())

    assert response.status_code == 404


def test_assets_do_not_expose_unknown_kinds(isolated_backend: Path) -> None:
    (isolated_backend / "reports").mkdir()
    (isolated_backend / "reports" / "debug.json").write_text("{}", encoding="utf-8")

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/v1/assets/reports/debug.json")

    response = asyncio.run(request())

    assert response.status_code == 404
