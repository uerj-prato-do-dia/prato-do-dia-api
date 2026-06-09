from pathlib import Path

from prato_do_dia_ml.detector import YoloOnnxDetector
from prato_do_dia_ml.pipeline import FoodSegmentationPipeline
from prato_do_dia_ml.schema import PipelineResult
from prato_do_dia_ml.segmenter import SamOnnxSegmenter

# Diretórios locais e compartilhados
ML_ROOT = Path("/home/gabe/projects/prato-do-dia/prato-do-dia-ml")
MODELS_DIR = ML_ROOT / "models"
DATA_DIR = Path("/home/gabe/projects/prato-do-dia/prato-do-dia-api/data")
UPLOADS_DIR = DATA_DIR / "uploads"


class MLService:
    _pipeline: FoodSegmentationPipeline | None = None

    @classmethod
    def get_pipeline(cls) -> FoodSegmentationPipeline:
        """Loads the models and returns the segmentation pipeline singleton."""
        if cls._pipeline is None:
            # Resolve caminhos absolutos dos modelos ONNX
            yolo_path = MODELS_DIR / "yolov11_food.onnx"
            sam_encoder_path = MODELS_DIR / "sam2.1_hiera_tiny.encoder.onnx"
            sam_decoder_path = MODELS_DIR / "sam2.1_hiera_tiny.decoder.onnx"

            # Valida existência dos pesos
            for path in (yolo_path, sam_encoder_path, sam_decoder_path):
                if not path.exists():
                    raise FileNotFoundError(
                        f"Modelo ONNX não encontrado em: {path}. "
                        f"Por favor, verifique a pasta de modelos no repositório ML."
                    )

            # Inicializa detector e segmentador ONNX (CPU-only)
            detector = YoloOnnxDetector(
                yolo_path,
                confidence_threshold=0.15,
                max_detections=10,
            )
            segmenter = SamOnnxSegmenter(
                sam_encoder_path,
                sam_decoder_path,
            )

            # Cria pastas locais para salvar os artefatos de IA do processamento
            output_dir = DATA_DIR / "raw_segmentations"
            mask_dir = DATA_DIR / "masks"
            overlay_dir = DATA_DIR / "overlays"
            report_dir = DATA_DIR / "reports"
            uploads_dir = DATA_DIR / "uploads"

            for directory in (output_dir, mask_dir, overlay_dir, report_dir, uploads_dir):
                directory.mkdir(parents=True, exist_ok=True)

            cls._pipeline = FoodSegmentationPipeline(
                detector,
                segmenter,
                output_dir=output_dir,
                mask_dir=mask_dir,
                overlay_dir=overlay_dir,
                report_dir=report_dir,
            )
        return cls._pipeline

    @classmethod
    def analyze_image(cls, image_path: Path) -> PipelineResult:
        """Executes the full pipeline on a single image and returns the results."""
        pipeline = cls.get_pipeline()
        return pipeline.run_image(image_path)
