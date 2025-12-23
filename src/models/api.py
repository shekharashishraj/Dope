"""API response models."""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class BatchStatus(BaseModel):
    """Batch API status model."""
    id: str
    status: str
    request_counts: Dict[str, Optional[int]] = {}
    output_file_id: Optional[str] = None
    error_file_id: Optional[str] = None


class BatchRequest(BaseModel):
    """Batch API request model."""
    custom_id: str
    method: str
    url: str
    body: Dict[str, Any]

