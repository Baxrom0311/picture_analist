"""
Prompt templates for LLM evaluation.
"""

# Version tracking for prompts
PROMPT_VERSION = '1.0'

# Grade thresholds
GRADE_THRESHOLDS = {
    'A': 90,
    'B': 80,
    'C': 70,
    'D': 60,
}


def get_grade(score):
    """Get letter grade from numeric score."""
    score = float(score)
    for grade, min_score in GRADE_THRESHOLDS.items():
        if score >= min_score:
            return grade
    return 'F'
