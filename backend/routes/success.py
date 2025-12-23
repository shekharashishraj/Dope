"""
Success page route.
Renders the success page after exam submission.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Get templates directory
backend_dir = Path(__file__).parent.parent
templates_dir = backend_dir / "templates"


@router.get("/success", response_class=HTMLResponse)
async def success_page():
    """
    Render the success page after exam submission.
    
    Returns:
        HTMLResponse with success page
    """
    logger.info("Success page accessed")
    
    # Read the success.html template directly
    success_html_path = templates_dir / "success.html"
    
    try:
        with open(success_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        logger.info("Success page rendered successfully")
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering success page: {e}", exc_info=True)
        return HTMLResponse(
            content="<h1>Success</h1><p>Exam submitted successfully.</p>",
            status_code=200
        )

