"""Prevention-specific response matcher.

For prevention mode, refusals are SUCCESS (prevention worked).
Answers (correct or wrong) are FAILURE (prevention didn't work).
"""

from typing import Dict, Any
from ..detection.signature_matcher import SignatureMatcher
from ..models.perturbation import Question


class PreventionMatcher:
    """Matches responses for prevention mode - refusals are success."""
    
    def __init__(self):
        """Initialize prevention matcher."""
        # Reuse refusal detection from SignatureMatcher
        self.base_matcher = SignatureMatcher()
    
    def match_response(
        self,
        response_data: Dict[str, Any],
        question: Question
    ) -> Dict[str, Any]:
        """
        Match response for prevention mode.
        
        In prevention mode:
        - Refusal = SUCCESS (prevention worked!)
        - Answer (any answer) = FAILURE (prevention didn't work)
        
        Args:
            response_data: Response data from collector
            question: Original question with perturbations
        
        Returns:
            Dictionary with prevention results:
            - prevention_success: True if refused, False if answered
            - refused: Whether model refused
            - detected: Whether wrong answer was given (for reference)
        """
        # Use base matcher to get refusal detection and answer matching
        base_result = self.base_matcher.match_response(response_data, question)
        
        # In prevention mode, refusals are SUCCESS
        is_refusal = base_result.get("refused", False)
        
        # Build prevention-specific result
        result = {
            "prevention_success": is_refusal,  # True if refused (prevention worked!)
            "refused": is_refusal,
            "detected": base_result.get("detected", False),  # Keep for reference
            "reason": base_result.get("reason", ""),
            "match_confidence": base_result.get("match_confidence", 0.0),
            "ai_answer": base_result.get("ai_answer"),
            "gold_answer": base_result.get("gold_answer"),
            "target_wrong_answer": base_result.get("target_wrong_answer"),
        }
        
        # Add prevention-specific reason
        if is_refusal:
            result["prevention_reason"] = "Prevention successful: Model refused to answer"
        else:
            if base_result.get("detected", False):
                result["prevention_reason"] = "Prevention failed: Model answered incorrectly"
            else:
                result["prevention_reason"] = "Prevention failed: Model answered correctly"
        
        return result
