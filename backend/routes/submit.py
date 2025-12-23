"""
Submit exam endpoint.
Handles POST requests for exam submissions.
"""

from fastapi import APIRouter, HTTPException, status
from backend.models import SubmitExamRequest, SubmitExamResponse
from backend.services.answer_service import save_answer_submission
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/submit_exam", response_model=SubmitExamResponse, status_code=status.HTTP_200_OK)
async def submit_exam(payload: SubmitExamRequest):
    """
    Submit exam answers.
    
    Args:
        payload: Exam submission payload (validated by Pydantic)
        
    Returns:
        SubmitExamResponse with status and message
        
    Raises:
        HTTPException: On validation errors, duplicate attempts, or filesystem errors
    """
    attempt_id = payload.attempt.attempt_id
    logger.info("=" * 80)
    logger.info(f"Received submission request for attempt_id: {attempt_id}")
    logger.info(f"Subject: {payload.attempt.subject}")
    logger.info(f"Number of responses: {len(payload.responses)}")
    logger.info(f"Is complete: {payload.validation.is_complete}")
    
    # Save submission
    success, message, error_code = save_answer_submission(payload)
    
    if not success:
        logger.error(f"Failed to save submission: {message}")
        
        if error_code == 'duplicate_attempt':
            logger.warning(f"Duplicate attempt detected: {attempt_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "message": f"Attempt {attempt_id} already exists",
                    "error_code": "duplicate_attempt"
                }
            )
        elif error_code in ['invalid_subject', 'invalid_attempt_id']:
            logger.error(f"Validation error: {message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "error",
                    "message": message,
                    "error_code": error_code
                }
            )
        else:
            # Filesystem or other error
            logger.error(f"Filesystem error: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Failed to save submission. Please try again.",
                    "error_code": "filesystem_error"
                }
            )
    
    logger.info(f"Submission saved successfully for attempt_id: {attempt_id}")
    logger.info("=" * 80)
    
    return SubmitExamResponse(
        status="success",
        message="Exam submitted successfully",
        attempt_id=attempt_id
    )

