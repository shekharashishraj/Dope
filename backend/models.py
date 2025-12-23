"""
Pydantic models for request/response validation.
Matches the JSON schema for exam submissions.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AttemptModel(BaseModel):
    """Attempt metadata model."""
    attempt_id: str = Field(..., description="UUID v4 for the attempt")
    subject: str = Field(..., description="Subject name (e.g., 'Mathematics', 'Science')")
    exam_id: str = Field(..., description="Exam identifier")
    education_level: str = Field(..., description="Education level (e.g., 'K-12')")
    started_at: str = Field(..., description="ISO-8601 timestamp when exam started")
    submitted_at: str = Field(..., description="ISO-8601 timestamp when exam submitted")
    duration_sec: int = Field(..., description="Duration in seconds")


class ClientModel(BaseModel):
    """Client information model."""
    user_agent: str = Field(..., description="Browser user agent string")
    timezone: str = Field(..., description="Timezone (e.g., 'America/New_York')")
    locale: str = Field(..., description="Locale (e.g., 'en-US')")


class UserModel(BaseModel):
    """User information model."""
    user_id: str = Field(default="anonymous", description="User identifier")
    session_id: str = Field(..., description="Browser session ID")
    client: ClientModel = Field(..., description="Client information")


class MCQResponseModel(BaseModel):
    """MCQ response model."""
    selected_option_id: str = Field(..., description="Selected option ID (e.g., 'A', 'B')")


class BooleanResponseModel(BaseModel):
    """True/False response model."""
    value: bool = Field(..., description="Boolean value (true or false)")


class TextResponseModel(BaseModel):
    """Long form text response model."""
    text: str = Field(..., description="Student's text answer")


class QuestionResponseModel(BaseModel):
    """Question response model - can be one of three types."""
    question_id: str = Field(..., description="Question identifier (e.g., 'mcq_q1')")
    section: str = Field(..., description="Section name (e.g., 'multiple_choice')")
    type: str = Field(..., description="Question type (e.g., 'mcq_single', 'boolean', 'text')")
    marks: int = Field(..., description="Marks allocated for this question")
    response: Union[MCQResponseModel, BooleanResponseModel, TextResponseModel] = Field(
        ..., 
        description="Response data (varies by question type)"
    )


class ValidationModel(BaseModel):
    """Validation information model."""
    is_complete: bool = Field(..., description="Whether all questions are answered")
    unanswered_question_ids: List[str] = Field(default_factory=list, description="List of unanswered question IDs")


class IntegrityShieldModel(BaseModel):
    """Integrity shield metadata model."""
    attack_variant: str = Field(..., description="Attack variant identifier")
    render_parse_gap_enabled: bool = Field(..., description="Whether render-parse gap is enabled")


class SubmitExamRequest(BaseModel):
    """Main request model for exam submission."""
    schema_version: str = Field(..., description="Schema version (e.g., '1.0')")
    attempt: AttemptModel = Field(..., description="Attempt metadata")
    user: UserModel = Field(..., description="User information")
    responses: List[QuestionResponseModel] = Field(..., description="List of question responses")
    validation: ValidationModel = Field(..., description="Validation information")
    integrityshield: IntegrityShieldModel = Field(..., description="Integrity shield metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "attempt": {
                    "attempt_id": "123e4567-e89b-12d3-a456-426614174000",
                    "subject": "Mathematics",
                    "exam_id": "math_k12_assessment_1",
                    "education_level": "K-12",
                    "started_at": "2024-01-01T10:00:00Z",
                    "submitted_at": "2024-01-01T11:00:00Z",
                    "duration_sec": 3600
                },
                "user": {
                    "user_id": "anonymous",
                    "session_id": "session-123",
                    "client": {
                        "user_agent": "Mozilla/5.0...",
                        "timezone": "America/New_York",
                        "locale": "en-US"
                    }
                },
                "responses": [
                    {
                        "question_id": "mcq_q1",
                        "section": "multiple_choice",
                        "type": "mcq_single",
                        "marks": 2,
                        "response": {
                            "selected_option_id": "A"
                        }
                    }
                ],
                "validation": {
                    "is_complete": True,
                    "unanswered_question_ids": []
                },
                "integrityshield": {
                    "attack_variant": "baseline",
                    "render_parse_gap_enabled": True
                }
            }
        }


class SubmitExamResponse(BaseModel):
    """Response model for exam submission."""
    status: str = Field(..., description="Status of submission ('success' or 'error')")
    message: str = Field(..., description="Human-readable message")
    attempt_id: Optional[str] = Field(None, description="Attempt ID if successful")

