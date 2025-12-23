"""Pydantic models for AI response parsing."""
from pydantic import BaseModel, Field
from typing import List, Optional


class QuestionAnswer(BaseModel):
    """Single question answer from AI."""
    question_number: int = Field(..., description="Question number")
    answer: str = Field(..., description="AI's answer to the question")
    confidence: Optional[str] = Field(None, description="Confidence level if mentioned")


class AIResponse(BaseModel):
    """Structured AI response containing all question answers."""
    answers: List[QuestionAnswer] = Field(..., description="List of all question answers")

