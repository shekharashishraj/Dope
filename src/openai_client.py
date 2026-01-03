"""OpenAI API client with batching and retry logic."""
import json
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
from pydantic import ValidationError
from openai import OpenAI
from .config import Config
from .models.perturbation import PerturbationMapping, PerturbationListResponse
from .models.api import BatchStatus

logger = logging.getLogger(__name__)

def get_timezone(config):
    """Get timezone from config."""
    timezone_str = config.logging.timezone if config else "America/Denver"
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
        api_key = config.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.openai.model
        self.max_retries = config.retry.max_retries
        self.timeout = config.openai.timeout
        self.temperature = config.openai.temperature
        self.top_p = config.openai.top_p
        self.frequency_penalty = config.openai.frequency_penalty
        self.presence_penalty = config.openai.presence_penalty
        self.max_tokens = config.openai.max_tokens
        self.mappings_per_question = config.processing.mappings_per_question
        # Log probabilities configuration
        self.logprobs = config.openai.logprobs
        self.top_logprobs = config.openai.top_logprobs
        # GPT-5.1 parameters
        self.reasoning_effort = config.openai.reasoning_effort
        self.verbosity = config.openai.verbosity
        # Retry configuration
        self.retry_initial_backoff = config.retry.initial_backoff
        self.retry_max_backoff = config.retry.max_backoff
        self.retry_backoff_multiplier = config.retry.backoff_multiplier
        self.retry_on_rate_limit = config.retry.retry_on_rate_limit
        self.retry_on_timeout = config.retry.retry_on_timeout
        self.retry_on_connection_error = config.retry.retry_on_connection_error
        # Performance delays
        self.delay_between_requests = config.performance.delay_between_requests
        # System message
        self.system_message = config.prompts.system_message
        # Grouped prompts folder
        self.grouped_prompts_folder = config.prompts.grouped_prompts_folder
    
    def _is_gpt5_model(self) -> bool:
        """Check if the model is a GPT-5.x model."""
        return self.config.openai.is_gpt5_model()
    
    def generate_perturbations(
        self, 
        prompts: List[str],
        question_indices: List[int]
    ) -> Dict[int, List[PerturbationMapping]]:
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
    
    def _call_api_with_retry(self, prompt: str, output_dir: Optional[Path] = None) -> List[PerturbationMapping]:
        """
        Call OpenAI API with retry logic.
        
        Args:
            prompt: Formatted prompt string
            output_dir: Optional output directory to save raw response
        
        Returns:
            List of perturbation mappings
        """
        prompt_length = len(prompt)
        prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        logger.info(f"API call - Prompt length: {prompt_length} chars")
        if self._is_gpt5_model():
            logger.info(f"API call - Model: {self.model}, Reasoning: {self.reasoning_effort}, Verbosity: {self.verbosity}, Timeout: {self.timeout}s")
        else:
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
                    "timeout": self.timeout
                }
                
                # GPT-5.1 models use different parameters
                # Note: Current OpenAI Python SDK doesn't support reasoning/verbosity parameters yet
                # The model will work without them (using defaults)
                # TODO: Add these parameters when SDK is updated to support them
                if self._is_gpt5_model():
                    # For now, don't pass reasoning/verbosity as SDK doesn't support them
                    # The model will use default values
                    # When SDK is updated, uncomment these lines:
                    # if self.reasoning_effort is not None:
                    #     api_params["reasoning"] = {"effort": self.reasoning_effort}
                    # if self.verbosity is not None:
                    #     api_params["verbosity"] = self.verbosity
                    pass
                else:
                    # Use traditional parameters for non-GPT-5 models
                    api_params["temperature"] = self.temperature
                    # Add optional parameters if set
                    if self.top_p is not None:
                        api_params["top_p"] = self.top_p
                    if self.frequency_penalty is not None:
                        api_params["frequency_penalty"] = self.frequency_penalty
                    if self.presence_penalty is not None:
                        api_params["presence_penalty"] = self.presence_penalty
                    if self.max_tokens is not None:
                        api_params["max_tokens"] = self.max_tokens
                    # Add logprobs if enabled
                    if self.logprobs:
                        api_params["logprobs"] = True
                        if self.top_logprobs is not None:
                            api_params["top_logprobs"] = self.top_logprobs
                
                # Try structured output first (ensures valid JSON), fallback to regular call
                response = None
                parsed_data = None
                use_structured_output = True
                
                try:
                    # Attempt structured output with Pydantic model
                    logger.info("Attempting structured output with Pydantic model...")
                    parse_response = self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=api_params["messages"],
                        response_format=PerturbationListResponse,
                        timeout=self.timeout
                    )
                    parsed_data = parse_response.choices[0].message.parsed
                    if isinstance(parsed_data, PerturbationListResponse):
                        logger.info("Successfully received structured output from API")
                        # Get the raw response for metadata extraction
                        response = parse_response
                        use_structured_output = True
                    elif isinstance(parsed_data, list):
                        # Handle case where API returns list directly
                        logger.info("Structured output returned list directly, wrapping in response model")
                        parsed_data = PerturbationListResponse(perturbations=parsed_data)
                        response = parse_response
                        use_structured_output = True
                    else:
                        logger.warning(f"Structured output returned unexpected type: {type(parsed_data)}, falling back to JSON parsing")
                        use_structured_output = False
                except Exception as structured_err:
                    logger.warning(f"Structured output failed: {structured_err}. Falling back to regular API call with JSON parsing.")
                    use_structured_output = False
                
                # Fallback to regular API call if structured output failed
                if not use_structured_output:
                    response = self.client.chat.completions.create(**api_params)
                    parsed_data = None
                
                call_time = (datetime.now(tz) - call_start).total_seconds()
                logger.info(f"API call attempt {attempt + 1} completed in {call_time:.2f} seconds")
                
                # Parse response
                choice = response.choices[0]
                
                # Handle structured output vs regular response
                if use_structured_output and parsed_data:
                    # We already have parsed data from structured output
                    content = None  # No raw content for structured output
                    logger.info("Using structured output data (no raw JSON parsing needed)")
                else:
                    # Regular response - get content for JSON parsing
                    content = choice.message.content
                    content_length = len(content)
                    content_preview = content[:500] + "..." if len(content) > 500 else content
                    logger.info(f"API response - Length: {content_length} chars")
                    logger.info(f"API response - Preview (first 500 chars): {content_preview}")
                    # Log complete response at DEBUG level (saved to file)
                    logger.debug(f"API response - Complete response:\n{content}")
                    
                    # Save raw API response to file
                    if output_dir:
                        prompts_dir = output_dir / "prompts"
                        prompts_dir.mkdir(parents=True, exist_ok=True)
                        response_file = prompts_dir / "api_response_raw.txt"
                        with open(response_file, 'w', encoding='utf-8') as f:
                            f.write("=" * 80 + "\n")
                            f.write("RAW API RESPONSE\n")
                            f.write("=" * 80 + "\n\n")
                            f.write(content)
                        logger.info(f"Saved raw API response to {response_file}")
                
                # Extract logprobs if available
                # Note: Structured output may not support logprobs, but we'll try anyway
                logprobs_data = None
                if hasattr(choice, 'logprobs') and choice.logprobs:
                    try:
                        # Convert logprobs to serializable format
                        logprobs_data = {
                            "tokens": [],
                            "token_logprobs": [],
                            "top_logprobs": []
                        }
                        if hasattr(choice.logprobs, 'content'):
                            for item in choice.logprobs.content:
                                logprobs_data["tokens"].append(item.token if hasattr(item, 'token') else str(item))
                                logprobs_data["token_logprobs"].append(item.logprob if hasattr(item, 'logprob') else None)
                                if hasattr(item, 'top_logprobs') and item.top_logprobs:
                                    top_logprobs_list = []
                                    for top_logprob in item.top_logprobs:
                                        top_logprobs_list.append({
                                            "token": top_logprob.token if hasattr(top_logprob, 'token') else str(top_logprob),
                                            "logprob": top_logprob.logprob if hasattr(top_logprob, 'logprob') else None
                                        })
                                    logprobs_data["top_logprobs"].append(top_logprobs_list)
                                else:
                                    logprobs_data["top_logprobs"].append([])
                        logger.debug(f"Extracted logprobs with {len(logprobs_data.get('tokens', []))} tokens")
                    except Exception as e:
                        logger.warning(f"Failed to extract logprobs: {e}")
                        logprobs_data = None
                
                # Extract API metadata (works for both structured output and regular calls)
                from .models.perturbation import APIMetadata
                api_metadata_dict = {
                    "response_id": response.id,
                    "model": response.model,
                    "system_fingerprint": getattr(response, 'system_fingerprint', None),
                    "created": response.created,
                    "finish_reason": choice.finish_reason,
                }
                
                # Log token usage if available
                if hasattr(response, 'usage'):
                    usage = response.usage
                    api_metadata_dict["prompt_tokens"] = usage.prompt_tokens
                    api_metadata_dict["completion_tokens"] = usage.completion_tokens
                    api_metadata_dict["total_tokens"] = usage.total_tokens
                    
                    # Extract cached tokens if available
                    if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                        api_metadata_dict["cached_tokens"] = getattr(usage.prompt_tokens_details, 'cached_tokens', None)
                    
                    # Extract token breakdown by role if available
                    prompt_tokens_by_role = {}
                    if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                        if hasattr(usage.prompt_tokens_details, 'tokens_by_role'):
                            prompt_tokens_by_role = usage.prompt_tokens_details.tokens_by_role
                    if prompt_tokens_by_role:
                        api_metadata_dict["prompt_tokens_by_role"] = prompt_tokens_by_role
                    
                    logger.info(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
                    # Calculate cost estimate (approximate)
                    # GPT-4o pricing: $2.50/$10 per 1M tokens (input/output)
                    input_cost = (usage.prompt_tokens / 1_000_000) * 2.50
                    output_cost = (usage.completion_tokens / 1_000_000) * 10.00
                    total_cost = input_cost + output_cost
                    logger.info(f"Estimated cost: ${total_cost:.4f} (Input: ${input_cost:.4f}, Output: ${output_cost:.4f})")
                    logger.info(f"Finish reason: {choice.finish_reason}")
                
                api_metadata = APIMetadata.model_validate(api_metadata_dict) if any(api_metadata_dict.values()) else None
                
                # If we have structured output, use it directly
                if use_structured_output and parsed_data:
                    validated_mappings = []
                    for mapping in parsed_data.perturbations:
                        try:
                            # Convert structured mapping to regular mapping (add logprobs and metadata)
                            # Structured mapping doesn't have logprobs/metadata, so we add them here
                            mapping_dict = mapping.model_dump()
                            if logprobs_data:
                                mapping_dict["logprobs"] = logprobs_data
                            if api_metadata:
                                mapping_dict["api_metadata"] = api_metadata.model_dump()
                            # Convert to regular PerturbationMapping (allows extra fields)
                            validated_mappings.append(PerturbationMapping.model_validate(mapping_dict))
                        except ValidationError as e:
                            logger.warning(f"Failed to validate perturbation mapping from structured output: {e}. Skipping invalid mapping.")
                            continue
                    
                    logger.info(f"Successfully parsed and validated {len(validated_mappings)} perturbation mappings from structured output")
                    if logprobs_data:
                        logger.info(f"Logprobs included for {len(validated_mappings)} perturbations")
                    if api_metadata:
                        logger.info(f"API metadata included for {len(validated_mappings)} perturbations")
                    return validated_mappings
                
                # Fallback: Try to parse as JSON and convert to PerturbationMapping models
                if not content:
                    logger.error("No content available for JSON parsing fallback")
                    return []
                
                try:
                    # Clean content - remove markdown code blocks if present
                    content_clean = content.strip()
                    if content_clean.startswith('```'):
                        # Remove markdown code block markers
                        lines = content_clean.split('\n')
                        content_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else content_clean
                        content_clean = content_clean.strip()
                    
                    # Parse JSON with Pydantic-based error handling
                    parsed = None
                    try:
                        # First attempt: standard JSON parsing
                        parsed = json.loads(content_clean)
                    except json.JSONDecodeError as json_err:
                        # If parsing fails, try to repair JSON using a structured approach
                        logger.warning(f"Initial JSON parse failed: {json_err}. Attempting to repair JSON...")
                        
                        # First, fix word numbers (e.g., "fifty" -> 50)
                        try:
                            repaired_content = self._repair_json_word_numbers(content_clean)
                            # Then use a character-by-character state machine to properly handle
                            # JSON string boundaries and fix escape sequences
                            repaired_content = self._repair_json_escapes(repaired_content)
                            parsed = json.loads(repaired_content)
                            logger.info("Successfully parsed JSON after repair")
                        except Exception as repair_err:
                            logger.error(f"JSON repair failed: {repair_err}")
                            logger.error(f"Response content (first 1000 chars): {content_clean[:1000]}")
                            raise json_err
                    
                    # Extract array from response
                    mappings_list = None
                    if isinstance(parsed, dict):
                        # Check for common array keys
                        for key in ['mappings', 'perturbations', 'results', 'data', 'array']:
                            if key in parsed and isinstance(parsed[key], list):
                                mappings_list = parsed[key]
                                break
                        if mappings_list is None:
                            logger.warning(f"JSON response is a dict but no array found: {parsed}")
                            return []
                    elif isinstance(parsed, list):
                        mappings_list = parsed
                    else:
                        logger.warning(f"Unexpected JSON response type: {type(parsed)}")
                        return []
                    
                    # Convert to PerturbationMapping models
                    validated_mappings = []
                    for mapping_dict in mappings_list:
                        try:
                            # Add logprobs and API metadata to mapping if available
                            if logprobs_data:
                                mapping_dict["logprobs"] = logprobs_data
                            if api_metadata:
                                mapping_dict["api_metadata"] = api_metadata.model_dump()
                            validated_mappings.append(PerturbationMapping.model_validate(mapping_dict))
                        except ValidationError as e:
                            logger.warning(f"Failed to validate perturbation mapping: {e}. Skipping invalid mapping.")
                            continue
                    
                    logger.info(f"Successfully parsed and validated {len(validated_mappings)} perturbation mappings")
                    if logprobs_data:
                        logger.info(f"Logprobs included for {len(validated_mappings)} perturbations")
                    if api_metadata:
                        logger.info(f"API metadata included for {len(validated_mappings)} perturbations")
                    return validated_mappings
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content (first 500 chars): {content[:500]}")
                    # Try to extract valid JSON objects from the array even if some are malformed
                    # This is a last resort - try to parse individual objects
                    try:
                        # Try to extract and parse individual objects from the array
                        # Look for object patterns: { ... }
                        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                        matches = re.findall(object_pattern, content_clean, re.DOTALL)
                        if matches:
                            validated_mappings = []
                            for match in matches:
                                try:
                                    # Try to repair this individual object
                                    repaired_obj = self._repair_json_word_numbers(match)
                                    repaired_obj = self._repair_json_escapes(repaired_obj)
                                    obj_dict = json.loads(repaired_obj)
                                    validated_mappings.append(PerturbationMapping.model_validate(obj_dict))
                                except (json.JSONDecodeError, ValidationError) as obj_err:
                                    logger.debug(f"Skipping invalid object: {obj_err}")
                                    continue
                            
                            if validated_mappings:
                                logger.info(f"Extracted {len(validated_mappings)} valid objects from malformed JSON array")
                                return validated_mappings
                    except Exception as extract_err:
                        logger.debug(f"Failed to extract individual objects: {extract_err}")
                    
                    # Fallback: Try to extract JSON array from text
                    # Look for array pattern
                    array_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if array_match:
                        try:
                            # Try repairing the array
                            array_str = array_match.group(0)
                            repaired_array = self._repair_json_word_numbers(array_str)
                            repaired_array = self._repair_json_escapes(repaired_array)
                            parsed = json.loads(repaired_array)
                            if isinstance(parsed, list):
                                validated_mappings = []
                                for mapping_dict in parsed:
                                    try:
                                        validated_mappings.append(PerturbationMapping.model_validate(mapping_dict))
                                    except ValidationError:
                                        continue
                                return validated_mappings
                        except Exception as array_err:
                            logger.debug(f"Failed to parse array pattern: {array_err}")
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
        question_prompts: Dict[int, str],
        output_dir: Optional[Path] = None,
        question_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
        use_grouped_format: bool = True
    ) -> Dict[int, List[PerturbationMapping]]:
        """
        Generate perturbations for multiple questions in a single batch API call.
        
        Args:
            question_prompts: Dictionary mapping question_index to prompt string
            output_dir: Optional output directory to save prompt and response files
            question_metadata: Optional dictionary mapping question_index to metadata dict
                              with keys: question_type, latex_stem_text, copyable_text, 
                              gold_answer, options (for MCQ)
            use_grouped_format: If True, use grouped format (instructions once per type)
        
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
            
            # Save prompt for single question case
            if output_dir:
                prompts_dir = output_dir / "prompts"
                prompts_dir.mkdir(parents=True, exist_ok=True)
                prompt_file = prompts_dir / f"question_{question_idx}_prompt.txt"
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"QUESTION {question_idx} INDIVIDUAL PROMPT\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(prompt)
                logger.debug(f"Saved prompt for question {question_idx} to {prompt_file}")
            
            try:
                mappings = self._call_api_with_retry(prompt, output_dir=output_dir)
                batch_time = (datetime.now(tz) - batch_start).total_seconds()
                logger.info(f"Batch generation completed in {batch_time:.2f} seconds")
                logger.info(f"Generated {len(mappings)} perturbations for question {question_idx}")
                return {question_idx: mappings}
            except Exception as e:
                batch_time = (datetime.now(tz) - batch_start).total_seconds()
                logger.error(f"Failed to generate perturbations for question {question_idx} after {batch_time:.2f}s: {e}", exc_info=True)
                return {question_idx: []}
        
        # Use grouped format if metadata is available and flag is set
        if use_grouped_format and question_metadata:
            try:
                import importlib.util
                from pathlib import Path
                
                # Import grouped batch formatters using importlib
                # Use prompts folder from config (default: "grouped_batch_v2")
                prompts_dir = Path(__file__).parent.parent / "prompts" / self.grouped_prompts_folder
                mcq_spec = importlib.util.spec_from_file_location("mcq_grouped_prompt", prompts_dir / "mcq_grouped_prompt.py")
                tf_spec = importlib.util.spec_from_file_location("tf_grouped_prompt", prompts_dir / "tf_grouped_prompt.py")
                long_spec = importlib.util.spec_from_file_location("long_grouped_prompt", prompts_dir / "long_grouped_prompt.py")
                
                mcq_module = importlib.util.module_from_spec(mcq_spec)
                tf_module = importlib.util.module_from_spec(tf_spec)
                long_module = importlib.util.module_from_spec(long_spec)
                
                mcq_spec.loader.exec_module(mcq_module)
                tf_spec.loader.exec_module(tf_module)
                long_spec.loader.exec_module(long_module)
                
                # Handle function names - v2 folder may have _v2 suffix for some functions
                # Try _v2 version first, fall back to non-suffixed version
                format_grouped_mcq_batch = getattr(mcq_module, 'format_grouped_mcq_batch_v2', None)
                if format_grouped_mcq_batch is None:
                    format_grouped_mcq_batch = getattr(mcq_module, 'format_grouped_mcq_batch')
                
                format_grouped_tf_batch = getattr(tf_module, 'format_grouped_tf_batch_v2', None)
                if format_grouped_tf_batch is None:
                    format_grouped_tf_batch = getattr(tf_module, 'format_grouped_tf_batch')
                
                format_grouped_long_batch = getattr(long_module, 'format_grouped_long_batch_v2', None)
                if format_grouped_long_batch is None:
                    format_grouped_long_batch = getattr(long_module, 'format_grouped_long_batch')
                
                # Group questions by type
                from collections import defaultdict
                questions_by_type = defaultdict(list)
                
                question_indices = sorted(question_prompts.keys())
                for idx in question_indices:
                    if idx in question_metadata:
                        meta = question_metadata[idx]
                        q_type = meta.get('question_type', 'MCQ').upper()
                        questions_by_type[q_type].append({
                            'question_index': idx,
                            'latex_stem_text': meta.get('latex_stem_text', ''),
                            'copyable_text': meta.get('copyable_text', ''),
                            'gold_answer': meta.get('gold_answer', ''),
                            'options': meta.get('options', {})
                        })
                
                # Build grouped batch prompt sections
                batch_sections = []
                total_mappings = 0
                
                for q_type in sorted(questions_by_type.keys()):
                    type_questions = questions_by_type[q_type]
                    if q_type == 'MCQ':
                        section = format_grouped_mcq_batch(type_questions, k=self.mappings_per_question)
                        batch_sections.append(section)
                        total_mappings += len(type_questions) * self.mappings_per_question
                    elif q_type == 'TF':
                        section = format_grouped_tf_batch(type_questions, k=self.mappings_per_question)
                        batch_sections.append(section)
                        total_mappings += len(type_questions) * self.mappings_per_question
                    elif q_type == 'LONG':
                        section = format_grouped_long_batch(type_questions, k=self.mappings_per_question)
                        batch_sections.append(section)
                        total_mappings += len(type_questions) * self.mappings_per_question
                
                # Combine all sections with a final instruction
                batch_prompt = "\n\n".join(batch_sections) + f"""

