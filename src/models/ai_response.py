"""Pydantic models for AI response parsing."""
from pydantic import BaseModel, Field
from typing import List, Optional


class QuestionAnswer(BaseModel):
    """Single question answer from AI."""
    question_number: int = Field(..., description="Question number")
    answer: str = Field(..., description="AI's answer to the question")
    confidence: Optional[str] = Field(None, description="Confidence level if mentioned")
    extracted_option: Optional[str] = Field(
        None, 
        description="For MCQ questions, extract the option letter (A, B, C, D, E) from the answer. For example, if answer is '(b) Metasploit', extract 'B'. If answer is 'A', extract 'A'. Return None for non-MCQ questions or if no option can be determined."
    )
    
    class Config:
        """Pydantic config for structured output."""
        extra = "forbid"  # Required by OpenAI structured output API


class AIResponse(BaseModel):
    """Structured AI response containing all question answers."""
    answers: List[QuestionAnswer] = Field(..., description="List of all question answers")
    
    class Config:
        """Pydantic config for structured output."""
        extra = "forbid"  # Required by OpenAI structured output API

