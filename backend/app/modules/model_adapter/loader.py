"""Model loader for initializing the scam prediction model."""

import importlib
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple
from app.core.config import Settings
from app.core.logging import logger
from app.modules.model_adapter.adapter import RealModelScorer
from app.modules.model_adapter.contract import ScamScorer
from app.modules.model_adapter.dummy import DummyScorer


def _resolve_model_dir(settings: Settings) -> Path:
    """Resolve absolute path to model_store directory."""
    raw_path = Path(settings.MODEL_DIR)
    if raw_path.is_absolute():
        return raw_path

    # Try relative to backend root or cwd
    candidate = Path.cwd() / raw_path
    if candidate.exists():
        return candidate.resolve()

    # Try relative to this file's root (backend/app/...)
    backend_root = Path(__file__).resolve().parent.parent.parent.parent
    return (backend_root / raw_path).resolve()


def load_model(settings: Settings) -> Tuple[ScamScorer, List[str]]:
    """Load scikit-learn model package from MODEL_DIR.

    Returns:
        (ScamScorer, degraded_flags)
    """
    degraded_flags: List[str] = []
    abs_model_dir = _resolve_model_dir(settings)

    # 1. Check directory existence
    if not abs_model_dir.exists() or not abs_model_dir.is_dir():
        msg = f"Model directory not found at {abs_model_dir}"
        if settings.MODEL_REQUIRED:
            raise RuntimeError(msg)
        logger.warning(msg)
        return DummyScorer(), ["model_unavailable"]

    # 2. Check required files
    required_files = ["model.joblib", "common.py", "predict.py"]
    missing = [f for f in required_files if not (abs_model_dir / f).is_file()]
    if missing:
        msg = f"Model directory {abs_model_dir} is missing required files: {missing}"
        if settings.MODEL_REQUIRED:
            raise RuntimeError(msg)
        logger.warning(msg)
        return DummyScorer(), ["model_unavailable"]

    # 3. Add MODEL_DIR to front of sys.path so 'common' and 'predict' resolve as top-level modules
    str_model_dir = str(abs_model_dir)
    if str_model_dir not in sys.path:
        sys.path.insert(0, str_model_dir)
    elif sys.path[0] != str_model_dir:
        sys.path.remove(str_model_dir)
        sys.path.insert(0, str_model_dir)

    # 4. Check model_card.json for scikit-learn version match
    card_path = abs_model_dir / "model_card.json"
    if card_path.is_file():
        try:
            with open(card_path, "r", encoding="utf-8") as f:
                card_data = json.load(f)
            trained_version = card_data.get("sklearn_version")
            if trained_version:
                import sklearn
                trained_major = trained_version.split(".")[0]
                current_major = sklearn.__version__.split(".")[0]
                if trained_major != current_major:
                    logger.warning(
                        "Scikit-learn version mismatch: trained on %s, running on %s",
                        trained_version,
                        sklearn.__version__,
                    )
                    degraded_flags.append("model_version_mismatch")
                elif sklearn.__version__ != trained_version:
                    logger.info(
                        "Scikit-learn minor version difference: trained on %s, running on %s",
                        trained_version,
                        sklearn.__version__,
                    )
        except Exception as exc:
            logger.warning("Failed to parse model_card.json: %s", str(exc))

    # 5. Import predict module and instantiate RukoModel with explicit absolute joblib path
    abs_joblib = abs_model_dir / "model.joblib"
    try:
        if "predict" in sys.modules:
            predict_module = importlib.reload(sys.modules["predict"])
        else:
            predict_module = importlib.import_module("predict")

        ruko_model_cls = getattr(predict_module, "RukoModel")
        model_instance = ruko_model_cls(path=str(abs_joblib))
        logger.info("Successfully loaded ML model from %s", abs_joblib)
        return RealModelScorer(model_instance), degraded_flags
    except Exception as exc:
        msg = f"Failed to load RukoModel from {abs_joblib}: {exc}"
        if settings.MODEL_REQUIRED:
            raise RuntimeError(msg) from exc
        logger.warning(msg)
        if "model_unavailable" not in degraded_flags:
            degraded_flags.append("model_unavailable")
        return DummyScorer(), degraded_flags
