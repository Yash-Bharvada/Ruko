#!/usr/bin/env python3
"""
Score messages with the trained model and explain the result.

    python predict.py "Guaranteed 30% monthly returns, join VIP group http://x.xyz"
    python predict.py --file messages.txt      # one message per line
Import use:
    from predict import RukoModel; RukoModel().check("text")
"""
import argparse, os, sys, warnings, numpy as np, joblib
warnings.filterwarnings("ignore")
from scipy.sparse import hstack
from common import preprocess

class RukoModel:
    # Probability bands -> honest three-state verdict. Tune on your own test set.
    HIGH, LOW = 0.80, 0.20

    def __init__(self, path=None):
        if path is None:
            if os.path.exists(os.path.join("artifacts", "model.joblib")):
                path = os.path.join("artifacts", "model.joblib")
            elif os.path.exists("model.joblib"):
                path = "model.joblib"
            else:
                path = os.path.join("artifacts", "model.joblib")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found. Run train_model.py first.")
        b = joblib.load(path)
        self.word, self.char, self.clf, self.threshold = b["word"], b["char"], b["clf"], b["threshold"]
        if not hasattr(self.clf, "multi_class"):
            self.clf.multi_class = "auto"
        self.n_word = len(self.word.get_feature_names_out())
        self.word_names = self.word.get_feature_names_out()

    def _x(self, text):
        t = [text if isinstance(text, str) else ""]
        return hstack([self.word.transform(t), self.char.transform(t)]).tocsr()

    def check(self, text, top=5):
        if not isinstance(text, str) or not text.strip():
            return {"verdict": "cannot_verify", "score": None,
                    "reasons": ["Empty message - nothing to check."],
                    "note": "Not enough text to assess."}
        X = self._x(text)
        p = float(self.clf.predict_proba(X)[0, 1])
        # explanation: contribution of WORD features only (readable); char n-grams are not shown
        coef = self.clf.coef_[0][: self.n_word]
        row = X[:, : self.n_word].tocoo()
        contrib = sorted(((self.word_names[j], v * coef[j]) for j, v in zip(row.col, row.data)),
                         key=lambda x: -x[1])
        red = [w for w, c in contrib if c > 0][:top]
        calm = [w for w, c in sorted(contrib, key=lambda x: x[1]) if c < 0][:3]
        if p >= self.HIGH:   verdict = "strong_red_flags"
        elif p <= self.LOW:  verdict = "no_red_flags_found"
        else:                verdict = "cannot_verify"
        note = {"strong_red_flags": "This message strongly resembles known scam patterns. Do not pay or share OTP/PIN.",
                "cannot_verify": "Mixed signals. We cannot tell. Verify with an official source (SEBI, your bank) before acting.",
                "no_red_flags_found": "No known red-flag patterns found. This does NOT mean it is safe."}[verdict]
        return {"verdict": verdict, "score": round(p, 3), "words_that_raised_risk": red,
                "words_that_lowered_risk": calm, "note": note}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("text", nargs="?"); ap.add_argument("--file")
    a = ap.parse_args()
    m = RukoModel()
    msgs = [l.strip() for l in open(a.file, encoding="utf-8")] if a.file else [a.text or ""]
    for s in msgs:
        r = m.check(s); print(f"\n> {s[:90]}\n  {r}")

if __name__ == "__main__":
    main()
