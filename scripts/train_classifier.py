"""
EvidenceRAG Machine Learning Model Training & Evaluation Script
Allows training and evaluating a TF-IDF + Logistic Regression Document Classifier
when a user-provided labeled dataset is supplied.
Computes Accuracy, Precision, Recall, F1-score, and Confusion Matrix.
"""

import sys
import os
import json
import argparse
from pathlib import Path
import joblib
import numpy as np

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

from backend.app.services.ocr.processor import process_document_ocr
from backend.app.core.config import settings

def train_and_evaluate(dataset_json: Path, docs_dir: Path):
    print("=" * 60)
    print("EvidenceRAG: Document Classifier Training & Evaluation")
    print("=" * 60)

    if not dataset_json.exists():
        print(f"\n[INFO] Labeled dataset file not found at: {dataset_json}")
        print("\nHow to add an optional user-provided labeled dataset:")
        print("1. Prepare a JSON file with mapping: {'doc_name.pdf': {'category': 'Income Certificate'}}")
        print("2. Place certificate files in a directory.")
        print("3. Run: python scripts/train_classifier.py --dataset-json <path.json> --docs-dir <path/to/docs>")
        print("\nCurrent Status: Using pre-trained classifier with configurable heuristic fallback.")
        return

    with open(dataset_json, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print(f"Found {len(ground_truth)} ground-truth records in dataset.")

    texts = []
    labels = []

    print("Extracting OCR text from dataset samples...")
    for key, item in ground_truth.items():
        filename = item.get("filename", key)
        category = item.get("category")
        if not category:
            continue

        # Look in docs_dir
        file_path = docs_dir / filename
        if not file_path.exists():
            # Try recursive search in docs_dir
            candidates = list(docs_dir.glob(f"**/{filename}"))
            if candidates:
                file_path = candidates[0]
            else:
                continue

        mime = "application/pdf" if file_path.suffix.lower() == ".pdf" else "image/png"
        try:
            ocr_out = process_document_ocr(str(file_path), mime)
            text = ocr_out.get("full_text", "").strip()
            if len(text) > 15:
                texts.append(text)
                labels.append(category)
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    print(f"Successfully extracted {len(texts)} usable labeled samples across {len(set(labels))} classes.")
    if len(texts) < 10 or len(set(labels)) < 2:
        print("Insufficient samples to train a generalized machine learning classifier. Minimum 10 samples required.")
        return

    # Train / test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels if len(set(labels)) <= len(texts) // 3 else None
    )

    print(f"Train split: {len(X_train)} samples | Test split: {len(X_test)} samples")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=3000, sublinear_tf=True)),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=500, solver="lbfgs"))
    ])

    print("Training Document Classification Model...")
    pipeline.fit(X_train, y_train)

    # Evaluation
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=pipeline.classes_)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    report_text = classification_report(y_test, y_pred, zero_division=0)

    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("-" * 50)
    print(report_text)
    print(f"Overall Accuracy:   {acc * 100:.2f}%")
    print(f"Weighted Precision: {prec * 100:.2f}%")
    print(f"Weighted Recall:    {rec * 100:.2f}%")
    print(f"Weighted F1-Score:  {f1 * 100:.2f}%")
    print("-" * 50)

    # Persist model
    model_save_path = settings.MODELS_DIR / "document_classifier.joblib"
    joblib.dump(pipeline, str(model_save_path))
    print(f"Trained model saved to: {model_save_path}")

    # Save evaluation metrics json
    metrics = {
        "dataset_size": len(texts),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "classes": list(pipeline.classes_),
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }

    metrics_save_path = settings.MODELS_DIR / "evaluation_metrics.json"
    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Evaluation metrics recorded at: {metrics_save_path}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EvidenceRAG Document Classifier Trainer")
    parser.add_argument("--dataset-json", default="labels.json", help="Path to ground-truth labels JSON")
    parser.add_argument("--docs-dir", default="documents", help="Path to document files directory")
    args = parser.parse_args()

    train_and_evaluate(Path(args.dataset_json), Path(args.docs_dir))
