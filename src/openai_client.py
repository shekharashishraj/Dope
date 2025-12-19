"""OpenAI API client with batching and retry logic."""
import json
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
from openai import OpenAI
from .config import Config

logger = logging.getLogger(__name__)

def get_timezone(config):
    """Get timezone from config."""
    timezone_str = config.logging_timezone if config else "America/Denver"
    return pytz.timezone(timezone_str)


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
        self.max_retries = config.retry_max_retries if hasattr(config, 'retry_max_retries') else config.max_retries
        self.timeout = config.timeout
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.frequency_penalty = config.frequency_penalty
        self.presence_penalty = config.presence_penalty
        self.max_tokens = config.max_tokens
        self.mappings_per_question = config.mappings_per_question
        # Retry configuration
        self.retry_initial_backoff = config.retry_initial_backoff
        self.retry_max_backoff = config.retry_max_backoff
        self.retry_backoff_multiplier = config.retry_backoff_multiplier
        self.retry_on_rate_limit = config.retry_on_rate_limit
        self.retry_on_timeout = config.retry_on_timeout
        self.retry_on_connection_error = config.retry_on_connection_error
        # Performance delays
        self.delay_between_requests = config.performance_delay_between_requests
        # System message
        self.system_message = config.prompt_system_message
        # Log probabilities
        self.logprobs_enabled = config.logprobs_enabled
        self.top_logprobs = config.top_logprobs
    
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
        prompt_length = len(prompt)
        prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        logger.info(f"API call - Prompt length: {prompt_length} chars")
        logger.info(f"API call - Model: {self.model}, Temperature: {self.temperature}, Timeout: {self.timeout}s")
        logger.info(f"API call - Prompt preview (first 500 chars): {prompt_preview}")
        # Log complete prompt at DEBUG level (saved to file)
        logger.debug(f"API call - Complete prompt:\n{prompt}")
        
        tz = get_timezone(self.config)
        for attempt in range(self.max_retries):
            call_start = datetime.now(tz)
            call_start_time = call_start.strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.info(f"API call attempt {attempt + 1}/{self.max_retries} started at {call_start_time}")
            
            try:
                # Build API parameters
                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.temperature,
                    "timeout": self.timeout
                }
                
                # Add optional parameters if set
                if self.top_p is not None:
                    api_params["top_p"] = self.top_p
                if self.frequency_penalty is not None:
                    api_params["frequency_penalty"] = self.frequency_penalty
                if self.presence_penalty is not None:
                    api_params["presence_penalty"] = self.presence_penalty
                if self.max_tokens is not None:
                    api_params["max_tokens"] = self.max_tokens
                
                # Add log probs if enabled
                if self.logprobs_enabled:
                    api_params["logprobs"] = True
                    if self.top_logprobs > 0:
                        api_params["top_logprobs"] = self.top_logprobs
                
                response = self.client.chat.completions.create(**api_params)
                
                call_time = (datetime.now(tz) - call_start).total_seconds()
                logger.info(f"API call attempt {attempt + 1} completed in {call_time:.2f} seconds")
                
                # Parse response
                content = response.choices[0].message.content
                content_length = len(content)
                content_preview = content[:500] + "..." if len(content) > 500 else content
                logger.info(f"API response - Length: {content_length} chars")
                logger.info(f"API response - Preview (first 500 chars): {content_preview}")
                # Log complete response at DEBUG level (saved to file)
                logger.debug(f"API response - Complete response:\n{content}")
                
                # Log token usage if available
                if hasattr(response, 'usage'):
                    usage = response.usage
                    logger.info(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
                    # Calculate cost estimate (approximate)
                    # GPT-4o pricing: $2.50/$10 per 1M tokens (input/output)
                    input_cost = (usage.prompt_tokens / 1_000_000) * 2.50
                    output_cost = (usage.completion_tokens / 1_000_000) * 10.00
                    total_cost = input_cost + output_cost
                    logger.info(f"Estimated cost: ${total_cost:.4f} (Input: ${input_cost:.4f}, Output: ${output_cost:.4f})")
                
                # Log log probs if available
                if self.logprobs_enabled and hasattr(response.choices[0], 'logprobs') and response.choices[0].logprobs:
                    logprobs = response.choices[0].logprobs
                    tokens_count = len(logprobs.tokens) if logprobs.tokens else 0
                    avg_logprob = sum(logprobs.token_logprobs) / len(logprobs.token_logprobs) if logprobs.token_logprobs else 0
                    logger.info(f"Log probs - Tokens: {tokens_count}, Avg logprob: {avg_logprob:.4f}")
                    logger.debug(f"Log probs - Full details: {logprobs}")
                
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
                        logger.info(f"Successfully parsed {len(parsed)} perturbation mappings")
                        return parsed
                    else:
                        logger.warning(f"Unexpected JSON response type: {type(parsed)}")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content (first 500 chars): {content[:500]}")
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
                call_time = (datetime.now(tz) - call_start).total_seconds()
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff with configurable parameters
                    wait_time = min(
                        self.retry_initial_backoff * (self.retry_backoff_multiplier ** attempt),
                        self.retry_max_backoff
                    )
                    
                    # Check if we should retry based on error type
                    should_retry = False
                    error_str = str(e).lower()
                    
                    if "rate limit" in error_str and self.retry_on_rate_limit:
                        should_retry = True
                    elif "timeout" in error_str and self.retry_on_timeout:
                        should_retry = True
                    elif "connection" in error_str and self.retry_on_connection_error:
                        should_retry = True
                    elif "rate limit" not in error_str and "timeout" not in error_str and "connection" not in error_str:
                        # Retry on other errors by default
                        should_retry = True
                    
                    if should_retry:
                        logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}) after {call_time:.2f}s: {e}")
                        logger.warning(f"Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"API call failed with non-retryable error: {e}")
                        raise
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts (total time: {call_time:.2f}s): {e}", exc_info=True)
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
        tz = get_timezone(self.config)
        batch_start = datetime.now(tz)
        logger.info(f"=== Batch generation started for {len(question_prompts)} questions ===")
        logger.info(f"Start time ({tz.zone}): {batch_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        if not question_prompts:
            logger.warning("No question prompts provided")
            return {}
        
        # If only one question, process it individually
        tz = get_timezone(self.config)
        if len(question_prompts) == 1:
            question_idx = list(question_prompts.keys())[0]
            prompt = question_prompts[question_idx]
            logger.info(f"Processing single question {question_idx}")
            try:
                mappings = self._call_api_with_retry(prompt)
                batch_time = (datetime.now(tz) - batch_start).total_seconds()
                logger.info(f"Batch generation completed in {batch_time:.2f} seconds")
                logger.info(f"Generated {len(mappings)} perturbations for question {question_idx}")
                return {question_idx: mappings}
            except Exception as e:
                batch_time = (datetime.now(tz) - batch_start).total_seconds()
                logger.error(f"Failed to generate perturbations for question {question_idx} after {batch_time:.2f}s: {e}", exc_info=True)
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
            logger.info(f"Combining {len(question_prompts)} questions into single batch prompt")
            batch_prompt_length = len(batch_prompt)
            logger.info(f"Batch prompt length: {batch_prompt_length} chars")
            # Log complete batch prompt at DEBUG level (saved to file)
            logger.debug(f"Batch prompt - Complete prompt:\n{batch_prompt}")
            
            # Single API call for all questions
            all_mappings = self._call_api_with_retry(batch_prompt)
            
            # Parse and organize mappings by question index
            parse_start = datetime.now(tz)
            results = {}
            for idx in question_indices:
                results[idx] = []
            
            if isinstance(all_mappings, list):
                for mapping in all_mappings:
                    if isinstance(mapping, dict) and 'question_index' in mapping:
                        q_idx = mapping['question_index']
                        if q_idx in results:
                            results[q_idx].append(mapping)
            
            parse_time = (datetime.now(tz) - parse_start).total_seconds()
            total_mappings = sum(len(m) for m in results.values())
            logger.info(f"Parsed {total_mappings} total perturbations in {parse_time:.2f} seconds")
            for idx, mappings in results.items():
                logger.debug(f"Question {idx}: {len(mappings)} perturbations")
            
            batch_time = (datetime.now(tz) - batch_start).total_seconds()
            logger.info(f"Generated perturbations for {len(question_prompts)} questions in 1 API call (saved {len(question_prompts) - 1} calls)")
            logger.info(f"Batch generation completed in {batch_time:.2f} seconds")
            logger.info(f"End time ({tz.zone}): {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return results
            
        except Exception as e:
            batch_time = (datetime.now(tz) - batch_start).total_seconds()
            logger.error(f"Batch API call failed after {batch_time:.2f}s: {e}. Falling back to individual calls.", exc_info=True)
            # Fallback to individual calls if batch fails
            fallback_start = datetime.now(tz)
            results = {}
            logger.info(f"Starting fallback to individual API calls for {len(question_prompts)} questions")
            for question_idx, prompt in question_prompts.items():
                try:
                    logger.info(f"Processing question {question_idx} individually")
                    mappings = self._call_api_with_retry(prompt)
                    results[question_idx] = mappings
                    logger.debug(f"Question {question_idx}: {len(mappings)} perturbations generated")
                    # Use configured delay between requests
                    if self.delay_between_requests > 0:
                        time.sleep(self.delay_between_requests)
                except Exception as e2:
                    logger.error(f"Failed to generate perturbations for question {question_idx}: {e2}", exc_info=True)
                    results[question_idx] = []
            fallback_time = (datetime.now(tz) - fallback_start).total_seconds()
            total_batch_time = (datetime.now(tz) - batch_start).total_seconds()
            logger.info(f"Fallback completed in {fallback_time:.2f} seconds (total batch time: {total_batch_time:.2f}s)")
            return results
    
    def create_batch_file(
        self,
        question_prompts: Dict[int, str],
        output_path: Path
    ) -> Path:
        """
        Create a JSONL file for OpenAI Batch API.
        
        Args:
            question_prompts: Dictionary mapping question_index to prompt string
            output_path: Path where JSONL file should be created
        
        Returns:
            Path to created JSONL file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for question_idx, prompt in sorted(question_prompts.items()):
                # Log complete prompt for each question at DEBUG level
                logger.debug(f"Batch file - Question {question_idx} - Complete prompt:\n{prompt}")
                
                # Build body dictionary
                body = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self.system_message
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature
                }
                
                # Add optional parameters if set
                if self.top_p is not None:
                    body["top_p"] = self.top_p
                if self.frequency_penalty is not None:
                    body["frequency_penalty"] = self.frequency_penalty
                if self.presence_penalty is not None:
                    body["presence_penalty"] = self.presence_penalty
                if self.max_tokens is not None:
                    body["max_tokens"] = self.max_tokens
                
                # Add log probs if enabled
                if self.logprobs_enabled:
                    body["logprobs"] = True
                    if self.top_logprobs > 0:
                        body["top_logprobs"] = self.top_logprobs
                
                request = {
                    "custom_id": f"question_{question_idx}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body
                }
                f.write(json.dumps(request) + '\n')
        
        logger.info(f"Created batch file with {len(question_prompts)} requests: {output_path}")
        logger.info(f"Batch file contains prompts for questions: {sorted(question_prompts.keys())}")
        return output_path
    
    def upload_batch_file(self, batch_file_path: Path) -> str:
        """
        Upload a batch file to OpenAI Batch API.
        
        Args:
            batch_file_path: Path to JSONL batch file
        
        Returns:
            Batch ID from OpenAI
        """
        try:
            with open(batch_file_path, 'rb') as f:
                batch_input_file = self.client.files.create(
                    file=f,
                    purpose="batch"
                )
            
            batch = self.client.batches.create(
                input_file_id=batch_input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            
            logger.info(f"Uploaded batch file. Batch ID: {batch.id}, Status: {batch.status}")
            return batch.id
        except Exception as e:
            logger.error(f"Failed to upload batch file: {e}")
            raise
    
    def check_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Check the status of a batch.
        
        Args:
            batch_id: Batch ID from OpenAI
        
        Returns:
            Batch status information
        """
        try:
            batch = self.client.batches.retrieve(batch_id)
            return {
                "id": batch.id,
                "status": batch.status,
                "request_counts": {
                    "total": batch.request_counts.total if hasattr(batch, 'request_counts') else None,
                    "completed": batch.request_counts.completed if hasattr(batch, 'request_counts') else None,
                    "failed": batch.request_counts.failed if hasattr(batch, 'request_counts') else None
                } if hasattr(batch, 'request_counts') else {},
                "output_file_id": batch.output_file_id if hasattr(batch, 'output_file_id') else None,
                "error_file_id": batch.error_file_id if hasattr(batch, 'error_file_id') else None
            }
        except Exception as e:
            logger.error(f"Failed to check batch status: {e}")
            raise
    
    def download_batch_results(self, batch_id: str, output_path: Path) -> Path:
        """
        Download batch results from OpenAI.
        
        Args:
            batch_id: Batch ID from OpenAI
            output_path: Path where results should be saved
        
        Returns:
            Path to downloaded results file
        """
        try:
            batch = self.client.batches.retrieve(batch_id)
            
            if not batch.output_file_id:
                raise ValueError(f"Batch {batch_id} has no output file yet. Status: {batch.status}")
            
            # Download the output file
            output_file = self.client.files.content(batch.output_file_id)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in output_file.iter_bytes():
                    f.write(chunk)
            
            logger.info(f"Downloaded batch results to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to download batch results: {e}")
            raise
    
    def parse_batch_results(self, results_file_path: Path) -> Dict[int, List[Dict[str, Any]]]:
        """
        Parse batch results JSONL file and organize by question index.
        
        Args:
            results_file_path: Path to batch results JSONL file
        
        Returns:
            Dictionary mapping question_index to list of perturbation mappings
        """
        results = {}
        
        try:
            with open(results_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        result = json.loads(line)
                        custom_id = result.get('custom_id', '')
                        
                        # Extract question index from custom_id (format: "question_1")
                        if custom_id.startswith('question_'):
                            question_idx = int(custom_id.split('_')[1])
                        else:
                            logger.warning(f"Unexpected custom_id format: {custom_id}")
                            continue
                        
                        # Parse response body
                        response_body = result.get('response', {}).get('body', {})
                        if 'error' in response_body:
                            logger.error(f"Error in batch result for question {question_idx}: {response_body['error']}")
                            results[question_idx] = []
                            continue
                        
                        # Extract content from response
                        content = response_body.get('choices', [{}])[0].get('message', {}).get('content', '')
                        if not content:
                            logger.warning(f"No content in response for question {question_idx}")
                            results[question_idx] = []
                            continue
                        
                        # Extract log probs if available
                        logprobs_data = None
                        if self.logprobs_enabled:
                            logprobs_data = response_body.get('choices', [{}])[0].get('logprobs')
                            if logprobs_data:
                                tokens_count = len(logprobs_data.get('tokens', []))
                                avg_logprob = sum(logprobs_data.get('token_logprobs', [])) / len(logprobs_data.get('token_logprobs', [])) if logprobs_data.get('token_logprobs') else 0
                                logger.debug(f"Batch log probs - Question {question_idx} - Tokens: {tokens_count}, Avg logprob: {avg_logprob:.4f}")
                        
                        # Log complete response at DEBUG level (saved to file)
                        content_length = len(content)
                        content_preview = content[:500] + "..." if len(content) > 500 else content
                        logger.info(f"Batch result - Question {question_idx} - Response length: {content_length} chars")
                        logger.info(f"Batch result - Question {question_idx} - Response preview (first 500 chars): {content_preview}")
                        logger.debug(f"Batch result - Question {question_idx} - Complete response:\n{content}")
                        
                        # Parse JSON from content
                        try:
                            content_clean = content.strip()
                            if content_clean.startswith('```'):
                                lines = content_clean.split('\n')
                                content_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else content_clean
                                content_clean = content_clean.strip()
                            
                            parsed = json.loads(content_clean)
                            
                            # Handle different response formats
                            if isinstance(parsed, dict):
                                for key in ['mappings', 'perturbations', 'results', 'data', 'array']:
                                    if key in parsed and isinstance(parsed[key], list):
                                        results[question_idx] = parsed[key]
                                        break
                                else:
                                    logger.warning(f"No array found in response for question {question_idx}")
                                    results[question_idx] = []
                            elif isinstance(parsed, list):
                                results[question_idx] = parsed
                            else:
                                logger.warning(f"Unexpected response type for question {question_idx}: {type(parsed)}")
                                results[question_idx] = []
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON for question {question_idx}: {e}")
                            # Try to extract JSON array from text
                            array_match = re.search(r'\[.*\]', content, re.DOTALL)
                            if array_match:
                                try:
                                    results[question_idx] = json.loads(array_match.group(0))
                                except:
                                    results[question_idx] = []
                            else:
                                results[question_idx] = []
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line in batch results: {e}")
                        continue
            
            logger.info(f"Parsed batch results for {len(results)} questions")
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse batch results file: {e}")
            raise

