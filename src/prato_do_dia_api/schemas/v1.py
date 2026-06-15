from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiErrorBody(BaseModel):
    code: Literal[
        "invalid_image",
        "unsupported_media_type",
        "file_too_large",
        "model_unavailable",
        "inference_failed",
        "database_error",
        "contract_error",
    ]
    message: str
    details: Any = None


class ApiErrorResponse(BaseModel):
    schema_version: str = "1.0"
    status: Literal["error"] = "error"
    error: ApiErrorBody


class MlModelFileStatus(BaseModel):
    filename: str
    role: str
    present: bool
    size_bytes: int | None = None
    sha256: str | None = None
    checksum_ok: bool | None = None


class MlStatusResponse(BaseModel):
    status: Literal["available", "unavailable"]
    available: bool
    loaded: bool
    models_dir: str
    models: list[MlModelFileStatus] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MlWarmupResponse(BaseModel):
    status: Literal["ready"]
    available: bool
    loaded: bool
    load_duration_ms: int
    already_loaded: bool = False
    warnings: list[str] = Field(default_factory=list)


class MealImageInfo(BaseModel):
    width: int
    height: int
    original_url: str
    overlay_url: str | None = None


class MealSummary(BaseModel):
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    score: float
    is_estimated: bool = True


class MealComponent(BaseModel):
    id: int
    label: str
    display_name: str
    confidence: float
    bbox: list[float] = Field(default_factory=list)
    area_px: int
    calories: int
    protein: float
    carbs: float
    fat: float
    warnings: list[str] = Field(default_factory=list)


class ModelInfo(BaseModel):
    pipeline: str
    version: str


class MealAnalysisResponse(BaseModel):
    schema_version: str = "1.0"
    analysis_id: str
    status: Literal["success", "empty"]
    image: MealImageInfo
    summary: MealSummary | None
    components: list[MealComponent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model: ModelInfo
