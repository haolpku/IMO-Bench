"""
Data loaders for IMO-Bench CSV datasets.
"""

import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "imobench")


def load_answerbench() -> list[dict]:
    """Load IMO-AnswerBench (v2) — 400 short-answer problems."""
    path = os.path.join(DATA_DIR, "answerbench_v2.csv")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_proofbench() -> list[dict]:
    """Load IMO-ProofBench — 60 proof-based problems."""
    path = os.path.join(DATA_DIR, "proofbench.csv")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_gradingbench() -> list[dict]:
    """Load IMO-GradingBench — 1000 human-graded solutions."""
    path = os.path.join(DATA_DIR, "gradingbench.csv")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
