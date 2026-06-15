# Contrato da API v1

Este documento descreve o contrato estável v1 consumido pelo aplicativo Flutter.

## `GET /v1/ml/status`

Retorna o estado configurado do ML sem carregar ONNX Runtime, sem inicializar o
predictor e sem executar inferência. Este endpoint é adequado para health checks
e smoke tests leves.

Query params:

- `verify_checksum`: padrão `false`. Quando `true`, calcula SHA256 dos arquivos
  de modelo presentes; isso pode ser custoso.

Exemplo:

```json
{
  "status": "available",
  "available": true,
  "loaded": false,
  "models_dir": "/caminho/local/models",
  "models": [
    {
      "filename": "yolov11_food.onnx",
      "role": "detector",
      "present": true,
      "size_bytes": 10741341,
      "sha256": "4ac77a556992be1f2ec2924441b49a4bd406bae2719e6dc293948acc086d98e4",
      "checksum_ok": null
    }
  ],
  "warnings": []
}
```

`models_dir` é um caminho local voltado ao ambiente de desenvolvimento/operacao
da API. O cliente mobile não deve depender dele.

## `POST /v1/ml/warmup`

Inicializa explicitamente o predictor/model stack. Este endpoint é pesado por
design e deve ser chamado apenas quando o processo precisa preparar inferência.

Resposta:

```json
{
  "status": "ready",
  "available": true,
  "loaded": true,
  "load_duration_ms": 5230,
  "already_loaded": false,
  "warnings": []
}
```

Se os modelos não estiverem disponíveis, retorna erro padronizado v1 com código
`model_unavailable`.

## `POST /v1/meals/analyze`

Analisa uma imagem de refeição usando o pipeline local YOLO11 + SAM2 ONNX.

- Método: `POST`
- Content-Type: `multipart/form-data`
- Campo do arquivo: `file`
- Formatos aceitos atualmente: JPEG (`image/jpeg`) e PNG (`image/png`)
- Limite padrão de upload: 5 MB
- Dimensões máximas decodificadas: 4096 x 4096 px

HEIC (`image/heic`) só deve ser habilitado quando o ambiente Pillow do backend suportar decodificação HEIC.

## Resposta de sucesso

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "status": "success",
  "image": {
    "width": 640,
    "height": 640,
    "original_url": "/v1/assets/uploads/uuid.jpg",
    "overlay_url": "/v1/assets/overlays/uuid_overlay.jpg"
  },
  "summary": {
    "name": "Refeição analisada",
    "calories": 650,
    "protein": 30.0,
    "carbs": 80.0,
    "fat": 20.0,
    "score": 7.2,
    "is_estimated": true
  },
  "components": [
    {
      "id": 1,
      "label": "rice",
      "display_name": "Arroz",
      "confidence": 0.82,
      "bbox": [120, 80, 310, 260],
      "area_px": 35210,
      "calories": 210,
      "protein": 4.0,
      "carbs": 45.0,
      "fat": 1.0,
      "warnings": []
    }
  ],
  "warnings": [
    "nutrition_is_estimated",
    "portion_size_not_measured"
  ],
  "model": {
    "pipeline": "yolo11_sam2_onnx",
    "version": "baseline-2026-06-15"
  }
}
```

## Resposta sem alimento detectado

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "status": "empty",
  "image": {
    "width": 640,
    "height": 640,
    "original_url": "/v1/assets/uploads/uuid.jpg",
    "overlay_url": null
  },
  "summary": null,
  "components": [],
  "warnings": ["no_food_detected"],
  "model": {
    "pipeline": "yolo11_sam2_onnx",
    "version": "baseline-2026-06-15"
  }
}
```

## Resposta de erro

```json
{
  "schema_version": "1.0",
  "status": "error",
  "error": {
    "code": "invalid_image",
    "message": "A imagem enviada não é válida.",
    "details": null
  }
}
```

Códigos padronizados:

- `invalid_image`
- `unsupported_media_type`
- `file_too_large`
- `model_unavailable`
- `inference_failed`
- `database_error`
- `contract_error`

## Semântica dos campos

- `schema_version`: versão do contrato JSON da API.
- `analysis_id`: UUID gerado pelo backend para a análise.
- `status`: `success` quando há componentes de comida, `empty` quando nada foi detectado, `error` em falhas padronizadas.
- `confidence`: confiança do detector/segmentador para o componente. Não é uma probabilidade nutricional.
- `summary` e campos nutricionais por componente: estimativas por classe detectada, baseadas em perfis fixos. A porção real não é medida.
- `warnings`: limitações relevantes para o cliente. A v1 sempre sinaliza `nutrition_is_estimated` e `portion_size_not_measured` quando há sucesso.
- URLs em `image`: caminhos relativos ao host da API. O cliente deve resolver `/v1/assets/...` contra a origem configurada.

## Assets públicos

Somente estes caminhos são públicos:

- `GET /v1/assets/uploads/{filename}`
- `GET /v1/assets/overlays/{filename}`

Arquivos de banco, relatórios, máscaras, segmentações brutas e outros caminhos internos não fazem parte da superfície pública.
