"""Staged pipeline prompts for 5-stage mapping generation."""
from .shared_constraints import (
    TF_TIER_GUIDANCE,
    TF_PROHIBITED_TECHNIQUES,
    MCQ_TIER_GUIDANCE,
    NEGATION_RULE,
    LENGTH_CONSTRAINT_MCQ,
    LENGTH_CONSTRAINT_TF,
    LATEX_RULE,
)
from .stage1_semantic_plan import STAGE1_TF_TEMPLATE, STAGE1_MCQ_TEMPLATE
from .stage2_span_selection import STAGE2_TEMPLATE
from .stage3_replacement import STAGE3_TF_TEMPLATE, STAGE3_MCQ_TEMPLATE
from .stage5_flip_judge import STAGE5_TF_JUDGE_TEMPLATE, STAGE5_MCQ_JUDGE_TEMPLATE

__all__ = [
    # Shared constraints
    "TF_TIER_GUIDANCE",
    "TF_PROHIBITED_TECHNIQUES",
    "MCQ_TIER_GUIDANCE",
    "NEGATION_RULE",
    "LENGTH_CONSTRAINT_MCQ",
    "LENGTH_CONSTRAINT_TF",
    "LATEX_RULE",
    # Stage templates
    "STAGE1_TF_TEMPLATE",
    "STAGE1_MCQ_TEMPLATE",
    "STAGE2_TEMPLATE",
    "STAGE3_TF_TEMPLATE",
    "STAGE3_MCQ_TEMPLATE",
    "STAGE5_TF_JUDGE_TEMPLATE",
    "STAGE5_MCQ_JUDGE_TEMPLATE",
]

