"""Anthropic Claude API response collector for PDF evaluation."""
import json
import base64
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from anthropic import Anthropic
from ..config import Config
from ..models.perturbation import Document, Question
from ..models.ai_response import AIResponse, QuestionAnswer

logger = logging.getLogger(__name__)


class AnthropicResponseCollector:
    """Collects AI responses by uploading PDFs to Anthropic Claude API."""
    
    def __init__(self, config: Config, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Anthropic response collector.
        
        Args:
            config: Configuration object
            model: Claude model to use
        """
        self.config = config
        # Get API key from environment (Anthropic API key is typically in env, not config)
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Try to get from config if it exists
            if hasattr(config, 'anthropic') and hasattr(config.anthropic, 'api_key') and config.anthropic.api_key:
                api_key = config.anthropic.api_key
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = config.retry.max_retries
        self.timeout = config.anthropic.timeout if hasattr(config, 'anthropic') else 120
        self.retry_initial_backoff = config.retry.initial_backoff
        self.retry_max_backoff = config.retry.max_backoff
        self.retry_backoff_multiplier = config.retry.backoff_multiplier
        self.temperature = config.anthropic.temperature if hasattr(config, 'anthropic') else 0.2
        self.max_tokens = config.anthropic.max_tokens if hasattr(config, 'anthropic') else None
        self.document_media_type = config.anthropic.document_media_type if hasattr(config, 'anthropic') else "application/pdf"
        self.system_message = config.prompts.system_message if hasattr(config, 'prompts') else "You are a helpful assistant."
        
        # Simple prompt - only PDF, no question text
        self.prompt = "Please read this document and answer ALL questions that appear in it. For each question, provide the question number and your answer."
    
    def collect_responses(
        self,
        pdf_path: Path,
        perturbation_json_path: Path,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Upload PDF, collect responses for all questions.
        
        Args:
            pdf_path: Path to perturbed PDF file
            perturbation_json_path: Path to perturbation JSON file
            output_dir: Directory to save responses
        
        Returns:
            Dictionary with responses and metadata
        """
        # Load perturbation data to get question structure
        with open(perturbation_json_path, 'r', encoding='utf-8') as f:
            perturbation_data = json.load(f)
        
        doc = Document.model_validate(perturbation_data)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Collecting responses for {pdf_path.name} with {len(doc.questions)} questions")
        
        # Read and encode PDF as base64
        logger.info("Encoding PDF as base64...")
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
            logger.info(f"✓ PDF encoded ({len(pdf_data)} chars base64)")
        except Exception as e:
            logger.error(f"PDF encoding failed: {e}")
            raise
        
        # Collect responses for all questions
        responses = {}
        all_responses = []
        
        try:
            # Call API with retry
            response = self._call_api_with_retry_pdf(pdf_data, self.prompt)
            
            # Parse response by question - try LLM judge first, fallback to regex
            parsed_responses, parsing_method = self._parse_response_with_llm_judge(response, doc.questions)
            
            for question in doc.questions:
                q_num = question.question_number
                if q_num in parsed_responses:
                    parsed_data = parsed_responses[q_num]
                    # Handle both old format (string) and new format (dict)
                    if isinstance(parsed_data, dict):
                        ai_answer = parsed_data.get("answer")
                        extracted_option = parsed_data.get("extracted_option")
                    else:
                        ai_answer = parsed_data
                        extracted_option = None
                    
                    responses[q_num] = {
                        "question_number": q_num,
                        "question_type": question.question_type.value,
                        "ai_answer": ai_answer,
                        "extracted_option": extracted_option,
                        "gold_answer": question.gold_answer,
                        "target_wrong_answer": question.perturbations[0].target_wrong_answer if question.perturbations else None,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model,
                        "parsing_method": parsing_method,
                        "raw_response": response
                    }
                else:
                    # No answer found for this question
                    responses[q_num] = {
                        "question_number": q_num,
                        "question_type": question.question_type.value,
                        "ai_answer": None,
                        "gold_answer": question.gold_answer,
                        "target_wrong_answer": question.perturbations[0].target_wrong_answer if question.perturbations else None,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model,
                        "parsing_method": parsing_method,
                        "raw_response": response,
                        "error": "No answer found in response"
                    }
            
            all_responses.extend(responses.values())
            
        except Exception as e:
            logger.error(f"Error collecting responses: {e}", exc_info=True)
            raise
        
        # Save responses
        output_file = output_dir / f"{pdf_path.stem}_responses.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "pdf_path": str(pdf_path),
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "responses": responses
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved responses to {output_file}")
        
        return {
            "responses": responses,
            "output_file": output_file,
            "total_questions": len(doc.questions)
        }
    
    def _call_api_with_retry_pdf(self, pdf_data: str, prompt: str) -> str:
        """Call Anthropic API with base64-encoded PDF."""
        for attempt in range(self.max_retries):
            try:
                # Build content array with PDF document
                content = [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": self.document_media_type,
                            "data": pdf_data
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
                
                # Build API parameters
                api_params = {
                    "model": self.model,
                    "max_tokens": self.max_tokens or 4096,
                    "temperature": self.temperature,
                    "system": self.system_message,
                    "messages": [{"role": "user", "content": content}]
                }
                
                logger.info(f"Calling Anthropic API (attempt {attempt + 1}/{self.max_retries})...")
                response = self.client.messages.create(**api_params)
                
                # Extract text from response
                if response.content and len(response.content) > 0:
                    response_text = response.content[0].text
                    logger.info(f"✓ API call successful, response length: {len(response_text)} chars")
                    return response_text
                else:
                    logger.warning("Empty response from API")
                    return ""
                
            except Exception as e:
                error_msg = f"API call attempt {attempt + 1} failed: {type(e).__name__}: {e}"
                logger.warning(error_msg)
                
                if attempt < self.max_retries - 1:
                    # Calculate backoff
                    backoff_time = min(
                        self.retry_initial_backoff * (self.retry_backoff_multiplier ** attempt),
                        self.retry_max_backoff
                    )
                    logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise e
        
        return ""
    
    def _parse_response_with_llm_judge(
        self, 
        response_text: str, 
        questions: List[Question]
    ) -> Tuple[Dict[int, Any], str]:
        """
        Parse response using LLM judge (call Anthropic to parse) with fallback to regex.
        
        Args:
            response_text: Raw response text from API
            questions: List of questions to extract answers for
        
        Returns:
            Tuple of (parsed_responses dict, parsing_method string)
        """
        question_numbers = [q.question_number for q in questions]
        question_types = {q.question_number: q.question_type.value for q in questions}
        
        # Try LLM judge: call Anthropic to parse the response into structured format
        try:
            extraction_prompt = f"""Extract all question answers from the following AI response and return as JSON.

Expected question numbers: {question_numbers}

AI Response:
{response_text}

Extract each question number and its corresponding answer. For MCQ questions, also extract the option letter (A, B, C, D, or E) from the answer text. For example:
- If answer is "(b) Metasploit", extract option "B"
- If answer is "A", extract option "A"  
- If answer is "Option C", extract option "C"
- For non-MCQ questions, leave extracted_option as null

Return JSON in this format:
{{
  "answers": [
    {{"question_number": 1, "answer": "...", "extracted_option": "B"}},
    {{"question_number": 2, "answer": "...", "extracted_option": null}}
  ]
}}"""

            parse_response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.0,  # Use low temperature for parsing
                system="You are a precise parser that extracts question-answer pairs from text. Return only valid JSON.",
                messages=[{"role": "user", "content": extraction_prompt}]
            )
            
            if parse_response.content and len(parse_response.content) > 0:
                parse_text = parse_response.content[0].text
                # Extract JSON from response (might be wrapped in markdown)
                import re
                json_match = re.search(r'\{.*\}', parse_text, re.DOTALL)
                if json_match:
                    parse_text = json_match.group(0)
                
                parsed_data = json.loads(parse_text)
                if "answers" in parsed_data:
                    result = {}
                    for qa in parsed_data["answers"]:
                        q_num = qa.get("question_number")
                        if q_num:
                            result[q_num] = {
                                "answer": qa.get("answer"),
                                "extracted_option": qa.get("extracted_option")
                            }
                    logger.info("✓ Parsed response using LLM judge")
                    return result, "llm_judge"
        except Exception as e:
            logger.warning(f"LLM judge parsing failed, trying regex fallback: {e}")
        
        # Fallback to regex
        return self._parse_response_with_regex(response_text, questions)
    
    def _parse_response_with_regex(
        self, 
        response_text: str, 
        questions: List[Question]
    ) -> Tuple[Dict[int, Any], str]:
        """
        Parse response using regex patterns.
        
        Args:
            response_text: Raw response text from API
            questions: List of questions to extract answers for
        
        Returns:
            Tuple of (parsed_responses dict, parsing_method string)
        """
        import re
        
        parsed = {}
        response_lower = response_text.lower()
        
        for question in questions:
            q_num = question.question_number
            question_type = question.question_type.value
            
            # Try to find answer for this question number
            # Pattern: "Question X" or "Q X" or "X." followed by answer
            patterns = [
                rf"(?:question|q)\s*{q_num}[:\s]+(.*?)(?=(?:question|q)\s*\d+|$)",
                rf"{q_num}[\.:]\s*(.*?)(?=\d+[\.:]|$)",
                rf"question\s*{q_num}[:\s]+(.*?)(?=question\s*\d+|$)",
            ]
            
            answer = None
            extracted_option = None
            
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    answer = match.group(1).strip()
                    # Clean up answer
                    answer = re.sub(r'\s+', ' ', answer)
                    if answer:
                        # For MCQ, try to extract option letter
                        if question_type == "MCQ":
                            option_match = re.search(r'\b([A-E])\b', answer, re.IGNORECASE)
                            if option_match:
                                extracted_option = option_match.group(1).upper()
                        break
            
            if answer:
                parsed[q_num] = {
                    "answer": answer,
                    "extracted_option": extracted_option
                }
        
        return parsed, "regex"
