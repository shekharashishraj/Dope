"""Validation functions for Pydantic models."""
from typing import Tuple, Optional
from .models.perturbation import PerturbationMapping, Question, Document


def validate_perturbation_mapping(
    mapping: PerturbationMapping,
    stem_text: str,
    gold_answer: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate a perturbation mapping against business rules.
    
    Args:
        mapping: PerturbationMapping to validate
        stem_text: The LaTeX stem text where the perturbation should occur
        gold_answer: Optional gold answer for additional validation
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if original_substring exists in stem_text
    if mapping.original_substring not in stem_text:
        return False, f"original_substring '{mapping.original_substring}' not found in stem_text"
    
    # Verify positions are correct
    actual_start = stem_text.find(mapping.original_substring)
    if actual_start == -1:
        return False, "original_substring not found in stem_text"
    
    # Check length constraint: replacement must be <= original
    if len(mapping.replacement_substring) > len(mapping.original_substring):
        return False, (
            f"replacement_substring ({len(mapping.replacement_substring)} chars) "
            f"must be <= original_substring ({len(mapping.original_substring)} chars)"
        )
    
    # Check that replacement is different from original
    if mapping.original_substring == mapping.replacement_substring:
        return False, "replacement_substring must be different from original_substring"
    
    # Check that neither is empty
    if not mapping.original_substring or not mapping.replacement_substring:
        return False, "original_substring and replacement_substring cannot be empty"
    
    # Check position consistency
    if mapping.end_pos <= mapping.start_pos:
        return False, f"end_pos ({mapping.end_pos}) must be > start_pos ({mapping.start_pos})"
    
    # Check target_wrong_answer if provided and gold_answer is available
    if gold_answer and mapping.target_wrong_answer:
        if mapping.target_wrong_answer == gold_answer:
            return False, f"target_wrong_answer ({mapping.target_wrong_answer}) must be different from gold_answer ({gold_answer})"
    
    return True, None


def validate_question(question: Question) -> Tuple[bool, Optional[str]]:
    """
    Validate a question model.
    
    Args:
        question: Question to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not question.question_number or question.question_number <= 0:
        return False, "question_number must be > 0"
    
    if not question.stem_text:
        return False, "stem_text cannot be empty"
    
    if not question.gold_answer:
        return False, "gold_answer cannot be empty"
    
    # Validate perturbations if present
    for pert in question.perturbations:
        is_valid, error = validate_perturbation_mapping(
            pert,
            question.latex_stem_text or question.stem_text,
            question.gold_answer
        )
        if not is_valid:
            return False, f"Invalid perturbation: {error}"
    
    return True, None


def validate_document(document: Document) -> Tuple[bool, Optional[str]]:
    """
    Validate a document model.
    
    Args:
        document: Document to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not document.docid:
        return False, "docid cannot be empty"
    
    if not document.questions:
        return False, "document must have at least one question"
    
    # Validate each question
    for question in document.questions:
        is_valid, error = validate_question(question)
        if not is_valid:
            return False, f"Invalid question {question.question_number}: {error}"
    
    return True, None

