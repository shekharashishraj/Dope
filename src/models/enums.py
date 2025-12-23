"""Enums for type safety."""
from enum import Enum


class QuestionType(str, Enum):
    """Question type enumeration."""
    MCQ = "MCQ"
    TF = "TF"
    LONG = "LONG"

