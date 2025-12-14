"""OpenAI API client with batching and retry logic."""
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .config import Config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client with batching and error handling."""
    
    def __init__(self, config: Config):
        """
        Initialize OpenAI client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        api_key = config.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.openai_model
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        self.temperature = config.temperature
        self.mappings_per_question = config.mappings_per_question
    
    def generate_perturbations(
        self, 
        prompts: List[str],
        question_indices: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Generate perturbations for a batch of questions.
        
        Args:
            prompts: List of formatted prompts (one per question)
            question_indices: List of question indices corresponding to prompts
        
        Returns:
            Dictionary mapping question_index to list of perturbation mappings
        """
        results = {}
        
        # Process each prompt (we could batch multiple prompts in one call, but for now
        # we'll process them individually to ensure proper error handling)
        for prompt, question_idx in zip(prompts, question_indices):
            try:
                mappings = self._call_api_with_retry(prompt)
                results[question_idx] = mappings
            except Exception as e:
                logger.error(f"Failed to generate perturbations for question {question_idx}: {e}")
                results[question_idx] = []
        
        return results
    
    def _call_api_with_retry(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Call OpenAI API with retry logic.
        
        Args:
            prompt: Formatted prompt string
        
        Returns:
            List of perturbation mappings
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates JSON array responses. Always return valid JSON arrays."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    timeout=self.timeout
                )
                
                # Parse response
                content = response.choices[0].message.content
                
                # Try to parse as JSON
                try:
                    # Clean content - remove markdown code blocks if present
                    content_clean = content.strip()
                    if content_clean.startswith('```'):
                        # Remove markdown code block markers
                        lines = content_clean.split('\n')
                        content_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else content_clean
                        content_clean = content_clean.strip()
                    
                    # Response might be a JSON object with an array, or directly an array
                    parsed = json.loads(content_clean)
                    
                    # If it's a dict, look for common keys that might contain the array
                    if isinstance(parsed, dict):
                        # Check for common array keys
                        for key in ['mappings', 'perturbations', 'results', 'data', 'array']:
                            if key in parsed and isinstance(parsed[key], list):
                                return parsed[key]
                        # If no array found, return empty list
                        logger.warning(f"JSON response is a dict but no array found: {parsed}")
                        return []
                    elif isinstance(parsed, list):
                        return parsed
                    else:
                        logger.warning(f"Unexpected JSON response type: {type(parsed)}")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content: {content[:500]}")
                    # Try to extract JSON array from text
                    # Look for array pattern
                    array_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if array_match:
                        try:
                            return json.loads(array_match.group(0))
                        except:
                            pass
                    return []
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts: {e}")
                    raise
        
        return []
    
    def batch_generate_perturbations(
        self,
        question_prompts: Dict[int, str]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Generate perturbations for multiple questions in a single batch API call.
        
        Args:
            question_prompts: Dictionary mapping question_index to prompt string
        
        Returns:
            Dictionary mapping question_index to list of perturbation mappings
        """
        if not question_prompts:
            return {}
        
        # If only one question, process it individually
        if len(question_prompts) == 1:
            question_idx = list(question_prompts.keys())[0]
            prompt = question_prompts[question_idx]
            try:
                mappings = self._call_api_with_retry(prompt)
                return {question_idx: mappings}
            except Exception as e:
                logger.error(f"Failed to generate perturbations for question {question_idx}: {e}")
                return {question_idx: []}
        
        # Combine all questions into a single batch prompt
        question_indices = sorted(question_prompts.keys())
        prompts_sections = []
        
        for idx in question_indices:
            prompt = question_prompts[idx]
            prompts_sections.append(f"=== QUESTION {idx} ===\n{prompt}")
        
        batch_prompt = f"""Process the following {len(question_prompts)} questions and generate perturbations for ALL of them in a single response.

{chr(10).join(prompts_sections)}

CRITICAL INSTRUCTIONS:
- Generate perturbations for ALL questions above
- Return a SINGLE JSON array containing mappings from ALL questions
- Each mapping must have the correct question_index field
- The total number of mappings should be {len(question_prompts)} * {self.mappings_per_question} = {len(question_prompts) * self.mappings_per_question}

Return format (single JSON array with all mappings):
[
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "B", "reasoning": "..."}},
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "C", "reasoning": "..."}},
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "D", "reasoning": "..."}},
  {{"question_index": 2, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "A", "reasoning": "..."}},
  ...
]

Return ONLY valid JSON array, no markdown or additional text."""
        
        try:
            # Single API call for all questions
            all_mappings = self._call_api_with_retry(batch_prompt)
            
            # Parse and organize mappings by question index
            results = {}
            for idx in question_indices:
                results[idx] = []
            
            if isinstance(all_mappings, list):
                for mapping in all_mappings:
                    if isinstance(mapping, dict) and 'question_index' in mapping:
                        q_idx = mapping['question_index']
                        if q_idx in results:
                            results[q_idx].append(mapping)
            
            logger.info(f"Generated perturbations for {len(question_prompts)} questions in 1 API call (saved {len(question_prompts) - 1} calls)")
            return results
            
        except Exception as e:
            logger.error(f"Batch API call failed: {e}. Falling back to individual calls.")
            # Fallback to individual calls if batch fails
            results = {}
            for question_idx, prompt in question_prompts.items():
                try:
                    mappings = self._call_api_with_retry(prompt)
                    results[question_idx] = mappings
                    time.sleep(0.5)
                except Exception as e2:
                    logger.error(f"Failed to generate perturbations for question {question_idx}: {e2}")
                    results[question_idx] = []
            return results

