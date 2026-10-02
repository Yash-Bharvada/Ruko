"""Script to export OpenAPI specification from FastAPI app to openapi.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import create_app


def export_openapi() -> Path:
    """Generate and write openapi.json."""
    app = create_app()
    openapi_data = app.openapi()

    # Save to backend/openapi.json and repo root openapi.json
    backend_path = Path(__file__).resolve().parent.parent / "openapi.json"
    root_path = Path(__file__).resolve().parent.parent.parent / "openapi.json"

    with open(backend_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2)

    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2)

    print(f"Exported OpenAPI spec to {backend_path} and {root_path}")
    return backend_path


if __name__ == "__main__":
    export_openapi()
