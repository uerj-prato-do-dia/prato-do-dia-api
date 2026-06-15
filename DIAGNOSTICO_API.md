# Diagnóstico da API

## Resumo executivo

A API é um backend FastAPI pequeno e funcional para protótipo, com um endpoint principal de análise de refeição que integra diretamente com o repo ML local. O fluxo básico passa nos testes, mas o contrato ainda está frágil: sem autenticação, sem versionamento, sem limites de upload, com dependência absoluta do repo ML e documentação README desatualizada.

## Arquitetura encontrada

Framework: FastAPI com Python 3.12, SQLAlchemy, SQLite, Pydantic Settings, Pillow e integração direta com `prato-do-dia-ml`.

Estrutura principal:

- `src/prato_do_dia_api/main.py`: cria `FastAPI`, inicializa banco no lifespan e monta `/static`.
- `src/prato_do_dia_api/api/routes/health.py`: healthcheck.
- `src/prato_do_dia_api/api/routes/meals.py`: endpoint de upload/análise.
- `src/prato_do_dia_api/schemas/meal.py`: modelos Pydantic de resposta.
- `src/prato_do_dia_api/db/models.py`: tabelas `meal_records` e `meal_components`.
- `src/prato_do_dia_api/db/session.py`: engine SQLAlchemy, sessão e `create_all`.
- `src/prato_do_dia_api/services/ml_service.py`: singleton da pipeline YOLO + SAM.
- `src/prato_do_dia_api/services/nutrition_mapper.py`: mapeamento de classes para macros.

Endpoints encontrados:

- `GET /`
- `GET /health`
- `POST /meals/analyze`
- `GET /static/...`, por montagem de arquivos estáticos em `main.py`

## Funcionalidades existentes

- Healthcheck funcionando.
- Upload multipart de imagem em `POST /meals/analyze`.
- Validação básica da imagem com Pillow e remoção de EXIF antes de persistir.
- Execução da pipeline ML real via `MLService.analyze_image`.
- Geração de `image_url` e `overlay_url`.
- Persistência de refeição e componentes segmentados em SQLite.
- Criação automática das tabelas no startup.
- OpenAPI automático do FastAPI disponível, embora não exportado/congelado.
- Teste de imagem inválida retornando HTTP 400.

## Lacunas e problemas

### Crítico

- Sem autenticação/autorização. O README confirma ausência de auth.
- `/static` expõe todo o diretório `data/`, incluindo uploads, overlays, masks, reports e possivelmente banco local se acessível por caminho.
- Sem limite de tamanho de upload, sem checagem explícita de MIME, sem proteção contra imagens muito grandes.

### Importante

- Dependência do ML está fixada com caminho absoluto local em `pyproject.toml`, o que quebra portabilidade/CI.
- Endpoint principal mistura upload, validação, ML, mapeamento nutricional, persistência e montagem de resposta no mesmo handler.
- Falhas do ML ou do banco sobem como exceções genéricas depois do rollback, sem resposta padronizada.
- `basedpyright` falha com 12 erros por tipagem fraca de `FOOD_PROFILES`.
- Banco usa `Base.metadata.create_all`, sem migrations reais, apesar do README listar Alembic.
- README está desatualizado: lista só `/` e `/health`, mas existe `/meals/analyze`.

### Menor

- Há fallback mockado quando nenhuma detecção gera componente.
- `orjson` aparece como dependência, mas não foi identificado uso.
- `MealAnalysisResponse.components` usa lista mutável como default; Pydantic lida melhor que dataclasses, mas `default_factory` seria mais explícito.
- Configuração por ambiente é mínima: só `APP_NAME`, `APP_ENV`, `DATABASE_URL`.

## Contratos importantes

Mobile provavelmente consome:

- `GET /health`: resposta `{ "status": "ok", "service": "prato-do-dia-api" }`.
- `POST /meals/analyze`: `multipart/form-data` com campo `file`.
- `GET /static/uploads/{uuid}.jpg` e `GET /static/overlays/{uuid}_overlay.jpg`.

Incerteza: o repo mobile não foi analisado. A inferência acima vem do contrato exposto pela API e dos nomes de resposta.

Resposta principal de `/meals/analyze`:

