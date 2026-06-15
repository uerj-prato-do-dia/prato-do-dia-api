# Prato do Dia API

Backend FastAPI do projeto Prato do Dia. A API recebe imagens do app Flutter,
valida o upload, chama o pacote Python de ML localmente e retorna um contrato
JSON v1 estável.

Não há autenticação nesta fase.

## Stack

- Python 3.12
- uv
- FastAPI
- SQLite + SQLAlchemy
- Pydantic Settings
- pytest, ruff, basedpyright

## Setup

```bash
uv sync --locked
```

Execute localmente na porta usada pelo app:

```bash
uv run uvicorn prato_do_dia_api.main:app --host 0.0.0.0 --port 42917 --reload
```

## Variáveis de ambiente

- `DATABASE_URL`: padrão `sqlite:///./data/prato_do_dia.db`
- `MAX_UPLOAD_BYTES`: padrão `5242880`
- `MAX_IMAGE_WIDTH`: padrão `4096`
- `MAX_IMAGE_HEIGHT`: padrão `4096`
- `PUBLIC_ASSETS_BASE_PATH`: padrão `/v1/assets`
- `ML_MODELS_DIR`: diretório com os ONNX, se diferente do padrão
- `ML_ROOT`: raiz do repositório ML, se o layout local for diferente

## Endpoints

Compatibilidade temporária:

- `GET /health`
- `POST /meals/analyze`

Contrato v1 documentado:

- `GET /v1/health`
- `GET /v1/ml/status`
- `POST /v1/meals/analyze`
- `GET /v1/assets/uploads/{filename}`
- `GET /v1/assets/overlays/{filename}`

O contrato detalhado de `POST /v1/meals/analyze` está em
[`docs/api_contract_v1.md`](docs/api_contract_v1.md).

## Integração com ML

A API consome `prato_do_dia_ml.inference.FoodPredictor` como biblioteca Python.
O pacote ML continua no mesmo processo da API; ele não deve ser exposto como um
serviço HTTP separado nesta versão.

Os modelos esperados ficam em:

```text
../prato-do-dia-ml/models/
```

ou no caminho definido por `ML_MODELS_DIR`.

## Uso com o app mobile

Emulador Android:

```text
http://10.0.2.2:42917
```

Celular físico com `adb reverse`:

```bash
adb reverse tcp:42917 tcp:42917
```

Use no app:

```text
http://localhost:42917
```

## Validação

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
uv run basedpyright
```

## Limitações

A nutrição retornada é estimada por classe detectada. O pipeline ainda não mede
porção real, peso ou volume do alimento. A resposta v1 sinaliza isso com
`nutrition_is_estimated` e `portion_size_not_measured`.
