"""Stage 4: Deterministic Validation - Code-based validation and index computation.

This module handles all mechanical validation without LLM calls:
- Find substring position
- Compute start_pos and end_pos
- Validate all hard constraints
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error with error code and details."""
    
    SUBSTRING_NOT_FOUND = "substring_not_found"
    SUBSTRING_NOT_UNIQUE = "substring_not_unique"
    REPLACEMENT_TOO_LONG = "replacement_too_long"
    EMPTY_STRING = "empty_string"
    IDENTICAL_STRINGS = "identical_strings"
    NEGATION_DETECTED = "negation_detected"
    LATEX_MALFORMED = "latex_malformed"


def validate_mapping(
    latex_stem_text: str,
    original_substring: str,
    replacement_substring: str,
    question_type: str,
    strict_length: bool = True,
) -> Dict[str, Any]:
    """
    Validate a mapping and compute indices.
    
    This function performs all Stage 4 validation:
    1. Find original_substring in stem
    2. Check uniqueness
    3. Compute end_pos
    4. Check length constraint
    5. Check non-empty
    6. Check different strings
    7. Check for prohibited negation patterns
    
    Args:
        latex_stem_text: The original question stem
        original_substring: The substring to replace
        replacement_substring: The replacement text
        question_type: "TF" or "MCQ"
        strict_length: If True, enforce len(replacement) <= len(original) for MCQ
    
    Returns:
        Dictionary with:
        - valid: bool
        - error: str (error code if invalid)
        - error_details: str (human-readable error message)
        - start_pos: int (if valid)
        - end_pos: int (if valid)
    """
    # 1. Check for empty strings
    if not original_substring or not original_substring.strip():
        return {
            "valid": False,
            "error": ValidationError.EMPTY_STRING,
            "error_details": "original_substring is empty or whitespace-only"
        }
    
    if not replacement_substring or not replacement_substring.strip():
        return {
            "valid": False,
            "error": ValidationError.EMPTY_STRING,
            "error_details": "replacement_substring is empty or whitespace-only"
        }
    
    # 2. Check for identical strings
    if original_substring == replacement_substring:
        return {
            "valid": False,
            "error": ValidationError.IDENTICAL_STRINGS,
            "error_details": "replacement_substring is identical to original_substring"
        }
    
    # 3. Find original_substring in stem
    start_pos = latex_stem_text.find(original_substring)
    if start_pos == -1:
        return {
            "valid": False,
            "error": ValidationError.SUBSTRING_NOT_FOUND,
            "error_details": f"original_substring '{original_substring[:50]}...' not found verbatim in stem"
        }
    
    # 4. Check uniqueness
    count = latex_stem_text.count(original_substring)
    if count > 1:
        return {
            "valid": False,
            "error": ValidationError.SUBSTRING_NOT_UNIQUE,
            "error_details": f"original_substring appears {count} times in stem (must be unique)"
        }
    
    # 5. Compute end_pos
    end_pos = start_pos + len(original_substring)
    
    # 6. Length constraint (MCQ strict, TF flexible)
    if question_type.upper() == "MCQ" and strict_length:
        if len(replacement_substring) > len(original_substring):
            return {
                "valid": False,
                "error": ValidationError.REPLACEMENT_TOO_LONG,
                "error_details": f"replacement ({len(replacement_substring)} chars) longer than original ({len(original_substring)} chars)"
            }
    
    # 7. Check for prohibited negation patterns in replacement
    negation_patterns = [
        r"\bnot\b",
        r"\bnever\b", 
        r"\bno\b",
        r"\bcannot\b",
        r"\bcan't\b",
        r"\bwon't\b",
        r"\bdon't\b",
        r"\bdoesn't\b",
        r"\bisn't\b",
        r"\baren't\b",
        r"\bwasn't\b",
        r"\bweren't\b",
    ]
    
    # Check if negation was ADDED (not present in original but present in replacement)
    replacement_lower = replacement_substring.lower()
    original_lower = original_substring.lower()
    
    for pattern in negation_patterns:
        if re.search(pattern, replacement_lower) and not re.search(pattern, original_lower):
            return {
                "valid": False,
                "error": ValidationError.NEGATION_DETECTED,
                "error_details": f"Prohibited negation pattern detected in replacement: {pattern}"
            }
    
    # Check for negation prefixes added
    negation_prefixes = ["un", "non", "in", "im", "ir", "dis"]
    # Simple heuristic: if replacement starts with negation prefix and original doesn't
    for prefix in negation_prefixes:
        if replacement_lower.startswith(prefix) and not original_lower.startswith(prefix):
            # Check if it's actually a negation (not words like "under", "into", etc.)
            if len(replacement_lower) > len(prefix) + 2:
                # Look for common negation patterns
                if replacement_lower.startswith(prefix + original_lower[:3]):
                    return {
                        "valid": False,
                        "error": ValidationError.NEGATION_DETECTED,
                        "error_details": f"Prohibited negation prefix '{prefix}' added to replacement"
                    }
    
    # 8. Basic LaTeX validation (check for unbalanced braces)
    if not _check_latex_balanced(replacement_substring):
        logger.warning(f"Potentially malformed LaTeX in replacement: {replacement_substring[:50]}...")
        # Don't fail on this, just warn - LaTeX validation is tricky
    
    # All checks passed
    return {
        "valid": True,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "original_length": len(original_substring),
        "replacement_length": len(replacement_substring),
    }


def _check_latex_balanced(text: str) -> bool:
    """Check if LaTeX braces are balanced.
    
    Args:
        text: Text to check
    
    Returns:
        True if braces are balanced
    """
    count = 0
    for char in text:
        if char == '{':
            count += 1
        elif char == '}':
            count -= 1
            if count < 0:
                return False
    return count == 0


def apply_replacement(
    latex_stem_text: str,
    original_substring: str,
    replacement_substring: str,
) -> str:
    """
    Apply the replacement to create the perturbed stem.
    
    Args:
        latex_stem_text: The original question stem
        original_substring: The substring to replace
        replacement_substring: The replacement text
    
    Returns:
        The perturbed stem with the replacement applied
    """
    return latex_stem_text.replace(original_substring, replacement_substring, 1)


def compute_indices(
    latex_stem_text: str,
    original_substring: str,
) -> Optional[Tuple[int, int]]:
    """
    Compute start_pos and end_pos for a substring.
    
    Args:
        latex_stem_text: The original question stem
        original_substring: The substring to find
    
    Returns:
        Tuple of (start_pos, end_pos) or None if not found
    """
    start_pos = latex_stem_text.find(original_substring)
    if start_pos == -1:
        return None
    end_pos = start_pos + len(original_substring)
    return (start_pos, end_pos)

