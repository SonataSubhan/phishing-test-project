# Phishing URL Detection

Artificial Intelligence course project
Subhan Huseynov, B.01.509.22.020

A machine learning model that predicts whether a link is a phishing site using only the URL text,
without opening the page. The repository contains the experiments (Python) and a static website
where the trained model runs in the browser, together with the project presentation.

## Website

- `web/index.html`: URL checker
- `web/slides.html`: presentation (arrow keys to navigate, F for fullscreen)

Run locally:

```bash
cd web
python3 -m http.server 8000
# open http://localhost:8000
```

Deploy on Vercel: import the repository, no settings needed (`vercel.json` serves the `web` folder).

## Experiments

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# dataset (PhiUSIIL, UCI id 967)
mkdir -p data/raw
curl -L -o data/raw/phiusiil.zip "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip"
unzip data/raw/phiusiil.zip -d data/raw

.venv/bin/python src/train.py          # experiments A and B, writes results/
.venv/bin/python src/predict.py        # interactive command line demo
.venv/bin/python src/export_model.py   # writes web/model.json for the website
```

## Dataset

PhiUSIIL (Prasad & Chandra, 2024): 235,795 URLs, 134,850 legitimate and 100,945 phishing.
In the original file `label = 1` means legitimate; the code uses `phishing = 1 - label`.

Every legitimate URL in the dataset has the form `https://www.<domain>` with no path, while only
2.4% of phishing URLs start with `https://www.` and about 60% have a path. A model trained on raw
URLs can learn this format instead of real phishing signs, so two experiments were run:

- **A (naive):** full URLs, 21 lexical features and character n-grams
- **B (fair):** hostname only (scheme, port, path and `www.` removed), duplicates removed,
  219,094 unique hostnames, 13 lexical features and character n-grams

80/20 stratified split, random_state 42.

## Results

| Experiment | Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| A | Logistic Regression | 0.998 | 1.000 | 0.996 | 0.998 | 0.999 |
| A | Random Forest | 0.998 | 0.999 | 0.996 | 0.998 | 0.998 |
| A | Char n-gram + LR | 0.997 | 1.000 | 0.993 | 0.997 | 0.999 |
| B | Logistic Regression | 0.837 | 0.891 | 0.656 | 0.756 | 0.840 |
| B | Random Forest | 0.845 | 0.892 | 0.678 | 0.770 | 0.849 |
| B | Char n-gram + LR | **0.880** | **0.918** | **0.755** | **0.828** | **0.923** |

- The ~99.8% in experiment A comes from the format difference, not from learning phishing.
- On hostnames only, the character n-gram model is the best.
- Recall is lower than precision because many phishing pages are hosted on legitimate platforms
  (`docs.google.com`, `sites.google.com`, `firebaseapp.com`, IPFS gateways). The dataset has 922
  phishing URLs on Google hosts, so a hostname-only model cannot separate them.

## Structure

```
src/features.py       feature extraction
src/train.py          experiments, metrics and plots
src/predict.py        command line demo
src/export_model.py   exports the n-gram model to web/model.json
results/              metrics.csv, plots
web/                  website (checker + presentation)
```
