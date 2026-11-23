"""Train and evaluate phishing URL classifiers.

Experiment A (naive): full raw URLs. Shows the dataset bias (all legitimate
URLs look like https://www.<domain> with no path).
Experiment B (fair): hostname only, scheme and 'www.' removed.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from features import full_url_features, host_features, hostname_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
SEED = 42
TITLES = {"A_naive_full_url": "Experiment A: full URL",
          "B_fair_hostname": "Experiment B: hostname only"}


def load():
    df = pd.read_csv(ROOT / "data/raw/PhiUSIIL_Phishing_URL_Dataset.csv",
                     usecols=["URL", "label"], encoding="utf-8-sig")
    df["phishing"] = 1 - df["label"]          # dataset: 1 = legitimate
    df["host"] = df["URL"].map(hostname_of)
    return df


def models():
    return {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "Random Forest": RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=SEED),
    }


def evaluate(name, y_true, y_pred, y_score):
    return {"model": name,
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred),
            "recall": recall_score(y_true, y_pred),
            "f1": f1_score(y_true, y_pred),
            "roc_auc": roc_auc_score(y_true, y_score)}


def run(exp, texts, feat_fn, y):
    X = pd.DataFrame([feat_fn(t) for t in texts])
    Xtr, Xte, Ttr, Tte, ytr, yte = train_test_split(
        X, texts, y, test_size=0.2, stratify=y, random_state=SEED)
    rows = []
    for name, m in models().items():
        m.fit(Xtr, ytr)
        p = m.predict(Xte)
        rows.append(evaluate(name, yte, p, m.predict_proba(Xte)[:, 1]))
        if name == "Random Forest":
            imp = pd.Series(m.feature_importances_, index=X.columns).sort_values()
            imp.plot.barh(figsize=(6, 5), color="#2f5bd3",
                          title=f"Random Forest feature importance\n{TITLES[exp]}")
            plt.tight_layout(); plt.savefig(OUT / f"importance_{exp}.png", dpi=150); plt.close()
            ConfusionMatrixDisplay.from_predictions(yte, p, display_labels=["legit", "phishing"])
            plt.title(f"Random Forest confusion matrix\n{TITLES[exp]}")
            plt.savefig(OUT / f"confusion_{exp}.png", dpi=150); plt.close()
    ngram = make_pipeline(TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                          sublinear_tf=True, max_features=200_000),
                          LogisticRegression(max_iter=2000, C=4))
    ngram.fit(Ttr, ytr)
    p = ngram.predict(Tte)
    rows.append(evaluate("Char n-gram + LR", yte, p, ngram.predict_proba(Tte)[:, 1]))
    res = pd.DataFrame(rows).assign(experiment=exp)
    print(f"\n=== Experiment {exp} ===\n", res.round(4).to_string(index=False))
    return res


def main():
    df = load()
    print(df["phishing"].value_counts().rename({0: "legit", 1: "phishing"}))
    a = run("A_naive_full_url", df["URL"].tolist(), full_url_features, df["phishing"])
    hosts = df.drop_duplicates("host")
    print(f"\nUnique hostnames for experiment B: {len(hosts)}")
    b = run("B_fair_hostname", hosts["host"].tolist(), host_features, hosts["phishing"])
    allres = pd.concat([a, b])
    allres.to_csv(OUT / "metrics.csv", index=False)
    (OUT / "metrics.json").write_text(json.dumps(allres.round(4).to_dict("records"), indent=2))


if __name__ == "__main__":
    main()
