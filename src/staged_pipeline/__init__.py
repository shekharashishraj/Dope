"""Staged pipeline for 5-stage mapping generation.

This module implements a multi-stage approach to perturbation generation:
- Stage 1: Semantic Planning (LLM) - Identify concept to flip
- Stage 2: Span Selection (LLM) - Select exact substring
- Stage 3: Replacement Generation (LLM) - Generate replacement text
- Stage 4: Validation (CODE) - Compute indices and validate constraints
- Stage 5: Flip Verification (LLM Judge) - Verify answer flips
"""
from .staged_generator import StagedMappingGenerator
from .deterministic_validator import validate_mapping, apply_replacement
from .stage_executor import StageExecutor

__all__ = [
    "StagedMappingGenerator",
    "validate_mapping",
    "apply_replacement",
    "StageExecutor",
]

