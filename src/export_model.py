"""Export the trained char n-gram model to JSON so the website can run it in the browser.

Usage: .venv/bin/python src/export_model.py
Writes web/model.json and checks a few hostnames against the Python model.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predict import get_model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "model.json"

model = get_model()
vec = model.named_steps["tfidfvectorizer"]
clf = model.named_steps["logisticregression"]

grams = vec.get_feature_names_out()
data = {
    "ngram_range": list(vec.ngram_range),
    "intercept": round(float(clf.intercept_[0]), 6),
    # ngram -> [idf, weight]
    "vocab": {g: [round(float(i), 4), round(float(w), 4)]
              for g, i, w in zip(grams, vec.idf_, clf.coef_[0])},
}
OUT.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {len(grams)} n-grams)")

samples = ["kapitalbank.az", "kapitalbank-az-onlayn-giris.top", "google.com",
           "microsoft-365-auth-login.firebaseapp.com", "prosol.az"]
for host, p in zip(samples, model.predict_proba(samples)[:, 1]):
    print(f"{p:.4f}  {host}")