```json
{
  "name": "string",
  "calories": 0,
  "protein": 0.0,
  "carbs": 0.0,
  "fat": 0.0,
  "ingredients": ["string"],
  "score": 0.0,
  "image_url": "/static/uploads/...",
  "overlay_url": "/static/overlays/...",
  "components": [
    {
      "label": "string",
      "confidence": 0.0,
      "calories": 0,
      "protein": 0.0,
      "carbs": 0.0,
      "fat": 0.0
    }
  ]
}
```

ML esperado:

- Pacote `prato_do_dia_ml`.
- Classes `YoloOnnxDetector`, `SamOnnxSegmenter`, `FoodSegmentationPipeline`.
- Modelos esperados em `ML_MODELS_DIR` ou `../prato-do-dia-ml/models`:
  - `yolov11_food.onnx`
  - `sam2.1_hiera_tiny.encoder.onnx`
  - `sam2.1_hiera_tiny.decoder.onnx`

## Testes e qualidade

Comandos executados:

- `uv run pytest`: 3 testes passaram.
- `uv run ruff check .`: passou.
- `uv run basedpyright`: falhou com 12 erros.

Observação: `pytest` não é isolado. O teste de refeições depende de imagem no repo ML em `../prato-do-dia-ml/data/input/imagem1.jpg`, usa a pipeline real e grava artefatos em `data/`. A execução dos testes gerou/atualizou arquivos ignorados pelo Git em `data/`.

## Riscos técnicos

### Críticos

- API pública sem auth e com endpoint caro de inferência.
- Upload sem limite de tamanho e sem controles robustos de tipo/conteúdo.
- Exposição ampla de arquivos via `/static`.
- Dependência operacional forte do repo ML local e dos pesos ONNX.

### Importantes

- Contrato mobile não versionado.
- Erros de ML não são traduzidos para respostas estáveis.
- Sem logging estruturado nem rastreio de requisições.
- Sem migrations; evolução do banco pode quebrar dados existentes.
- Testes de integração misturam API, ML real e banco local.
- README/OpenAPI não estão congelados como contrato de integração.

### Menores

- Tipagem de perfis nutricionais fraca.
- Fallback mockado pode mascarar falha de detecção.
- Dependências/documentação inconsistentes.
- Sem endpoints para consultar histórico de refeições já persistidas.

## Plano recomendado

### Fase 1: estabilização mínima

- Adicionar limites de upload e validação explícita de formato/tamanho.
- Restringir `/static` a subpastas realmente públicas ou criar endpoints controlados para imagens/overlays.
- Padronizar erros de `/meals/analyze`: imagem inválida, modelo ausente, falha de inferência, falha de banco.
- Corrigir `basedpyright`.
- Atualizar README com `/meals/analyze`, variáveis `ML_ROOT`/`ML_MODELS_DIR` e dependências reais.
- Separar teste unitário do contrato de `/meals/analyze` usando mock da pipeline.

### Fase 2: contrato e integração

- Congelar schema de `POST /meals/analyze` para mobile.
- Exportar OpenAPI versionado ou documentar exemplos reais de request/response.
- Definir se `image_url`/`overlay_url` serão paths relativos ou URLs absolutas.
- Definir contrato API-ML: classes, IDs, confidence, segmentations, nomes de artefatos e erros.
- Criar prefixo de versão, por exemplo `/v1`.
- Decidir comportamento correto quando nenhuma comida é detectada: fallback mockado, resposta vazia ou erro controlado.

### Fase 3: melhorias estruturais

- Extrair service de aplicação para análise de refeições, deixando a rota fina.
- Introduzir Alembic de verdade ou remover a promessa do README.
- Criar repositório/camada de persistência para refeições.
- Adicionar testes de contrato, testes de falha do ML e testes de persistência isolados.
- Adicionar logging estruturado, request id e métricas básicas de latência/inferência.
- Tornar a dependência ML instalável sem caminho absoluto local.

## Próximas ações sugeridas

1. Corrigir documentação e contrato público de `/meals/analyze`.
2. Colocar limites e validações de upload.
3. Padronizar erros do endpoint de análise.
4. Restringir exposição de `/static`.
5. Remover caminho absoluto do repo ML em `pyproject.toml`.
6. Corrigir typecheck.
7. Isolar testes da pipeline ML real.
8. Introduzir versionamento `/v1` antes do mobile depender fortemente do contrato.
