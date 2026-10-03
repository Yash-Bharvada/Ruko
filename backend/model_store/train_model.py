#!/usr/bin/env python3
"""
Train the Ruko scam-message classifier.

Usage:
    python train_model.py                              # trains on sangyan_all_data.csv
    python train_model.py --data path/to/data.csv
    python train_model.py --own-test my_test.csv       # also evaluate on your hand-written set (columns: text,label)

Outputs (in ./artifacts): model.joblib, metrics.json, report.txt
"""
import argparse, json, os, sys, warnings
import numpy as np, pandas as pd, joblib
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             precision_recall_fscore_support, precision_recall_curve)
from common import preprocess, TOKEN_PATTERN

warnings.filterwarnings("ignore")
SEED = 42
REQUIRED = ["text", "label", "split"]

def fail(msg):
    print(f"\nERROR: {msg}", file=sys.stderr); sys.exit(1)

def load(path):
    if not os.path.exists(path): fail(f"data file not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    miss = [c for c in REQUIRED if c not in df.columns]
    if miss: fail(f"missing columns {miss}; found {list(df.columns)}")
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(int)
    if not set(df.label.unique()) <= {0, 1}: fail("label must be 0/1")
    for opt in ("language", "source", "scam_type", "template_id"):
        if opt not in df.columns: df[opt] = "unknown"
    return df

def build_vectorizers():
    word = TfidfVectorizer(preprocessor=preprocess, token_pattern=TOKEN_PATTERN, ngram_range=(1, 2),
                           min_df=2, sublinear_tf=True, max_features=150_000, lowercase=False)
    char = TfidfVectorizer(preprocessor=preprocess, analyzer="char_wb", ngram_range=(2, 5),
                           min_df=3, sublinear_tf=True, max_features=250_000, lowercase=False)
    return word, char

def featurize(word, char, texts, fit=False):
    if fit:  return hstack([word.fit_transform(texts), char.fit_transform(texts)]).tocsr()
    return hstack([word.transform(texts), char.transform(texts)]).tocsr()

def fit_model(train_texts, y, C=3.0):
    word, char = build_vectorizers()
    X = featurize(word, char, train_texts, fit=True)
    clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced", solver="liblinear", random_state=SEED)
    clf.fit(X, y)
    return word, char, clf

def predict_proba(word, char, clf, texts):
    return clf.predict_proba(featurize(word, char, texts))[:, 1]

def metrics(y, p, thr=0.5):
    pred = (p >= thr).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(y, pred, labels=[1], zero_division=0)
    return {"n": int(len(y)), "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
            "scam_precision": round(float(pr[0]), 4), "scam_recall": round(float(rc[0]), 4)}

def pick_threshold(y, p, lo=0.30, hi=0.70):
    """Threshold that maximises macro-F1 on VALIDATION data, clamped to [lo, hi].
    The clamp stops a near-perfect validation set from picking an extreme, brittle cut-off."""
    best_t, best_f = 0.5, -1.0
    for t in np.linspace(lo, hi, 41):
        f = f1_score(y, (p >= t).astype(int), average="macro")
        if f > best_f + 1e-9: best_t, best_f = float(t), f
    return best_t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="sangyan_all_data.csv")
    ap.add_argument("--out", default="artifacts")
    ap.add_argument("--own-test", default=None, help="CSV with columns text,label (your hand-written test set)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lines = []
    def log(s=""):
        print(s); lines.append(s)

    df = load(a.data)
    df = df[df.split.isin(["train", "val", "test"])]
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    if min(len(tr), len(va), len(te)) == 0: fail("train/val/test split is empty")

    # ---- leakage guard: no template may appear in two splits
    if "template_id" in df.columns and df.template_id.nunique() > 1:
        ov = set(tr.template_id) & set(te.template_id)
        log(f"Leakage check: templates shared by train and test = {len(ov)}")
        if ov: fail("train/test share templates, results would be inflated. Re-split by template_id.")
    log(f"Rows -> train {len(tr)}, val {len(va)}, test {len(te)}")
    log(f"Scam share -> train {tr.label.mean():.2f}, val {va.label.mean():.2f}, test {te.label.mean():.2f}")

    # ---- fit on train, choose threshold on val, report on test
    word, char, clf = fit_model(tr.text, tr.label)
    pv = predict_proba(word, char, clf, va.text)
    thr = pick_threshold(va.label.values, pv)
    log(f"\nThreshold chosen on validation (max macro-F1, clamped 0.30-0.70): {thr:.3f}")
    pt = predict_proba(word, char, clf, te.text)
    res = {"threshold": thr, "test_overall": metrics(te.label.values, pt, thr)}
    log(f"\n=== TEST (held-out templates) @ threshold {thr:.3f} ===")
    log(classification_report(te.label, (pt >= thr).astype(int), target_names=["legit", "scam"], digits=3))
    log("Confusion matrix [[TN FP],[FN TP]]:\n" + str(confusion_matrix(te.label, (pt >= thr).astype(int))))

    te = te.assign(p=pt)
    for col in ("language", "source", "scam_type"):
        log(f"\n--- by {col} ---")
        res[f"by_{col}"] = {}
        for k, g in te.groupby(col):
            if g.label.nunique() < 2 and col != "scam_type":
                m = {"n": len(g), "accuracy": round(float(((g.p >= thr).astype(int) == g.label).mean()), 4)}
            elif col == "scam_type":
                m = {"n": len(g), "accuracy": round(float(((g.p >= thr).astype(int) == g.label).mean()), 4)}
            else:
                m = metrics(g.label.values, g.p.values, thr)
            res[f"by_{col}"][str(k)] = m; log(f"{k:28s} {m}")

    # ---- harder checks: cross-source generalisation
    log("\n=== Cross-source generalisation (more honest than the split above) ===")
    res["cross_source"] = {}
    srcs = [s for s in df.source.unique() if s != "unknown"]
    for held in srcs:
        rest, test = df[df.source != held], df[df.source == held]
        if len(test) < 50 or test.label.nunique() < 2 or len(rest) < 200: continue
        w, c, m_ = fit_model(rest.text, rest.label)
        f = f1_score(test.label, (predict_proba(w, c, m_, test.text) >= 0.5).astype(int), average="macro")
        res["cross_source"][held] = round(float(f), 4)
        log(f"Hold out '{held}' (train on all other sources): macro-F1 = {f:.3f}  (n={len(test)})")
    log("Note: low numbers here mean the model learned a dataset's generator, not scams in general.")

    # ---- optional: your own hand-written set
    if a.own_test:
        own = pd.read_csv(a.own_test, encoding="utf-8-sig")
        if not {"text", "label"} <= set(own.columns): fail("--own-test needs columns text,label")
        own = own.dropna(subset=["text", "label"])
        po = predict_proba(word, char, clf, own.text.astype(str))
        res["own_test"] = metrics(own.label.astype(int).values, po, thr)
        log(f"\n=== YOUR OWN TEST SET (report this one!) ===\n{res['own_test']}")
        log(classification_report(own.label.astype(int), (po >= thr).astype(int), target_names=["legit", "scam"], digits=3))

    # ---- final model: refit on train+val with the chosen threshold, save
    full = pd.concat([tr, va])
    w, c, m_ = fit_model(full.text, full.label)
    joblib.dump({"word": w, "char": c, "clf": m_, "threshold": thr, "version": 1}, os.path.join(a.out, "model.joblib"))
    json.dump(res, open(os.path.join(a.out, "metrics.json"), "w"), indent=2, ensure_ascii=False)
    open(os.path.join(a.out, "report.txt"), "w", encoding="utf-8").write("\n".join(lines))
    log(f"\nSaved model + reports to ./{a.out}/")

if __name__ == "__main__":
    main()
