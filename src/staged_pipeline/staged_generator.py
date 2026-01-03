"""Staged Mapping Generator - Main orchestrator for 5-stage pipeline.

This module orchestrates the complete 5-stage mapping generation:
1. Stage 1: Semantic Planning (LLM) - Identify concept to flip
2. Stage 2: Span Selection (LLM) - Select exact substring  
3. Stage 3: Replacement Generation (LLM) - Generate replacement text
4. Stage 4: Validation (CODE) - Compute indices and validate constraints
5. Stage 5: Flip Verification (LLM Judge) - Verify answer flips

Includes retry logic for failed stages.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .stage_executor import StageExecutor
from .deterministic_validator import validate_mapping, apply_replacement
from ..models.perturbation import PerturbationMapping

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result from a single pipeline attempt."""
    success: bool
    failed_stage: Optional[int] = None
    error: Optional[str] = None
    mapping: Optional[PerturbationMapping] = None
    
    # Intermediate results for debugging
    stage1_result: Optional[Dict[str, Any]] = None
    stage2_result: Optional[Dict[str, Any]] = None
    stage3_result: Optional[Dict[str, Any]] = None
    stage4_result: Optional[Dict[str, Any]] = None
    stage5_result: Optional[Dict[str, Any]] = None


class StagedMappingGenerator:
    """
    Orchestrates the 5-stage mapping generation pipeline.
    
    Each stage is focused on one type of work:
    - Stages 1-3, 5: LLM calls for semantic decisions
    - Stage 4: Deterministic code validation
    
    The generator includes retry logic that re-runs from Stage 1
    when any stage fails.
    """
    
    def __init__(self, openai_client, config):
        """
        Initialize the staged mapping generator.
        
        Args:
            openai_client: OpenAI client instance (OpenAIClient from src/openai_client.py)
            config: Configuration object
        """
        self.openai_client = openai_client
        self.config = config
        self.stage_executor = StageExecutor(openai_client, config)
        
        # Configuration for staged pipeline
        staged_config = getattr(config.processing, 'staged_pipeline', None)
        if staged_config:
            self.max_retries_per_mapping = getattr(staged_config, 'max_retries_per_mapping', 3)
            self.enable_flip_verification = getattr(staged_config, 'enable_flip_verification', True)
        else:
            self.max_retries_per_mapping = 3
            self.enable_flip_verification = True
    
    def generate_mappings(
        self,
        question: Any,
        k: int = 3,
    ) -> List[PerturbationMapping]:
        """
        Generate k validated mappings for a question.
        
        This is the main entry point for the staged pipeline.
        
        Args:
            question: Question object with question_number, question_type, 
                     latex_stem_text, gold_answer, options (for MCQ)
            k: Number of mappings to generate
        
        Returns:
            List of validated PerturbationMapping objects
        """
        validated_mappings = []
        attempts = 0
        max_attempts = k * self.max_retries_per_mapping
        
        question_type = question.question_type.value.upper()
        latex_stem_text = question.latex_stem_text or question.stem_text or ""
        gold_answer = question.gold_answer
        options = getattr(question, 'options', {}) or {}
        question_number = question.question_number
        
        logger.info(
            f"Staged pipeline: Generating {k} mappings for question {question_number} "
            f"(type: {question_type})"
        )
        
        while len(validated_mappings) < k and attempts < max_attempts:
            attempts += 1
            logger.debug(f"Attempt {attempts}/{max_attempts} for question {question_number}")
            
            # Run the complete pipeline
            if question_type == "TF":
                result = self._run_pipeline_tf(
                    latex_stem_text=latex_stem_text,
                    gold_answer=gold_answer,
                    question_number=question_number,
                )
            elif question_type == "MCQ":
                result = self._run_pipeline_mcq(
                    latex_stem_text=latex_stem_text,
                    gold_answer=gold_answer,
                    options=options,
                    question_number=question_number,
                )
            else:
                logger.warning(f"Unsupported question type: {question_type}")
                break
            
            if result.success and result.mapping:
                # Check for duplicates
                if not self._is_duplicate(result.mapping, validated_mappings):
                    validated_mappings.append(result.mapping)
                    logger.info(
                        f"Question {question_number}: Generated mapping {len(validated_mappings)}/{k}"
                    )
                else:
                    logger.debug(f"Question {question_number}: Skipping duplicate mapping")
            else:
                logger.debug(
                    f"Question {question_number}: Attempt {attempts} failed at stage "
                    f"{result.failed_stage}: {result.error}"
                )
        
        logger.info(
            f"Staged pipeline: Generated {len(validated_mappings)}/{k} mappings for "
            f"question {question_number} in {attempts} attempts"
        )
        
        return validated_mappings
    
    def _run_pipeline_tf(
        self,
        latex_stem_text: str,
        gold_answer: str,
        question_number: int,
    ) -> StageResult:
        """
        Run the complete pipeline for a TF question.
        
        Args:
            latex_stem_text: The question stem
            gold_answer: The correct answer
            question_number: Question number for the mapping
        
        Returns:
            StageResult with success status and mapping
        """
        result = StageResult(success=False)
        
        # Stage 1: Semantic Planning
        stage1 = self.stage_executor.execute_stage1_tf(latex_stem_text, gold_answer)
        if not stage1:
            result.failed_stage = 1
            result.error = "Stage 1 failed: Could not generate flip strategy"
            return result
        result.stage1_result = stage1
        
        target_wrong_answer = stage1.get("target_wrong_answer")
        flip_strategy = stage1.get("flip_strategy", "")
        
        # Stage 2: Span Selection
        stage2 = self.stage_executor.execute_stage2(latex_stem_text, flip_strategy)
        if not stage2:
            result.failed_stage = 2
            result.error = "Stage 2 failed: Could not select substring"
            return result
        result.stage2_result = stage2
        
        original_substring = stage2.get("original_substring", "")
        
        # Stage 3: Replacement Generation
        stage3 = self.stage_executor.execute_stage3_tf(
            latex_stem_text, original_substring, gold_answer
        )
        if not stage3:
            result.failed_stage = 3
            result.error = "Stage 3 failed: Could not generate replacement"
            return result
        result.stage3_result = stage3
        
        replacement_substring = stage3.get("replacement_substring", "")
        
        # Stage 4: Validation (CODE)
        validation = validate_mapping(
            latex_stem_text,
            original_substring,
            replacement_substring,
            "TF",
        )
        result.stage4_result = validation
        
        if not validation.get("valid"):
            result.failed_stage = 4
            result.error = f"Stage 4 failed: {validation.get('error_details', validation.get('error'))}"
            return result
        
        # Stage 5: Flip Verification (optional)
        if self.enable_flip_verification:
            perturbed_stem = apply_replacement(
                latex_stem_text, original_substring, replacement_substring
            )
            stage5 = self.stage_executor.execute_stage5_tf(perturbed_stem)
            result.stage5_result = stage5
            
            if not stage5:
                result.failed_stage = 5
                result.error = "Stage 5 failed: Judge could not answer"
                return result
            
            predicted_answer = stage5.get("answer")
            if predicted_answer != target_wrong_answer:
                result.failed_stage = 5
                result.error = (
                    f"Stage 5 failed: Expected {target_wrong_answer}, "
                    f"got {predicted_answer}"
                )
                return result
        
        # Success! Build the mapping
        mapping = PerturbationMapping(
            question_index=question_number,
            latex_stem_text=latex_stem_text,
            original_substring=original_substring,
            replacement_substring=replacement_substring,
            start_pos=validation["start_pos"],
            end_pos=validation["end_pos"],
            target_wrong_answer=target_wrong_answer,
            reasoning=flip_strategy,
            verification=f"Staged pipeline: Judge confirmed {target_wrong_answer}" if self.enable_flip_verification else "Staged pipeline: Flip verification disabled",
        )
        
        result.success = True
        result.mapping = mapping
        return result
    
    def _run_pipeline_mcq(
        self,
        latex_stem_text: str,
        gold_answer: str,
        options: Dict[str, str],
        question_number: int,
    ) -> StageResult:
        """
        Run the complete pipeline for an MCQ question.
        
        Args:
            latex_stem_text: The question stem
            gold_answer: The correct answer option
            options: Dictionary of option letter to option text
            question_number: Question number for the mapping
        
        Returns:
            StageResult with success status and mapping
        """
        result = StageResult(success=False)
        
        # Stage 1: Semantic Planning
        stage1 = self.stage_executor.execute_stage1_mcq(latex_stem_text, gold_answer, options)
        if not stage1:
            result.failed_stage = 1
            result.error = "Stage 1 failed: Could not generate flip strategy"
            return result
        result.stage1_result = stage1
        
        target_wrong_answer = stage1.get("target_wrong_answer")
        flip_strategy = stage1.get("flip_strategy", "")
        
        # Stage 2: Span Selection
        stage2 = self.stage_executor.execute_stage2(latex_stem_text, flip_strategy)
        if not stage2:
            result.failed_stage = 2
            result.error = "Stage 2 failed: Could not select substring"
            return result
        result.stage2_result = stage2
        
        original_substring = stage2.get("original_substring", "")
        
        # Stage 3: Replacement Generation
        stage3 = self.stage_executor.execute_stage3_mcq(
            latex_stem_text, original_substring, gold_answer, target_wrong_answer, options
        )
        if not stage3:
            result.failed_stage = 3
            result.error = "Stage 3 failed: Could not generate replacement"
            return result
        result.stage3_result = stage3
        
        replacement_substring = stage3.get("replacement_substring", "")
        
        # Stage 4: Validation (CODE)
        validation = validate_mapping(
            latex_stem_text,
            original_substring,
            replacement_substring,
            "MCQ",
            strict_length=True,  # MCQ requires len(replacement) <= len(original)
        )
        result.stage4_result = validation
        
        if not validation.get("valid"):
            result.failed_stage = 4
            result.error = f"Stage 4 failed: {validation.get('error_details', validation.get('error'))}"
            return result
        
        # Stage 5: Flip Verification (optional)
        if self.enable_flip_verification:
            perturbed_stem = apply_replacement(
                latex_stem_text, original_substring, replacement_substring
            )
            stage5 = self.stage_executor.execute_stage5_mcq(perturbed_stem, options)
            result.stage5_result = stage5
            
            if not stage5:
                result.failed_stage = 5
                result.error = "Stage 5 failed: Judge could not answer"
                return result
            
            predicted_answer = stage5.get("answer")
            if predicted_answer != target_wrong_answer:
                result.failed_stage = 5
                result.error = (
                    f"Stage 5 failed: Expected {target_wrong_answer}, "
                    f"got {predicted_answer}"
                )
                return result
        
        # Success! Build the mapping
        mapping = PerturbationMapping(
            question_index=question_number,
            latex_stem_text=latex_stem_text,
            original_substring=original_substring,
            replacement_substring=replacement_substring,
            start_pos=validation["start_pos"],
            end_pos=validation["end_pos"],
            target_wrong_answer=target_wrong_answer,
            reasoning=flip_strategy,
            verification=f"Staged pipeline: Judge confirmed {target_wrong_answer}" if self.enable_flip_verification else "Staged pipeline: Flip verification disabled",
        )
        
        result.success = True
        result.mapping = mapping
        return result
    
    def _is_duplicate(
        self,
        new_mapping: PerturbationMapping,
        existing_mappings: List[PerturbationMapping],
    ) -> bool:
        """
        Check if a mapping is a duplicate of an existing one.
        
        A mapping is considered duplicate if:
        - Same original_substring AND same replacement_substring
        - OR same target_wrong_answer (for diversity)
        
        Args:
            new_mapping: The new mapping to check
            existing_mappings: List of existing mappings
        
        Returns:
            True if duplicate
        """
        for existing in existing_mappings:
            # Check for exact duplicate
            if (new_mapping.original_substring == existing.original_substring and
                new_mapping.replacement_substring == existing.replacement_substring):
                return True
            
            # Check for same target (want diverse targets)
            if new_mapping.target_wrong_answer == existing.target_wrong_answer:
                return True
        
        return False
    
    def generate_mappings_batch(
        self,
        questions: List[Any],
        k: int = 3,
    ) -> Dict[int, List[PerturbationMapping]]:
        """
        Generate mappings for a batch of questions.
        
        Args:
            questions: List of question objects
            k: Number of mappings per question
        
        Returns:
            Dictionary mapping question_number to list of mappings
        """
        results = {}
        
        for question in questions:
            question_number = question.question_number
            mappings = self.generate_mappings(question, k=k)
            results[question_number] = mappings
        
        return results

