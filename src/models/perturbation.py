"""Perturbation and question data models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from .enums import QuestionType


class APIMetadata(BaseModel):
    """Metadata from OpenAI API response."""
    response_id: Optional[str] = Field(None, description="Unique response ID")
    model: Optional[str] = Field(None, description="Model version used")
    system_fingerprint: Optional[str] = Field(None, description="Model system fingerprint")
    created: Optional[int] = Field(None, description="Response creation timestamp")
    finish_reason: Optional[str] = Field(None, description="Why generation stopped (stop, length, content_filter)")
    prompt_tokens: Optional[int] = Field(None, description="Number of prompt tokens")
    completion_tokens: Optional[int] = Field(None, description="Number of completion tokens")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    cached_tokens: Optional[int] = Field(None, description="Number of cached tokens (if caching enabled)")
    prompt_tokens_by_role: Optional[Dict[str, int]] = Field(None, description="Token breakdown by role")
    
    class Config:
        """Pydantic config."""
        extra = "allow"


class PerturbationMapping(BaseModel):
    """Perturbation mapping model with validation."""
    question_index: int = Field(..., gt=0, description="Question number")
    latex_stem_text: str = Field(..., min_length=1, description="LaTeX question stem")
    original_substring: str = Field(..., min_length=1, description="Substring to replace")
    replacement_substring: str = Field(..., min_length=1, description="Replacement text")
    start_pos: int = Field(..., ge=0, description="Start position (0-based)")
    end_pos: int = Field(..., gt=0, description="End position (exclusive)")
    target_wrong_answer: Optional[str] = Field(None, description="Target wrong answer")
    reasoning: Optional[str] = Field(None, description="Reasoning for perturbation")
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities from API response")
    api_metadata: Optional[APIMetadata] = Field(None, description="API response metadata")
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for backward compatibility


# Separate models for structured output (require extra="forbid")
# These are used only for OpenAI structured output API
class PerturbationMappingStructured(BaseModel):
    """Perturbation mapping model for structured output (strict schema)."""
    question_index: int = Field(..., gt=0, description="Question number")
    latex_stem_text: str = Field(..., min_length=1, description="LaTeX question stem")
    original_substring: str = Field(..., min_length=1, description="Substring to replace")
    replacement_substring: str = Field(..., min_length=1, description="Replacement text")
    start_pos: int = Field(..., ge=0, description="Start position (0-based)")
    end_pos: int = Field(..., gt=0, description="End position (exclusive)")
    target_wrong_answer: Optional[str] = Field(None, description="Target wrong answer")
    reasoning: Optional[str] = Field(None, description="Reasoning for perturbation")
    
    class Config:
        """Pydantic config for structured output - must forbid extra properties."""
        extra = "forbid"  # Required by OpenAI structured output API


class PerturbationListResponse(BaseModel):
    """Response model for structured output containing a list of perturbations."""
    perturbations: List[PerturbationMappingStructured] = Field(..., description="List of perturbation mappings")
    
    class Config:
        """Pydantic config for structured output - must forbid extra properties."""
        extra = "forbid"  # Required by OpenAI structured output API


class Question(BaseModel):
    """Question model."""
    question_number: int = Field(..., gt=0)
    question_type: QuestionType
    stem_text: str
    options: Optional[Dict[str, str]] = None
    gold_answer: str
    perturbations: List[PerturbationMapping] = Field(default_factory=list)
    latex_stem_text: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for backward compatibility


class FilePaths(BaseModel):
    """File paths model."""
    latex_file: Optional[str] = None
    pdf_file: Optional[str] = None
    layout_json: Optional[str] = None
    page_images: Optional[List[str]] = None
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for backward compatibility


class Document(BaseModel):
    """Document model."""
    docid: str
    domain: Optional[str] = None
    academic_level: Optional[str] = None
    questions: List[Question]
    file_paths: Optional[FilePaths] = None
    # Optional layout and image fields for reconstruction (Option A)
    title_text: Optional[str] = None
    subtitle_text: Optional[str] = None
    section_title: Optional[str] = None
    instructions_text: Optional[str] = None
    geometry: Optional[str] = None
    document_class_options: Optional[str] = None
    enumerate_label: Optional[str] = None
    logo_path: Optional[str] = None
    logo_width: Optional[str] = None
    logo_position: Optional[str] = None  # e.g. "top_center", "top_left"

    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for backward compatibility

