"""Stage Executor - Execute individual LLM stages with retry logic.

This module handles:
- Calling OpenAI API for each stage
- Parsing JSON responses
- Error handling and retries
"""
import json
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from prompts.staged_pipeline.stage1_semantic_plan import (
    format_stage1_tf_prompt,
    format_stage1_mcq_prompt,
)
from prompts.staged_pipeline.stage2_span_selection import format_stage2_prompt
from prompts.staged_pipeline.stage3_replacement import (
    format_stage3_tf_prompt,
    format_stage3_mcq_prompt,
)
from prompts.staged_pipeline.stage5_flip_judge import (
    format_stage5_tf_prompt,
    format_stage5_mcq_prompt,
)

logger = logging.getLogger(__name__)


class StageExecutor:
    """Executes individual stages of the staged pipeline."""
    
    def __init__(self, openai_client, config):
        """
        Initialize the stage executor.
        
        Args:
            openai_client: OpenAI client instance
            config: Configuration object
        """
        self.client = openai_client.client  # The underlying OpenAI client
        self.model = openai_client.model
        self.temperature = openai_client.temperature
        self.timeout = openai_client.timeout
        self.max_retries = config.retry.max_retries
        self.retry_initial_backoff = config.retry.initial_backoff
        self.retry_max_backoff = config.retry.max_backoff
        self.retry_backoff_multiplier = config.retry.backoff_multiplier
    
    def execute_stage1_tf(
        self,
        latex_stem_text: str,
        gold_answer: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 1 for TF questions.
        
        Args:
            latex_stem_text: The question stem
            gold_answer: The correct answer ("True" or "False")
        
        Returns:
            Dict with target_wrong_answer and flip_strategy, or None on failure
        """
        prompt = format_stage1_tf_prompt(latex_stem_text, gold_answer)
        return self._call_api_and_parse(prompt, "Stage 1 TF")
    
    def execute_stage1_mcq(
        self,
        latex_stem_text: str,
        gold_answer: str,
        options: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 1 for MCQ questions.
        
        Args:
            latex_stem_text: The question stem
            gold_answer: The correct answer option
            options: Dictionary of option letter to option text
        
        Returns:
            Dict with target_wrong_answer and flip_strategy, or None on failure
        """
        prompt = format_stage1_mcq_prompt(latex_stem_text, gold_answer, options)
        result = self._call_api_and_parse(prompt, "Stage 1 MCQ")
        
        # Validate that target_wrong_answer is not the gold answer
        if result and result.get("target_wrong_answer") == gold_answer:
            logger.warning(f"Stage 1 MCQ returned gold answer as target: {gold_answer}")
            return None
        
        return result
    
    def execute_stage2(
        self,
        latex_stem_text: str,
        flip_strategy: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 2 for span selection.
        
        Args:
            latex_stem_text: The question stem
            flip_strategy: The flip strategy from Stage 1
        
        Returns:
            Dict with original_substring, or None on failure
        """
        prompt = format_stage2_prompt(latex_stem_text, flip_strategy)
        result = self._call_api_and_parse(prompt, "Stage 2")
        
        # Validate that original_substring exists in stem
        if result:
            original_substring = result.get("original_substring", "")
            if original_substring not in latex_stem_text:
                logger.warning(
                    f"Stage 2 returned substring not found in stem: "
                    f"'{original_substring[:50]}...'"
                )
                return None
        
        return result
    
    def execute_stage3_tf(
        self,
        latex_stem_text: str,
        original_substring: str,
        gold_answer: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 3 for TF questions.
        
        Args:
            latex_stem_text: The question stem
            original_substring: The substring from Stage 2
            gold_answer: The correct answer
        
        Returns:
            Dict with replacement_substring, or None on failure
        """
        prompt = format_stage3_tf_prompt(latex_stem_text, original_substring, gold_answer)
        result = self._call_api_and_parse(prompt, "Stage 3 TF")
        
        # Validate replacement is different from original
        if result:
            replacement = result.get("replacement_substring", "")
            if replacement == original_substring:
                logger.warning("Stage 3 TF returned identical replacement")
                return None
        
        return result
    
    def execute_stage3_mcq(
        self,
        latex_stem_text: str,
        original_substring: str,
        gold_answer: str,
        target_wrong_answer: str,
        options: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 3 for MCQ questions.
        
        Args:
            latex_stem_text: The question stem
            original_substring: The substring from Stage 2
            gold_answer: The correct answer
            target_wrong_answer: The target wrong option
            options: Dictionary of option letter to option text
        
        Returns:
            Dict with replacement_substring, or None on failure
        """
        prompt = format_stage3_mcq_prompt(
            latex_stem_text, original_substring, gold_answer, target_wrong_answer, options
        )
        result = self._call_api_and_parse(prompt, "Stage 3 MCQ")
        
        # Validate replacement is different from original
        if result:
            replacement = result.get("replacement_substring", "")
            if replacement == original_substring:
                logger.warning("Stage 3 MCQ returned identical replacement")
                return None
            
            # Validate length constraint for MCQ
            if len(replacement) > len(original_substring):
                logger.warning(
                    f"Stage 3 MCQ replacement too long: "
                    f"{len(replacement)} > {len(original_substring)}"
                )
                return None
        
        return result
    
    def execute_stage5_tf(
        self,
        perturbed_stem: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 5 judge for TF questions.
        
        Args:
            perturbed_stem: The question stem after replacement
        
        Returns:
            Dict with answer ("True" or "False"), or None on failure
        """
        prompt = format_stage5_tf_prompt(perturbed_stem)
        result = self._call_api_and_parse(prompt, "Stage 5 TF Judge")
        
        # Normalize answer
        if result:
            answer = result.get("answer", "").strip()
            # Normalize to "True" or "False"
            if answer.lower() in ["true", "t", "yes"]:
                result["answer"] = "True"
            elif answer.lower() in ["false", "f", "no"]:
                result["answer"] = "False"
            else:
                logger.warning(f"Stage 5 TF Judge returned invalid answer: {answer}")
                return None
        
        return result
    
    def execute_stage5_mcq(
        self,
        perturbed_stem: str,
        options: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute Stage 5 judge for MCQ questions.
        
        Args:
            perturbed_stem: The question stem after replacement
            options: Dictionary of option letter to option text
        
        Returns:
            Dict with answer (option letter), or None on failure
        """
        prompt = format_stage5_mcq_prompt(perturbed_stem, options)
        result = self._call_api_and_parse(prompt, "Stage 5 MCQ Judge")
        
        # Validate answer is a valid option
        if result:
            answer = result.get("answer", "").strip().upper()
            if answer and answer[0] in options:
                result["answer"] = answer[0]  # Normalize to single letter
            else:
                logger.warning(f"Stage 5 MCQ Judge returned invalid answer: {answer}")
                return None
        
        return result
    
    def _call_api_and_parse(
        self,
        prompt: str,
        stage_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Call OpenAI API and parse JSON response.
        
        Args:
            prompt: The prompt to send
            stage_name: Name of the stage (for logging)
        
        Returns:
            Parsed JSON dict or None on failure
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise assistant that outputs only valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    timeout=self.timeout,
                    max_tokens=500,  # Stage outputs are small
                )
                
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"{stage_name} returned empty response")
                    continue
                
                # Parse JSON from response
                result = self._parse_json_response(content)
                if result:
                    logger.debug(f"{stage_name} succeeded: {result}")
                    return result
                else:
                    logger.warning(f"{stage_name} failed to parse JSON from: {content[:200]}")
                    
            except Exception as e:
                wait_time = min(
                    self.retry_initial_backoff * (self.retry_backoff_multiplier ** attempt),
                    self.retry_max_backoff
                )
                logger.warning(
                    f"{stage_name} attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
        
        logger.error(f"{stage_name} failed after {self.max_retries} attempts")
        return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response.
        
        Handles:
        - Clean JSON
        - JSON wrapped in markdown code blocks
        - JSON with extra text before/after
        
        Args:
            content: Raw LLM response content
        
        Returns:
            Parsed dict or None
        """
        content = content.strip()
        
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try removing markdown code block
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (```json and ```)
            if len(lines) >= 3:
                json_content = "\n".join(lines[1:-1])
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    pass
        
        # Try to extract JSON object from text
        import re
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Try more aggressive JSON extraction (nested braces)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None

