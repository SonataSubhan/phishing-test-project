"""Demo: classify URLs with the hostname char n-gram model.

Usage: .venv/bin/python src/predict.py <url> [<url> ...]
The model is trained on first run and cached in results/model.joblib.
"""
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

sys.path.insert(0, str(Path(__file__).parent))
from features import hostname_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "results" / "model.joblib"


def get_model():
    if MODEL.exists():
        return joblib.load(MODEL)
    df = pd.read_csv(ROOT / "data/raw/PhiUSIIL_Phishing_URL_Dataset.csv",
                     usecols=["URL", "label"], encoding="utf-8-sig")
    df["host"] = df["URL"].map(hostname_of)
    df = df.drop_duplicates("host")
    model = make_pipeline(TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3,
                                          sublinear_tf=True, max_features=200_000),
                          LogisticRegression(max_iter=2000, C=4))
    model.fit(df["host"], 1 - df["label"])
    MODEL.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL)
    return model


def main(urls):
    model = get_model()
    for url in urls:
        p = model.predict_proba([hostname_of(url)])[0, 1]
        verdict = "PHISHING" if p >= 0.5 else "legit"
        print(f"{verdict:9} {p:6.1%}  {url}")


def interactive():
    model = get_model()
    print("Link yaz və Enter bas (çıxmaq üçün boş Enter):")
    while True:
        try:
            url = input("> ").strip()
        except EOFError:
            break
        if not url:
            break
        p = model.predict_proba([hostname_of(url)])[0, 1]
        print(f"  {'PHISHING' if p >= 0.5 else 'legit'}  {p:.1%}")


if __name__ == "__main__":
    if sys.argv[1:]:
        main(sys.argv[1:])
    else:
        interactive()
