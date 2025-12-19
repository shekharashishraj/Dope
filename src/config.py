"""Configuration management for IntegrityShield pipeline."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for the pipeline."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._load_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            # Return default config if file doesn't exist
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Deep merge with defaults
        default = self._get_default_config()
        return self._deep_merge(default, config)
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "openai": {
                "model": "gpt-4o",
                "batch_size": 5,
                "max_retries": 3,
                "timeout": 120,
                "temperature": 0.5,
                "top_p": None,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "max_tokens": None,
                "logprobs_enabled": False,
                "top_logprobs": 5
            },
            "processing": {
                "input_dir": "output",
                "output_suffix": "_perturbation",
                "resume": True,
                "mappings_per_question": 3,
                "use_organized_structure": True,
                "output_base_dir": "output_perturbation",
                "shared_timestamp": True
            },
            "retry": {
                "max_retries": 3,
                "initial_backoff": 1.0,
                "max_backoff": 60.0,
                "backoff_multiplier": 2.0,
                "retry_on_rate_limit": True,
                "retry_on_timeout": True,
                "retry_on_connection_error": True
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "console_level": "INFO",
                "file_level": "DEBUG",
                "log_dir": "logs",
                "timezone": "America/Denver",
                "max_bytes": 10485760,
                "backup_count": 5,
                "log_complete_prompts": True,
                "log_complete_responses": True,
                "log_token_usage": True,
                "log_timing": True
            },
            "batch_api": {
                "enabled": True,
                "completion_window": "24h",
                "auto_fallback": True,
                "check_interval": 300,
                "max_wait_time": None
            },
            "injection": {
                "default_methods": ["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"],
                "methods": {
                    "icw": {"enabled": True, "use_first_perturbation_only": False},
                    "dual_layer": {"enabled": True, "use_first_perturbation_only": True},
                    "font_attack": {"enabled": True, "base_font_path": None, "fonts_dir": None, "generate_all_perturbations": True},
                    "icw_dual_layer": {"enabled": True},
                    "icw_font_attack": {"enabled": True}
                }
            },
            "pdf_generation": {
                "enabled": True,
                "compile_pdf": True,
                "output_base_dir": "output_attacked_pdfs",
                "latex_compiler": "auto",
                "require_xetex_for_fonts": True,
                "compilation_timeout": 300,
                "cleanup_fonts_after_compile": True,
                "cleanup_temp_files": True,
                "apply_pdf_overlay": True,
                "overlay_search_original_pdf": True
            },
            "prompts": {
                "mcq": {"include_reasoning": False, "include_answer_guidance": False, "prefix_note": "", "retry_instructions": ""},
                "tf": {"include_reasoning": False, "include_answer_guidance": False, "prefix_note": "", "retry_instructions": ""},
                "long": {"include_reasoning": False, "include_answer_guidance": False, "prefix_note": "", "retry_instructions": ""},
                "system_message": "You are a helpful assistant that generates JSON array responses. Always return valid JSON arrays.",
                "json_format_strict": True
            },
            "performance": {
                "delay_between_requests": 0.0,
                "delay_between_documents": 0.0,
                "delay_on_rate_limit": 1.0,
                "max_concurrent_requests": 1,
                "max_concurrent_documents": 1
            },
            "experimental": {
                "icw_use_replacement_for_long": True,
                "icw_use_target_wrong_for_mcq": True,
                "dual_layer_allow_multiple_perturbations": False,
                "font_attack_cleanup_after_compile": True,
                "include_metadata_in_output": True,
                "include_timing_in_output": True,
                "include_cost_estimates_in_output": True
            },
            "paths": {
                "base_font": "fonts/Roboto-Regular.ttf",
                "latex_compiler_path": None,
                "output_perturbation": "output_perturbation",
                "output_pdfs": "output_attacked_pdfs",
                "logs": "logs",
                "temp": None
            },
            "validation": {
                "validate_perturbations": True,
                "validate_latex_paths": True,
                "validate_question_numbers": True,
                "min_perturbations_per_question": 1,
                "max_perturbations_per_question": 10,
                "require_replacement_substring": True,
                "require_original_substring": True
            }
        }
    
    def _load_env_overrides(self):
        """Override config with environment variables if present."""
        # OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            if "openai" not in self.config:
                self.config["openai"] = {}
            self.config["openai"]["api_key"] = api_key
        
        # Override batch size if set
        batch_size = os.getenv("BATCH_SIZE")
        if batch_size:
            self.config["openai"]["batch_size"] = int(batch_size)
    
    # OpenAI properties
    @property
    def openai_model(self) -> str:
        """Get OpenAI model name."""
        return self.config.get("openai", {}).get("model", "gpt-4o")
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key."""
        return self.config.get("openai", {}).get("api_key") or os.getenv("OPENAI_API_KEY", "")
    
    @property
    def batch_size(self) -> int:
        """Get batch size (number of documents per batch)."""
        return self.config.get("openai", {}).get("batch_size", 5)
    
    @property
    def max_retries(self) -> int:
        """Get maximum number of retries."""
        return self.config.get("openai", {}).get("max_retries", 3)
    
    @property
    def timeout(self) -> int:
        """Get timeout in seconds."""
        return self.config.get("openai", {}).get("timeout", 120)
    
    @property
    def temperature(self) -> float:
        """Get temperature for API calls."""
        return self.config.get("openai", {}).get("temperature", 0.5)
    
    @property
    def top_p(self) -> Optional[float]:
        """Get top_p parameter."""
        return self.config.get("openai", {}).get("top_p")
    
    @property
    def frequency_penalty(self) -> float:
        """Get frequency penalty."""
        return self.config.get("openai", {}).get("frequency_penalty", 0.0)
    
    @property
    def presence_penalty(self) -> float:
        """Get presence penalty."""
        return self.config.get("openai", {}).get("presence_penalty", 0.0)
    
    @property
    def max_tokens(self) -> Optional[int]:
        """Get max tokens limit."""
        return self.config.get("openai", {}).get("max_tokens")
    
    @property
    def logprobs_enabled(self) -> bool:
        """Get whether to enable log probabilities."""
        return self.config.get("openai", {}).get("logprobs_enabled", False)
    
    @property
    def top_logprobs(self) -> int:
        """Get number of top log probabilities to return."""
        return self.config.get("openai", {}).get("top_logprobs", 5)
    
    # Processing properties
    @property
    def input_dir(self) -> str:
        """Get input directory."""
        return self.config.get("processing", {}).get("input_dir", "output")
    
    @property
    def output_suffix(self) -> str:
        """Get output suffix."""
        return self.config.get("processing", {}).get("output_suffix", "_perturbation")
    
    @property
    def resume(self) -> bool:
        """Get resume flag."""
        return self.config.get("processing", {}).get("resume", True)
    
    @property
    def mappings_per_question(self) -> int:
        """Get number of mappings to generate per question."""
        return self.config.get("processing", {}).get("mappings_per_question", 3)
    
    @property
    def use_organized_structure(self) -> bool:
        """Get whether to use organized output structure."""
        return self.config.get("processing", {}).get("use_organized_structure", True)
    
    @property
    def output_base_dir(self) -> str:
        """Get base output directory for organized structure."""
        return self.config.get("processing", {}).get("output_base_dir", "output_perturbation")
    
    @property
    def shared_timestamp(self) -> bool:
        """Get whether to use shared timestamp for all docs in a run."""
        return self.config.get("processing", {}).get("shared_timestamp", True)
    
    # Retry properties
    @property
    def retry_max_retries(self) -> int:
        """Get max retries from retry config."""
        return self.config.get("retry", {}).get("max_retries", 3)
    
    @property
    def retry_initial_backoff(self) -> float:
        """Get initial backoff time."""
        return self.config.get("retry", {}).get("initial_backoff", 1.0)
    
    @property
    def retry_max_backoff(self) -> float:
        """Get maximum backoff time."""
        return self.config.get("retry", {}).get("max_backoff", 60.0)
    
    @property
    def retry_backoff_multiplier(self) -> float:
        """Get backoff multiplier."""
        return self.config.get("retry", {}).get("backoff_multiplier", 2.0)
    
    @property
    def retry_on_rate_limit(self) -> bool:
        """Get whether to retry on rate limit."""
        return self.config.get("retry", {}).get("retry_on_rate_limit", True)
    
    @property
    def retry_on_timeout(self) -> bool:
        """Get whether to retry on timeout."""
        return self.config.get("retry", {}).get("retry_on_timeout", True)
    
    @property
    def retry_on_connection_error(self) -> bool:
        """Get whether to retry on connection error."""
        return self.config.get("retry", {}).get("retry_on_connection_error", True)
    
    # Logging properties
    @property
    def logging_enabled(self) -> bool:
        """Get whether logging is enabled."""
        return self.config.get("logging", {}).get("enabled", True)
    
    @property
    def logging_level(self) -> str:
        """Get logging level."""
        return self.config.get("logging", {}).get("level", "INFO")
    
    @property
    def logging_console_level(self) -> str:
        """Get console logging level."""
        return self.config.get("logging", {}).get("console_level", "INFO")
    
    @property
    def logging_file_level(self) -> str:
        """Get file logging level."""
        return self.config.get("logging", {}).get("file_level", "DEBUG")
    
    @property
    def logging_log_dir(self) -> str:
        """Get log directory."""
        return self.config.get("logging", {}).get("log_dir", "logs")
    
    @property
    def logging_timezone(self) -> str:
        """Get logging timezone."""
        return self.config.get("logging", {}).get("timezone", "America/Denver")
    
    @property
    def logging_max_bytes(self) -> int:
        """Get max bytes for log rotation."""
        return self.config.get("logging", {}).get("max_bytes", 10485760)
    
    @property
    def logging_backup_count(self) -> int:
        """Get backup count for log rotation."""
        return self.config.get("logging", {}).get("backup_count", 5)
    
    @property
    def logging_log_complete_prompts(self) -> bool:
        """Get whether to log complete prompts."""
        return self.config.get("logging", {}).get("log_complete_prompts", True)
    
    @property
    def logging_log_complete_responses(self) -> bool:
        """Get whether to log complete responses."""
        return self.config.get("logging", {}).get("log_complete_responses", True)
    
    @property
    def logging_log_token_usage(self) -> bool:
        """Get whether to log token usage."""
        return self.config.get("logging", {}).get("log_token_usage", True)
    
    @property
    def logging_log_timing(self) -> bool:
        """Get whether to log timing information."""
        return self.config.get("logging", {}).get("log_timing", True)
    
    # Batch API properties
    @property
    def batch_api_enabled(self) -> bool:
        """Get whether batch API is enabled."""
        return self.config.get("batch_api", {}).get("enabled", True)
    
    @property
    def batch_api_completion_window(self) -> str:
        """Get batch API completion window."""
        return self.config.get("batch_api", {}).get("completion_window", "24h")
    
    @property
    def batch_api_auto_fallback(self) -> bool:
        """Get whether to auto-fallback on batch failure."""
        return self.config.get("batch_api", {}).get("auto_fallback", True)
    
    @property
    def batch_api_check_interval(self) -> int:
        """Get batch status check interval."""
        return self.config.get("batch_api", {}).get("check_interval", 300)
    
    @property
    def batch_api_max_wait_time(self) -> Optional[int]:
        """Get max wait time for batch."""
        return self.config.get("batch_api", {}).get("max_wait_time")
    
    # Injection properties
    @property
    def injection_default_methods(self) -> List[str]:
        """Get default injection methods."""
        return self.config.get("injection", {}).get("default_methods", ["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"])
    
    def injection_method_enabled(self, method: str) -> bool:
        """Check if an injection method is enabled."""
        return self.config.get("injection", {}).get("methods", {}).get(method, {}).get("enabled", True)
    
    def injection_method_config(self, method: str) -> Dict[str, Any]:
        """Get configuration for a specific injection method."""
        return self.config.get("injection", {}).get("methods", {}).get(method, {})
    
    # PDF generation properties
    @property
    def pdf_generation_enabled(self) -> bool:
        """Get whether PDF generation is enabled."""
        return self.config.get("pdf_generation", {}).get("enabled", True)
    
    @property
    def pdf_generation_compile_pdf(self) -> bool:
        """Get whether to compile PDF."""
        return self.config.get("pdf_generation", {}).get("compile_pdf", True)
    
    @property
    def pdf_generation_output_base_dir(self) -> str:
        """Get PDF generation output base directory."""
        return self.config.get("pdf_generation", {}).get("output_base_dir", "output_attacked_pdfs")
    
    @property
    def pdf_generation_latex_compiler(self) -> str:
        """Get LaTeX compiler preference."""
        return self.config.get("pdf_generation", {}).get("latex_compiler", "auto")
    
    @property
    def pdf_generation_require_xetex_for_fonts(self) -> bool:
        """Get whether XeLaTeX is required for fonts."""
        return self.config.get("pdf_generation", {}).get("require_xetex_for_fonts", True)
    
    @property
    def pdf_generation_compilation_timeout(self) -> int:
        """Get PDF compilation timeout."""
        return self.config.get("pdf_generation", {}).get("compilation_timeout", 300)
    
    @property
    def pdf_generation_cleanup_fonts_after_compile(self) -> bool:
        """Get whether to cleanup fonts after compile."""
        return self.config.get("pdf_generation", {}).get("cleanup_fonts_after_compile", True)
    
    @property
    def pdf_generation_cleanup_temp_files(self) -> bool:
        """Get whether to cleanup temp files."""
        return self.config.get("pdf_generation", {}).get("cleanup_temp_files", True)
    
    @property
    def pdf_generation_apply_pdf_overlay(self) -> bool:
        """Get whether to apply PDF overlay."""
        return self.config.get("pdf_generation", {}).get("apply_pdf_overlay", True)
    
    @property
    def pdf_generation_overlay_search_original_pdf(self) -> bool:
        """Get whether to search for original PDF for overlay."""
        return self.config.get("pdf_generation", {}).get("overlay_search_original_pdf", True)
    
    # Prompt properties
    def prompt_config(self, question_type: str) -> Dict[str, Any]:
        """Get prompt configuration for a question type."""
        return self.config.get("prompts", {}).get(question_type.lower(), {})
    
    @property
    def prompt_system_message(self) -> str:
        """Get system message for prompts."""
        return self.config.get("prompts", {}).get("system_message", "You are a helpful assistant that generates JSON array responses. Always return valid JSON arrays.")
    
    @property
    def prompt_json_format_strict(self) -> bool:
        """Get whether to enforce strict JSON format."""
        return self.config.get("prompts", {}).get("json_format_strict", True)
    
    # Performance properties
    @property
    def performance_delay_between_requests(self) -> float:
        """Get delay between API requests."""
        return self.config.get("performance", {}).get("delay_between_requests", 0.0)
    
    @property
    def performance_delay_between_documents(self) -> float:
        """Get delay between documents."""
        return self.config.get("performance", {}).get("delay_between_documents", 0.0)
    
    @property
    def performance_delay_on_rate_limit(self) -> float:
        """Get delay on rate limit."""
        return self.config.get("performance", {}).get("delay_on_rate_limit", 1.0)
    
    @property
    def performance_max_concurrent_requests(self) -> int:
        """Get max concurrent requests."""
        return self.config.get("performance", {}).get("max_concurrent_requests", 1)
    
    @property
    def performance_max_concurrent_documents(self) -> int:
        """Get max concurrent documents."""
        return self.config.get("performance", {}).get("max_concurrent_documents", 1)
    
    # Experimental properties
    @property
    def experimental_icw_use_replacement_for_long(self) -> bool:
        """Get ICW replacement for long questions setting."""
        return self.config.get("experimental", {}).get("icw_use_replacement_for_long", True)
    
    @property
    def experimental_icw_use_target_wrong_for_mcq(self) -> bool:
        """Get ICW target wrong for MCQ setting."""
        return self.config.get("experimental", {}).get("icw_use_target_wrong_for_mcq", True)
    
    @property
    def experimental_dual_layer_allow_multiple_perturbations(self) -> bool:
        """Get dual layer multiple perturbations setting."""
        return self.config.get("experimental", {}).get("dual_layer_allow_multiple_perturbations", False)
    
    @property
    def experimental_font_attack_cleanup_after_compile(self) -> bool:
        """Get font attack cleanup setting."""
        return self.config.get("experimental", {}).get("font_attack_cleanup_after_compile", True)
    
    @property
    def experimental_include_metadata_in_output(self) -> bool:
        """Get include metadata in output setting."""
        return self.config.get("experimental", {}).get("include_metadata_in_output", True)
    
    @property
    def experimental_include_timing_in_output(self) -> bool:
        """Get include timing in output setting."""
        return self.config.get("experimental", {}).get("include_timing_in_output", True)
    
    @property
    def experimental_include_cost_estimates_in_output(self) -> bool:
        """Get include cost estimates in output setting."""
        return self.config.get("experimental", {}).get("include_cost_estimates_in_output", True)
    
    # Paths properties
    @property
    def paths_base_font(self) -> str:
        """Get base font path."""
        return self.config.get("paths", {}).get("base_font", "fonts/Roboto-Regular.ttf")
    
    @property
    def paths_latex_compiler_path(self) -> Optional[str]:
        """Get LaTeX compiler path."""
        return self.config.get("paths", {}).get("latex_compiler_path")
    
    @property
    def paths_output_perturbation(self) -> str:
        """Get output perturbation directory."""
        return self.config.get("paths", {}).get("output_perturbation", "output_perturbation")
    
    @property
    def paths_output_pdfs(self) -> str:
        """Get output PDFs directory."""
        return self.config.get("paths", {}).get("output_pdfs", "output_attacked_pdfs")
    
    @property
    def paths_logs(self) -> str:
        """Get logs directory."""
        return self.config.get("paths", {}).get("logs", "logs")
    
    @property
    def paths_temp(self) -> Optional[str]:
        """Get temp directory."""
        return self.config.get("paths", {}).get("temp")
    
    # Validation properties
    @property
    def validation_validate_perturbations(self) -> bool:
        """Get whether to validate perturbations."""
        return self.config.get("validation", {}).get("validate_perturbations", True)
    
    @property
    def validation_validate_latex_paths(self) -> bool:
        """Get whether to validate LaTeX paths."""
        return self.config.get("validation", {}).get("validate_latex_paths", True)
    
    @property
    def validation_validate_question_numbers(self) -> bool:
        """Get whether to validate question numbers."""
        return self.config.get("validation", {}).get("validate_question_numbers", True)
    
    @property
    def validation_min_perturbations_per_question(self) -> int:
        """Get minimum perturbations per question."""
        return self.config.get("validation", {}).get("min_perturbations_per_question", 1)
    
    @property
    def validation_max_perturbations_per_question(self) -> int:
        """Get maximum perturbations per question."""
        return self.config.get("validation", {}).get("max_perturbations_per_question", 10)
    
    @property
    def validation_require_replacement_substring(self) -> bool:
        """Get whether to require replacement substring."""
        return self.config.get("validation", {}).get("require_replacement_substring", True)
    
    @property
    def validation_require_original_substring(self) -> bool:
        """Get whether to require original substring."""
        return self.config.get("validation", {}).get("require_original_substring", True)
