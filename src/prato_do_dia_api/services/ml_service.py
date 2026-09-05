import os
from pathlib import Path

from prato_do_dia_ml.inference import FoodPredictor, PlatePredictionResponse, get_predictor

project_root = Path(__file__).resolve().parent.parent.parent.parent

env_ml_root = os.environ.get("ML_ROOT")
ML_ROOT = Path(env_ml_root) if env_ml_root else project_root.parent / "prato-do-dia-ml"

env_models_dir = os.environ.get("ML_MODELS_DIR")
MODELS_DIR = Path(env_models_dir) if env_models_dir else ML_ROOT / "models"

DATA_DIR = project_root / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


class MLService:
    _predictor: FoodPredictor | None = None

    @classmethod
    def get_predictor(cls) -> FoodPredictor:
        """Loads and returns the predictor singleton."""
        if cls._predictor is None:
            cls._predictor = get_predictor(MODELS_DIR)
        return cls._predictor

    @classmethod
    def analyze_bytes(cls, image_bytes: bytes) -> PlatePredictionResponse:
        """Executes prediction on image bytes and returns the result."""
        predictor = cls.get_predictor()
        return predictor.predict_bytes(image_bytes)

    @classmethod
    def analyze_image(cls, image_path: Path) -> PlatePredictionResponse:
        """Executes prediction on an image file path and returns the result."""
        image_bytes = image_path.read_bytes()
        return cls.analyze_bytes(image_bytes)
