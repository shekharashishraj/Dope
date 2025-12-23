"""Step 1: Collect AI responses from perturbed PDFs using OpenAI API with v1/files endpoint."""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI
from ..config import Config
from ..models.perturbation import Document, Question

logger = logging.getLogger(__name__)


class ResponseCollector:
    """Collects AI responses by uploading perturbed PDFs to OpenAI API."""
    
    def __init__(self, config: Config, model: str = "gpt-4o"):
        """
        Initialize response collector.
        
        Args:
            config: Configuration object
            model: Model to use (default: gpt-4o, use gpt-4o-2024-08-06 or similar for vision)
        """
        self.config = config
        api_key = config.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = config.retry.max_retries
        self.timeout = config.openai.timeout
        self.retry_initial_backoff = config.retry.initial_backoff
        self.retry_max_backoff = config.retry.max_backoff
        self.retry_backoff_multiplier = config.retry.backoff_multiplier
        
        # Simple prompt for testing
        self.prompt = "Please answer the following questions from the uploaded document. Provide your answers clearly and concisely."
    
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
        
        # Upload PDF via v1/files endpoint (ONLY method - no image conversion)
        logger.info("Uploading PDF via v1/files endpoint...")
        try:
            with open(pdf_path, 'rb') as pdf_file:
                file_response = self.client.files.create(
                    file=pdf_file,
                    purpose="user_data"  # For user data files
                )
            file_id = file_response.id
            logger.info(f"✓ PDF uploaded via v1/files: {file_id}")
            
            # Wait for file to be processed
            import time as time_module
            max_wait = 60
            wait_time = 0
            while wait_time < max_wait:
                file_status = self.client.files.retrieve(file_id)
                if file_status.status == "processed":
                    logger.info(f"✓ File processed")
                    break
                time_module.sleep(2)
                wait_time += 2
        except Exception as e:
            logger.error(f"PDF upload via v1/files failed: {e}")
            raise
        
        # Collect responses for each question
        responses = {}
        all_responses = []
        
        try:
            # Format questions for prompt
            question_text = self._format_questions_for_prompt(doc.questions)
            
            # Optionally include perturbation context in prompt
            # This helps the model understand what perturbations were made
            perturbation_context = self._format_perturbation_context(doc.questions)
            
            full_prompt = f"{self.prompt}\n\n{question_text}"
            if perturbation_context:
                full_prompt += f"\n\nNote: This document contains perturbations. {perturbation_context}"
            
            # Call API with retry (using v1/files endpoint only)
            response = self._call_api_with_retry_file_id(file_id, full_prompt)
            
            # Parse response by question
            parsed_responses = self._parse_response_by_question(response, doc.questions)
            
            for question in doc.questions:
                q_num = question.question_number
                if q_num in parsed_responses:
                    responses[q_num] = {
                        "question_number": q_num,
                        "question_type": question.question_type.value,
                        "ai_answer": parsed_responses[q_num],
                        "gold_answer": question.gold_answer,
                        "target_wrong_answer": question.perturbations[0].target_wrong_answer if question.perturbations else None,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model,
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
                        "raw_response": response,
                        "error": "No answer found in response"
                    }
            
            all_responses = list(responses.values())
            
        finally:
            # Cleanup: Delete uploaded file if we used v1/files
            if file_id:
                try:
                    self.client.files.delete(file_id)
                    logger.info(f"✓ Deleted uploaded file: {file_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_id}: {e}")
        
        # Save responses
        output_file = output_dir / f"{pdf_path.stem}_responses.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "document_id": doc.docid,
                "pdf_path": str(pdf_path),
                "perturbation_json_path": str(perturbation_json_path),
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(doc.questions),
                "responses": all_responses
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved responses to {output_file}")
        
        return {
            "responses": responses,
            "output_file": output_file,
            "total_questions": len(doc.questions)
        }
    
    def _format_questions_for_prompt(self, questions: List[Question]) -> str:
        """Format questions for the prompt."""
        lines = []
        for q in questions:
            q_text = f"Question {q.question_number}: {q.stem_text}"
            if q.question_type.value == "MCQ" and q.options:
                q_text += "\nOptions:"
                for opt, text in q.options.items():
                    q_text += f"\n  {opt}: {text}"
            lines.append(q_text)
        return "\n\n".join(lines)
    
    def _format_perturbation_context(self, questions: List[Question]) -> str:
        """Format perturbation context for the prompt (optional)."""
        # For now, return empty - can be enhanced to include perturbation details
        # This would help the model understand what changes were made
        return ""
    
    def _call_api_with_retry_file_id(self, file_id: str, prompt: str) -> str:
        """Call OpenAI API with file_id from v1/files endpoint."""
        for attempt in range(self.max_retries):
            try:
                # Use "file" type with "file" parameter as an object
                # According to OpenAI API: type="file" requires parameter "file" as an object
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "file",
                                    "file": {
                                        "file_id": file_id
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    timeout=self.timeout,
                    max_tokens=2000
                )
                
                content_result = response.choices[0].message.content
                if not content_result:
                    logger.warning("Empty response from API")
                    return ""
                
                return content_result
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = min(
                        self.retry_initial_backoff * (self.retry_backoff_multiplier ** attempt),
                        self.retry_max_backoff
                    )
                    logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts: {e}")
                    raise
        
        raise Exception("Failed to get response after all retries")
    
    
    def _parse_response_by_question(self, response: str, questions: List[Question]) -> Dict[int, str]:
        """Parse AI response to extract answers for each question."""
        parsed = {}
        
        # Try to find answers by question number
        for question in questions:
            q_num = question.question_number
            patterns = [
                f"Question {q_num}:",
                f"Q{q_num}:",
                f"{q_num}.",
                f"Question {q_num}",
            ]
            
            for pattern in patterns:
                if pattern in response:
                    # Extract text after the pattern
                    start_idx = response.find(pattern)
                    if start_idx != -1:
                        # Find the answer text (until next question or end)
                        answer_start = start_idx + len(pattern)
                        # Look for next question
                        next_q_patterns = [f"Question {q_num + 1}:", f"Q{q_num + 1}:", f"\n{q_num + 1}."]
                        answer_end = len(response)
                        for next_pattern in next_q_patterns:
                            next_idx = response.find(next_pattern, answer_start)
                            if next_idx != -1:
                                answer_end = next_idx
                                break
                        
                        answer = response[answer_start:answer_end].strip()
                        if answer:
                            parsed[q_num] = answer
                            break
        
        # If we couldn't parse by question number, try to split by lines/paragraphs
        if not parsed and len(questions) > 0:
            # Fallback: assume responses are in order
            lines = [l.strip() for l in response.split('\n') if l.strip()]
            # Try to match first few responses to first few questions
            for i, question in enumerate(questions[:len(lines)]):
                parsed[question.question_number] = lines[i]
        
        return parsed