## FINAL INSTRUCTIONS

CRITICAL: Return a SINGLE JSON array containing ALL mappings from ALL question types above.
- Total expected mappings: {total_mappings}
- Each mapping must have the correct question_index field
- Return ONLY valid JSON array, no markdown or additional text."""
                
                logger.info(f"Using grouped batch format: {len(questions_by_type)} question types, {len(question_prompts)} total questions")
                
            except ImportError as e:
                logger.warning(f"Failed to import grouped batch formatters: {e}. Falling back to individual format.")
                use_grouped_format = False
        
        # Fallback to original format if grouped format failed or not requested
        if not use_grouped_format or not question_metadata:
            # Combine all questions into a single batch prompt (original format)
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
            
            # Save complete batch prompt to file for inspection
            if output_dir:
                prompts_dir = output_dir / "prompts"
                prompts_dir.mkdir(parents=True, exist_ok=True)
                batch_prompt_file = prompts_dir / "batch_prompt_complete.txt"
                with open(batch_prompt_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("COMPLETE BATCH PROMPT SENT TO API\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(batch_prompt)
                logger.info(f"Saved complete batch prompt to {batch_prompt_file}")
            
            # Single API call for all questions
            all_mappings = self._call_api_with_retry(batch_prompt, output_dir=output_dir)
            
            # Parse and organize mappings by question index
            parse_start = datetime.now(tz)
            results = {}
            # Get question_indices from sorted question_prompts keys
            all_question_indices = sorted(question_prompts.keys())
            for idx in all_question_indices:
                results[idx] = []
            
            # Detailed logging for response parsing
            logger.info(f"Starting response parsing for {len(all_mappings) if isinstance(all_mappings, list) else 0} mappings")
            
            if isinstance(all_mappings, list):
                parsing_details = []
                for i, mapping in enumerate(all_mappings):
                    if isinstance(mapping, PerturbationMapping):
                        q_idx = mapping.question_index
                        parsing_details.append({
                            "mapping_index": i,
                            "question_index": q_idx,
                            "latex_stem_text": mapping.latex_stem_text[:100] + "..." if len(mapping.latex_stem_text) > 100 else mapping.latex_stem_text,
                            "original_substring": mapping.original_substring[:50] + "..." if len(mapping.original_substring) > 50 else mapping.original_substring,
                            "target_wrong_answer": mapping.target_wrong_answer
                        })
                        if q_idx in results:
                            results[q_idx].append(mapping)
                            logger.debug(f"Parsed mapping {i}: question_index={q_idx}, target_answer={mapping.target_wrong_answer}, original='{mapping.original_substring[:50]}...'")
                        else:
                            logger.warning(f"Parsed mapping {i}: question_index={q_idx} not in expected indices {all_question_indices}")
                    else:
                        logger.warning(f"Mapping {i} is not a PerturbationMapping instance: {type(mapping)}")
                
                # Save parsing details to file
                if output_dir:
                    prompts_dir = output_dir / "prompts"
                    parsing_file = prompts_dir / "response_parsing_details.json"
                    import json
                    with open(parsing_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "total_mappings_received": len(all_mappings),
                            "expected_questions": all_question_indices,
                            "parsing_details": parsing_details,
                            "results_summary": {idx: len(mappings) for idx, mappings in results.items()}
                        }, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved response parsing details to {parsing_file}")
            else:
                logger.error(f"Expected list of mappings, got {type(all_mappings)}")
            
            parse_time = (datetime.now(tz) - parse_start).total_seconds()
            total_mappings = sum(len(m) for m in results.values())
            logger.info(f"Parsed {total_mappings} total perturbations in {parse_time:.2f} seconds")
            for idx, mappings in results.items():
                logger.info(f"Question {idx}: {len(mappings)} perturbations assigned")
                logger.debug(f"Question {idx}: {len(mappings)} perturbations")
                # Log first perturbation details for each question
                if mappings:
                    first_pert = mappings[0]
                    logger.debug(f"Question {idx} - First perturbation: latex_stem_text='{first_pert.latex_stem_text[:100]}...', original='{first_pert.original_substring[:50]}...'")
            
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
                    ]
                }
                
                # GPT-5.1 models use different parameters
                # Note: Current OpenAI Python SDK doesn't support reasoning/verbosity parameters yet
                # The model will work without them (using defaults)
                # TODO: Add these parameters when SDK is updated to support them
                if self._is_gpt5_model():
                    # For now, don't pass reasoning/verbosity as SDK doesn't support them
                    # When SDK is updated, uncomment these lines:
                    # if self.reasoning_effort is not None:
                    #     body["reasoning"] = {"effort": self.reasoning_effort}
                    # if self.verbosity is not None:
                    #     body["verbosity"] = self.verbosity
                    pass
                else:
                    # Use traditional parameters for non-GPT-5 models
                    body["temperature"] = self.temperature
                    # Add optional parameters if set
                    if self.top_p is not None:
                        body["top_p"] = self.top_p
                    if self.frequency_penalty is not None:
                        body["frequency_penalty"] = self.frequency_penalty
                    if self.presence_penalty is not None:
                        body["presence_penalty"] = self.presence_penalty
                    if self.max_tokens is not None:
                        body["max_tokens"] = self.max_tokens
                    # Add logprobs if enabled
                    if self.logprobs:
                        body["logprobs"] = True
                        if self.top_logprobs is not None:
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
    
    def check_batch_status(self, batch_id: str) -> BatchStatus:
        """
        Check the status of a batch.
        
        Args:
            batch_id: Batch ID from OpenAI
        
        Returns:
            Batch status information
        """
        try:
            batch = self.client.batches.retrieve(batch_id)
            request_counts = {}
            if hasattr(batch, 'request_counts'):
                request_counts = {
                    "total": batch.request_counts.total if hasattr(batch.request_counts, 'total') else None,
                    "completed": batch.request_counts.completed if hasattr(batch.request_counts, 'completed') else None,
                    "failed": batch.request_counts.failed if hasattr(batch.request_counts, 'failed') else None
                }
            return BatchStatus(
                id=batch.id,
                status=batch.status,
                request_counts=request_counts,
                output_file_id=batch.output_file_id if hasattr(batch, 'output_file_id') else None,
                error_file_id=batch.error_file_id if hasattr(batch, 'error_file_id') else None
            )
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
    
    def parse_batch_results(self, results_file_path: Path) -> Dict[int, List[PerturbationMapping]]:
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
                        
                        # Extract content and logprobs from response
                        choice = response_body.get('choices', [{}])[0]
                        content = choice.get('message', {}).get('content', '')
                        if not content:
                            logger.warning(f"No content in response for question {question_idx}")
                            results[question_idx] = []
                            continue
                        
                        # Extract logprobs if available
                        logprobs_data = None
                        if 'logprobs' in choice and choice['logprobs']:
                            try:
                                logprobs_obj = choice['logprobs']
                                logprobs_data = {
                                    "tokens": [],
                                    "token_logprobs": [],
                                    "top_logprobs": []
                                }
                                if 'content' in logprobs_obj:
                                    for item in logprobs_obj['content']:
                                        logprobs_data["tokens"].append(item.get('token', ''))
                                        logprobs_data["token_logprobs"].append(item.get('logprob'))
                                        if 'top_logprobs' in item and item['top_logprobs']:
                                            top_logprobs_list = []
                                            for top_logprob in item['top_logprobs']:
                                                top_logprobs_list.append({
                                                    "token": top_logprob.get('token', ''),
                                                    "logprob": top_logprob.get('logprob')
                                                })
                                            logprobs_data["top_logprobs"].append(top_logprobs_list)
                                        else:
                                            logprobs_data["top_logprobs"].append([])
                                logger.debug(f"Extracted logprobs for question {question_idx} with {len(logprobs_data.get('tokens', []))} tokens")
                            except Exception as e:
                                logger.warning(f"Failed to extract logprobs for question {question_idx}: {e}")
                                logprobs_data = None
                        
                        # Extract API metadata from batch response
                        from .models.perturbation import APIMetadata
                        api_metadata_dict = {
                            "response_id": response_body.get('id'),
                            "model": response_body.get('model'),
                            "system_fingerprint": response_body.get('system_fingerprint'),
                            "created": response_body.get('created'),
                            "finish_reason": choice.get('finish_reason'),
                        }
                        
                        # Extract usage information
                        if 'usage' in response_body:
                            usage = response_body['usage']
                            api_metadata_dict["prompt_tokens"] = usage.get('prompt_tokens')
                            api_metadata_dict["completion_tokens"] = usage.get('completion_tokens')
                            api_metadata_dict["total_tokens"] = usage.get('total_tokens')
                            
                            # Extract cached tokens if available
                            if 'prompt_tokens_details' in usage:
                                prompt_details = usage['prompt_tokens_details']
                                api_metadata_dict["cached_tokens"] = prompt_details.get('cached_tokens')
                                if 'tokens_by_role' in prompt_details:
                                    api_metadata_dict["prompt_tokens_by_role"] = prompt_details['tokens_by_role']
                        
                        api_metadata = APIMetadata.model_validate(api_metadata_dict) if any(api_metadata_dict.values()) else None
                        
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
                            
                            # Extract array from response
                            mappings_list = None
                            if isinstance(parsed, dict):
                                for key in ['mappings', 'perturbations', 'results', 'data', 'array']:
                                    if key in parsed and isinstance(parsed[key], list):
                                        mappings_list = parsed[key]
                                        break
                                if mappings_list is None:
                                    logger.warning(f"No array found in response for question {question_idx}")
                                    results[question_idx] = []
                                    continue
                            elif isinstance(parsed, list):
                                mappings_list = parsed
                            else:
                                logger.warning(f"Unexpected response type for question {question_idx}: {type(parsed)}")
                                results[question_idx] = []
                                continue
                            
                            # Convert to PerturbationMapping models
                            validated_mappings = []
                            for mapping_dict in mappings_list:
                                try:
                                    # Add logprobs and API metadata to mapping if available
                                    if logprobs_data:
                                        mapping_dict["logprobs"] = logprobs_data
                                    if api_metadata:
                                        mapping_dict["api_metadata"] = api_metadata.model_dump()
                                    validated_mappings.append(PerturbationMapping.model_validate(mapping_dict))
                                except ValidationError as e:
                                    logger.warning(f"Failed to validate perturbation mapping for question {question_idx}: {e}")
                                    continue
                            results[question_idx] = validated_mappings
                            if logprobs_data:
                                logger.info(f"Logprobs included for {len(validated_mappings)} perturbations in question {question_idx}")
                            if api_metadata:
                                logger.info(f"API metadata included for {len(validated_mappings)} perturbations in question {question_idx}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON for question {question_idx}: {e}")
                            # Try to extract JSON array from text
                            array_match = re.search(r'\[.*\]', content, re.DOTALL)
                            if array_match:
                                try:
                                    parsed = json.loads(array_match.group(0))
                                    if isinstance(parsed, list):
                                        validated_mappings = []
                                        for mapping_dict in parsed:
                                            try:
                                                validated_mappings.append(PerturbationMapping.model_validate(mapping_dict))
                                            except ValidationError:
                                                continue
                                        results[question_idx] = validated_mappings
                                    else:
                                        results[question_idx] = []
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
    
    def _repair_json_word_numbers(self, json_str: str) -> str:
        """
        Repair JSON by converting word numbers to numeric values.
        
        This handles cases where the model outputs words like "fifty" instead of 50.
        Only converts words that appear in numeric contexts (after colons, before commas).
        
        Args:
            json_str: The JSON string to repair
            
        Returns:
            Repaired JSON string with word numbers converted
        """
        # Dictionary mapping word numbers to their numeric values
        word_to_number = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
            'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
            'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
        }
        
        # Pattern to match word numbers in numeric contexts
        # Look for: ": word," or ": word\n" or ": word}" where word is a number word
        import re
        
        # Create a pattern that matches word numbers after colons (in value positions)
        # but not inside string values
        result = []
        i = 0
        in_string = False
        
        while i < len(json_str):
            char = json_str[i]
            
            # Track string boundaries
            if char == '"':
                # Check if quote is escaped
                backslash_count = 0
                j = i - 1
                while j >= 0 and json_str[j] == '\\':
                    backslash_count += 1
                    j -= 1
                
                if backslash_count % 2 == 0:
                    in_string = not in_string
                
                result.append(char)
                i += 1
                continue
            
            # Only process outside of strings
            if not in_string:
                # Look for pattern: ": word" where word might be a number word
                # Check if we're at ":" followed by whitespace and a potential word number
                if char == ':' and i + 1 < len(json_str):
                    # Look ahead to find the next word
                    # Skip whitespace after colon
                    j = i + 1
                    while j < len(json_str) and json_str[j] in ' \t\n':
                        j += 1
                    
                    # Extract potential word (until comma, newline, closing brace, bracket, or space)
                    word_start = j
                    while j < len(json_str) and json_str[j] not in ',}\n\r\t] ':
                        j += 1
                    
                    word = json_str[word_start:j].strip().lower()
                    
                    # Check if it's a number word
                    if word in word_to_number:
                        # Replace the word with its numeric value
                        result.append(json_str[i:word_start])  # Include ": " and any extra spaces
                        result.append(word_to_number[word])
                        i = j  # Skip past the word
                        continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    def _repair_json_escapes(self, json_str: str) -> str:
        """
        Repair JSON with unescaped backslashes using a state machine approach.
        
        This method properly handles JSON string boundaries and fixes escape sequences
        like \_ (invalid in JSON) to \\_ (valid in JSON) without using regex.
        
        Uses a character-by-character state machine that respects JSON string boundaries.
        
        Args:
            json_str: The JSON string to repair
            
        Returns:
            Repaired JSON string
        """
        result = []
        i = 0
        in_string = False
        
        while i < len(json_str):
            char = json_str[i]
            
            if char == '"':
                # Check if this quote is escaped
                # Count backslashes before the quote
                backslash_count = 0
                j = i - 1
                while j >= 0 and json_str[j] == '\\':
                    backslash_count += 1
                    j -= 1
                
                # If even number of backslashes (or zero), quote is not escaped
                if backslash_count % 2 == 0:
                    in_string = not in_string
                
                result.append(char)
                i += 1
                
            elif char == '\\' and in_string:
                # We're inside a string and found a backslash
                # Check what comes after it
                if i + 1 >= len(json_str):
                    # Trailing backslash - escape it
                    result.append('\\\\')
                    i += 1
                    continue
                
                next_char = json_str[i + 1]
                # Valid JSON escapes: ", \, /, b, f, n, r, t, u
                valid_escapes = {'"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'}
                
                if next_char == 'u':
                    # Unicode escape: \uXXXX
                    if i + 5 < len(json_str):
                        hex_chars = json_str[i+2:i+6]
                        if all(c in '0123456789abcdefABCDEF' for c in hex_chars):
                            # Valid unicode escape
                            result.append('\\u' + hex_chars)
                            i += 6
                            continue
                    # Invalid unicode escape - escape the backslash
                    result.append('\\\\')
                    i += 1
                    # Process next_char normally
                    continue
                elif next_char in valid_escapes:
                    # Valid escape sequence - keep as is
                    result.append('\\' + next_char)
                    i += 2
                    continue
                else:
                    # Invalid escape (like \_) - escape the backslash
                    result.append('\\\\')
                    i += 1
                    # Process next_char normally in next iteration
                    continue
            else:
                # Normal character
                result.append(char)
                i += 1
        
        return ''.join(result)

