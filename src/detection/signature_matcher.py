"""Step 2: Match AI responses against detection signatures."""
import logging
import re
from typing import Dict, List, Any, Optional
from ..models.perturbation import Question
from ..models.enums import QuestionType

logger = logging.getLogger(__name__)


class SignatureMatcher:
    """Matches AI responses to expected detection signatures."""
    
    # Refusal patterns
    REFUSAL_PATTERNS = [
        r"i cannot",
        r"i'm not able",
        r"i shouldn't",
        r"i can't",
        r"unable to",
        r"not able to",
        r"cannot help",
        r"academic integrity",
        r"cheating",
        r"i'm not sure",
        r"unclear",
        r"i don't",
        r"i won't",
        r"will not",
        r"not solve",
        r"not answer",
        r"refuse",
        r"decline",
        r"cannot answer",
        r"can't answer",
        r"won't answer",
        r"will not answer",
        r"will not solve",
        r"i refuse",
        r"i decline",
        r"cannot provide",
        r"can't provide",
        r"unable to provide",
        r"not appropriate",
        r"not allowed",
        r"against.*policy",
        r"against.*guidelines",
    ]
    
    def __init__(self):
        """Initialize signature matcher."""
        self.refusal_pattern = re.compile(
            "|".join(self.REFUSAL_PATTERNS),
            re.IGNORECASE
        )
    
    def match_response(
        self,
        response_data: Dict[str, Any],
        question: Question
    ) -> Dict[str, Any]:
        """
        Match a single response against detection signatures.
        
        Args:
            response_data: Response data from collector
            question: Original question with perturbations
        
        Returns:
            Dictionary with detection results
        """
        ai_answer = response_data.get("ai_answer")
        gold_answer = response_data.get("gold_answer")
        target_wrong_answer = response_data.get("target_wrong_answer")
        question_type = response_data.get("question_type")
        
        if not ai_answer:
            return {
                "detected": False,
                "refused": True,
                "reason": "No answer provided",
                "match_confidence": 0.0
            }
        
        # Check for refusal
        is_refusal = self._is_refusal(ai_answer)
        if is_refusal:
            return {
                "detected": False,  # Refusal is not a successful detection
                "refused": True,
                "reason": "Model refused to answer",
                "match_confidence": 0.0
            }
        
        # Match based on question type
        if question_type == "MCQ":
            extracted_option = response_data.get("extracted_option")
            detected, confidence, reason = self._match_mcq(ai_answer, gold_answer, target_wrong_answer, question, extracted_option)
        elif question_type == "TF":
            detected, confidence, reason = self._match_tf(ai_answer, gold_answer, target_wrong_answer)
        elif question_type == "LONG":
            detected, confidence, reason = self._match_long_form(ai_answer, gold_answer, target_wrong_answer)
        else:
            detected, confidence, reason = False, 0.0, "Unknown question type"
        
        return {
            "detected": detected,
            "refused": False,
            "reason": reason,
            "match_confidence": confidence,
            "ai_answer": ai_answer,
            "gold_answer": gold_answer,
            "target_wrong_answer": target_wrong_answer
        }
    
    def _is_refusal(self, answer: str) -> bool:
        """Check if answer is a refusal."""
        if not answer:
            return True
        return bool(self.refusal_pattern.search(answer))
    
    def _match_mcq(
        self,
        ai_answer: str,
        gold_answer: str,
        target_wrong_answer: Optional[str],
        question: Question,
        extracted_option: Optional[str] = None
    ) -> tuple:
        """
        Match MCQ response using LLM-extracted option.
        
        Args:
            ai_answer: Full AI answer text
            gold_answer: Gold standard answer
            target_wrong_answer: Target wrong answer option
            question: Question object
            extracted_option: Option letter extracted by LLM judge (A, B, C, D, E)
        
        Returns:
            (detected, confidence, reason)
        """
        # Normalize answers for text-based fallback
        ai_answer_clean = self._normalize_answer(ai_answer)
        gold_answer_clean = self._normalize_answer(gold_answer)
        target_clean = self._normalize_answer(target_wrong_answer) if target_wrong_answer else None
        
        # Use LLM-extracted option if available
        ai_option = extracted_option.upper() if extracted_option else None
        
        # Extract gold and target options (these are usually just single letters)
        gold_option = gold_answer.strip().upper() if gold_answer and len(gold_answer.strip()) == 1 else None
        target_option = target_wrong_answer.strip().upper() if target_wrong_answer and len(target_wrong_answer.strip()) == 1 else None
        
        # If we have LLM-extracted option, use option-based matching
        if ai_option and gold_option:
            # If AI gave correct answer, perturbation failed - not detected
            if ai_option == gold_option:
                return False, 0.0, "AI answer matches gold answer (perturbation not detected)"
            
            # AI gave wrong answer - check if it matches target
            if target_option:
                if ai_option == target_option:
                    return True, 1.0, f"AI selected wrong option {ai_option} (target was {target_option}, gold was {gold_option})"
                else:
                    # Selected a wrong option, but not the target one
                    return True, 0.7, f"AI selected wrong option {ai_option} (target was {target_option}, gold was {gold_option})"
            else:
                # No target specified, but AI gave wrong answer
                return True, 0.7, f"AI selected wrong option {ai_option} (gold was {gold_option})"
        
        # Fallback: text-based matching if option extraction failed
        # Check if answer text matches target wrong answer
        if target_clean and target_clean in ai_answer_clean:
            return True, 0.9, "AI answer contains target wrong answer text"
        
        # Check if answer matches gold (perturbation failed)
        if ai_answer_clean == gold_answer_clean:
            return False, 0.0, "AI answer matches gold answer (perturbation not detected)"
        
        # Answer differs from gold, but couldn't extract options - lower confidence
        return True, 0.5, f"AI answer differs from gold answer"
    
    def _match_tf(
        self,
        ai_answer: str,
        gold_answer: str,
        target_wrong_answer: Optional[str]
    ) -> tuple:
        """Match True/False response."""
        ai_answer_clean = self._normalize_answer(ai_answer)
        gold_answer_clean = self._normalize_answer(gold_answer)
        target_clean = self._normalize_answer(target_wrong_answer) if target_wrong_answer else None
        
        # Extract True/False
        ai_tf = self._extract_true_false(ai_answer_clean)
        gold_tf = self._extract_true_false(gold_answer_clean)
        target_tf = self._extract_true_false(target_clean) if target_clean else None
        
        # Check if flipped
        if ai_tf and target_tf:
            if ai_tf == target_tf:
                return True, 1.0, f"AI answered {ai_tf} (target was {target_tf}, gold was {gold_tf})"
        
        # Check if different from gold
        if ai_tf and gold_tf and ai_tf != gold_tf:
            return True, 0.8, f"AI answered {ai_tf} (gold was {gold_tf})"
        
        return False, 0.0, f"AI answer matches gold answer (perturbation not detected)"
    
    def _match_long_form(
        self,
        ai_answer: str,
        gold_answer: str,
        target_wrong_answer: Optional[str]
    ) -> tuple:
        """Match long-form response."""
        ai_answer_clean = ai_answer.lower()
        gold_answer_clean = gold_answer.lower()
        
        # For long-form, we check for deviation indicators
        # If target_wrong_answer describes the deviation, look for those markers
        if target_wrong_answer:
            target_lower = target_wrong_answer.lower()
            # Check if AI answer shows signs of the described deviation
            deviation_keywords = [
                "different", "focus", "aspect", "concept", "missing", "lacks"
            ]
            has_deviation_keywords = any(kw in target_lower for kw in deviation_keywords)
            
            if has_deviation_keywords:
                # Check if answer is substantially different
                # Simple heuristic: check word overlap
                ai_words = set(ai_answer_clean.split())
                gold_words = set(gold_answer_clean.split())
                overlap = len(ai_words & gold_words) / max(len(ai_words), len(gold_words), 1)
                
                if overlap < 0.5:  # Less than 50% word overlap
                    return True, 0.7, "AI answer shows significant deviation from gold answer"
        
        # Check if answer is very different (low similarity)
        ai_words = set(ai_answer_clean.split())
        gold_words = set(gold_answer_clean.split())
        overlap = len(ai_words & gold_words) / max(len(ai_words), len(gold_words), 1)
        
        if overlap < 0.3:
            return True, 0.6, "AI answer has low similarity to gold answer"
        
        return False, 0.0, "AI answer is similar to gold answer (perturbation not detected)"
    
    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer text for comparison."""
        if not answer:
            return ""
        return answer.strip().lower()
    
    def _extract_true_false(self, text: str) -> Optional[str]:
        """Extract True/False from text."""
        if not text:
            return None
        text_lower = text.lower()
        if re.search(r'\btrue\b', text_lower):
            return "True"
        elif re.search(r'\bfalse\b', text_lower):
            return "False"
        return None

