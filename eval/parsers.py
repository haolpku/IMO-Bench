"""
Parsers for extracting grades/scores from autograder model outputs.
"""

import re

# Score mappings between labels and IMO 0-7 point scale
GRADE_TO_POINTS = {"correct": 7, "almost": 6, "partial": 1, "incorrect": 0}
POINTS_TO_GRADE = {
    7: "correct", 6: "almost", 5: "almost", 4: "almost",
    3: "partial", 2: "partial", 1: "partial", 0: "incorrect",
}


def parse_answer_grade(text: str) -> str:
    """Extract Correct/Incorrect from AnswerAutoGrader output."""
    match = re.search(r"\\boxed\{(Correct|Incorrect)\}", text, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    if "boxed{correct}" in text.lower():
        return "Correct"
    if "boxed{incorrect}" in text.lower():
        return "Incorrect"
    last = text.strip().split("\n")[-1].lower()
    if "correct" in last and "incorrect" not in last:
        return "Correct"
    return "Incorrect"


def parse_proof_score(text: str) -> int:
    """Extract N from <points>N out of 7</points>."""
    match = re.search(r"<points>\s*(\d)\s*out of 7\s*</points>", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d)\s*out of 7", text)
    if match:
        return int(match.group(1))
    return 0


def parse_grading_label(text: str) -> str:
    """Extract the classification label from GradingBench model output."""
    last_line = text.strip().split("\n")[-1].strip().lower()
    for label in ["incorrect", "correct", "almost", "partial"]:
        if label in last_line:
            return label
    for label in ["incorrect", "correct", "almost", "partial"]:
        if label in text.lower():
            return label
    return "incorrect"
