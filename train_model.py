import os
import json
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import dump

# -------------------------
# Config
# -------------------------
DATA_PATH = "off_sample_10k.csv"   # input file you created earlier
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Define the allergen categories we care about
TARGET_ALLERGENS = [
    "milk",
    "egg",
    "peanut",
    "tree_nut",   # group of nuts
    "soy",
    "wheat",
    "gluten",
    "sesame",
    "fish",
    "shellfish",
    "mustard",
]


# -------------------------
# Helper functions
# -------------------------

def clean_text(text: str) -> str:
    """Simple cleaning: lower, remove weird chars, normalize spaces."""
    if not isinstance(text, str):
        return ""
    s = text.lower()
    s = re.sub(r"[^a-z0-9,;()\-/%\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_allergens_field(raw_allergens: str):
    """
    OFF 'allergens_tags' field often looks like:
    'en:milk,en:nuts,en:gluten'
    We'll turn it into ['milk', 'tree_nut', 'gluten'] etc.
    """
    labels = set()
    if not isinstance(raw_allergens, str):
        return []

    for token in raw_allergens.split(","):
        token = token.strip().lower()
        if not token:
            continue
        # Drop language prefix like 'en:milk'
        if ":" in token:
            token = token.split(":")[-1]

        # Map nuts → tree_nut (rough grouping)
        if token in ["nuts", "hazelnut", "walnut", "almond", "pecan", "cashew"]:
            labels.add("tree_nut")
        elif token in TARGET_ALLERGENS:
            labels.add(token)

    return list(labels)


def keyword_fallback(text: str):
    """
    If allergens field is missing/empty, infer labels from ingredient keywords.
    Very rough, but helps get more labels.
    """
    text = text.lower()
    labels = set()

    # simple keyword rules
    if any(k in text for k in ["milk", "lactose", "casein", "whey"]):
        labels.add("milk")
    if any(k in text for k in ["egg", "albumen", "albumin"]):
        labels.add("egg")
    if "peanut" in text or "groundnut" in text:
        labels.add("peanut")
    if any(k in text for k in ["almond", "hazelnut", "walnut", "cashew", "pistachio", "pecan", "macadamia"]):
        labels.add("tree_nut")
    if any(k in text for k in ["soy", "soya", "soybean"]):
        labels.add("soy")
    if any(k in text for k in ["wheat", "durum", "semolina"]):
        labels.add("wheat")
    if "gluten" in text:
        labels.add("gluten")
    if "sesame" in text:
        labels.add("sesame")
    if any(k in text for k in ["fish", "salmon", "tuna", "cod", "anchovy"]):
        labels.add("fish")
    if any(k in text for k in ["shrimp", "prawn", "crab", "lobster", "mussel", "clam"]):
        labels.add("shellfish")
    if "mustard" in text:
        labels.add("mustard")

    return list(labels)


def build_labels(row):
    """
    Combine OFF allergens field + keyword fallback
    """
    labels_from_allergens = parse_allergens_field(row.get("allergens", ""))
    labels_from_text = keyword_fallback(row.get("ingredients_text", ""))

    labels = set(labels_from_allergens) | set(labels_from_text)
    return list(labels)


# -------------------------
# Main training pipeline
# -------------------------

def main():
    print(f"Loading data from {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)

    # Ensure columns exist / rename if needed
    # If your CSV had 'allergens_tags' instead of 'allergens', rename it:
    if "allergens" not in df.columns and "allergens_tags" in df.columns:
        df = df.rename(columns={"allergens_tags": "allergens"})

    # Keep only rows with ingredients_text not null
    df = df[df["ingredients_text"].notnull()].copy()
    print(f"Rows with ingredients_text: {len(df)}")

    # Clean text
    print("Cleaning ingredient text...")
    df["clean_text"] = df["ingredients_text"].apply(clean_text)

    # Build labels
    print("Building multi-label targets...")
    df["labels_list"] = df.apply(build_labels, axis=1)

    # You can inspect how many have at least 1 allergen
    df["has_label"] = df["labels_list"].apply(lambda x: len(x) > 0)
    print("Rows with at least one allergen label:", df["has_label"].sum())

    # Use all rows (including no-label) for training; no-label rows act as negatives.
    X = df["clean_text"].values
    y_list = df["labels_list"].values

    # Multi-label binarization
    mlb = MultiLabelBinarizer(classes=TARGET_ALLERGENS)
    Y = mlb.fit_transform(y_list)

    # Train/val split
    X_train, X_val, Y_train, Y_val = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )

    # Text vectorizer
    print("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),  # unigrams + bigrams
        min_df=2
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)

    # Classifier: One-vs-Rest Logistic Regression
    print("Training classifier...")
    base_clf = LogisticRegression(max_iter=200, n_jobs=-1)
    clf = OneVsRestClassifier(base_clf)

    clf.fit(X_train_vec, Y_train)

    # Evaluate
    print("Evaluating on validation set...")
    Y_pred = clf.predict(X_val_vec)
    print(classification_report(Y_val, Y_pred, target_names=mlb.classes_))

    # Save artifacts
    print("Saving model artifacts...")
    dump(vectorizer, os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
    dump(clf, os.path.join(MODELS_DIR, "allergen_classifier.joblib"))
    dump(mlb, os.path.join(MODELS_DIR, "label_binarizer.joblib"))

    print("Done. Models saved in 'models/' folder.")


if __name__ == "__main__":
    main()
