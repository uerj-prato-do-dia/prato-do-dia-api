#!/usr/bin/env python3
"""Offline OpenAPI specification exporter script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPTS_DIR.parent
PROJECT_ROOT = API_ROOT.parent

# Add src to sys.path
sys.path.insert(0, str(API_ROOT / "src"))

from prato_do_dia_api.main import app  # noqa: E402


def export_openapi_schema(output_path: Path) -> Path:
    openapi_schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    formatted_json = json.dumps(openapi_schema, indent=2, ensure_ascii=False)
    output_path.write_text(formatted_json, encoding="utf-8")
    return output_path


def main() -> int:
    root_openapi = PROJECT_ROOT / "openapi.json"
    api_openapi = API_ROOT / "openapi.json"

    export_openapi_schema(root_openapi)
    export_openapi_schema(api_openapi)

    print(f"✔ Successfully exported OpenAPI schema to {root_openapi}")
    print(f"✔ Successfully exported OpenAPI schema to {api_openapi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
