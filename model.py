"""Machine-learning part of RESQ-AI.

Two small text classifiers, both TF-IDF + Logistic Regression (scikit-learn):
  * type model      -> Accident / Fire / Medical / Traffic / Infrastructure / Other
  * severity model  -> Critical / High / Medium / Low   (a "second opinion" that
                       feeds the confidence score; the explainable priority
                       engine makes the final decision)

TF-IDF uses word pairs AND character n-grams, so spelling mistakes and Hinglish
spellings ("dhuan", "dhuaan") still get matched.

Training takes about a second, so the models are re-trained every time the
server starts. There is no model file to lose or to break between versions.
"""
from __future__ import annotations

import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


def _clean(text: str) -> str:
    text = str(text).lower()
    return re.sub(r"\d+", " num ", text)


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("words", TfidfVectorizer(preprocessor=_clean, ngram_range=(1, 2), sublinear_tf=True)),
        ("chars", TfidfVectorizer(preprocessor=_clean, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    return Pipeline([("tfidf", features), ("clf", LogisticRegression(C=12, max_iter=3000))])


class Brain:
    """Holds the two trained models."""

    def __init__(self, csv_path=None, df=None):
        if df is None:
            df = pd.read_csv(csv_path)
        self.df = df.dropna(subset=["report", "type", "priority"]).reset_index(drop=True)
        self.type_model = build_pipeline().fit(self.df["report"], self.df["type"])
        self.sev_model = build_pipeline().fit(self.df["report"], self.df["priority"])

    @staticmethod
    def _probs(model, text):
        p = model.predict_proba([text])[0]
        return {c: float(v) for c, v in zip(model.classes_, p)}

    def type_probs(self, text):
        return self._probs(self.type_model, text)

    def severity_probs(self, text):
        return self._probs(self.sev_model, text)
