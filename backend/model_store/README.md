# Model Store

Drop your trained scikit-learn text classifier package into this directory (`backend/model_store/`).

## Required Files

1. `model.joblib`:
   The scikit-learn pipeline bundle dictionary containing keys:
   - `word` (TfidfVectorizer for words)
   - `char` (TfidfVectorizer for character n-grams)
   - `clf` (Trained classifier, e.g., LogisticRegression / SGDClassifier)
   - `threshold` (e.g., 0.41)
   - `version`

2. `common.py`:
   **REQUIRED**: The saved vectorizers reference `common.preprocess`.
   This file must be in this folder so it can be imported as a top-level module named `common`.

3. `predict.py`:
   Exposes class `RukoModel(path=None)` with method:
   `check(text: str, top: int = 5) -> dict`
   Returning:
   ```python
   {
       "verdict": "...",  # (Ignored by backend verdict engine)
       "score": 0.85,  # float probability or None
       "words_that_raised_risk": ["guaranteed", "vip", "profit"],
       "words_that_lowered_risk": ["ref", "credited"],
       "note": "...",
   }
   ```

4. `model_card.json`:
   Records the exact scikit-learn version trained with.
   Run:
   ```bash
   pip freeze | findstr scikit
   ```
   Save as `model_card.json`:
   ```json
   {
     "sklearn_version": "1.3.0",
     "trained_on": "2026-03-01",
     "notes": "Trained on SMS/WhatsApp fraud messages dataset"
   }
   ```

## How to Test

Once files are copied into `backend/model_store/`, run from `backend/`:
```bash
python scripts/check_model.py "Guaranteed 30% monthly returns, join VIP group, send Rs 5000 to trade55@ybl"
```
You should see `available=True` and a score > 0.80.
