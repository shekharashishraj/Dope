"""Configuration models using Pydantic."""
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any
from pathlib import Path


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    model: str = Field(default="gpt-4o")
    batch_size: int = Field(default=5, gt=0)
    max_retries: int = Field(default=3, ge=0)
    timeout: int = Field(default=120, gt=0)
    temperature: float = Field(default=0.5, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    api_key: Optional[str] = None  # Loaded from env
    logprobs: bool = Field(default=True, description="Request log probabilities from API")
    top_logprobs: Optional[int] = Field(default=5, ge=0, le=20, description="Number of top logprobs to return")


class StagedPipelineConfig(BaseModel):
    """Staged pipeline configuration for 5-stage mapping generation."""
    enabled: bool = Field(default=False, description="Enable 5-stage pipeline instead of grouped batch")
    max_retries_per_mapping: int = Field(default=3, ge=1, description="Max retries for each mapping attempt")
    enable_flip_verification: bool = Field(default=True, description="Enable Stage 5 LLM judge to verify answer flips")


class ProcessingConfig(BaseModel):
    """Processing configuration."""
    input_dir: str = Field(default="output")
    output_suffix: str = Field(default="_perturbation")
    resume: bool = Field(default=True)
    mappings_per_question: int = Field(default=3, gt=0)
    use_organized_structure: bool = Field(default=True)
    output_base_dir: str = Field(default="output_perturbation")
    shared_timestamp: bool = Field(default=True)
    use_staged_pipeline: bool = Field(default=False, description="Use 5-stage pipeline for mapping generation")
    staged_pipeline: StagedPipelineConfig = Field(default_factory=StagedPipelineConfig)


class RetryConfig(BaseModel):
    """Retry configuration."""
    max_retries: int = Field(default=3, ge=0)
    initial_backoff: float = Field(default=1.0, gt=0)
    max_backoff: float = Field(default=60.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, gt=0)
    retry_on_rate_limit: bool = Field(default=True)
    retry_on_timeout: bool = Field(default=True)
    retry_on_connection_error: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    enabled: bool = Field(default=True)
    level: str = Field(default="INFO")
    console_level: str = Field(default="INFO")
    file_level: str = Field(default="DEBUG")
    log_dir: str = Field(default="logs")
    timezone: str = Field(default="America/Denver")
    max_bytes: int = Field(default=10485760, gt=0)
    backup_count: int = Field(default=5, ge=0)
    log_complete_prompts: bool = Field(default=True)
    log_complete_responses: bool = Field(default=True)
    log_token_usage: bool = Field(default=True)
    log_timing: bool = Field(default=True)


class BatchAPIConfig(BaseModel):
    """Batch API configuration."""
    enabled: bool = Field(default=True)
    completion_window: str = Field(default="24h")
    auto_fallback: bool = Field(default=True)
    check_interval: int = Field(default=300, gt=0)
    max_wait_time: Optional[int] = Field(default=None, gt=0)


class InjectionMethodConfig(BaseModel):
    """Configuration for a specific injection method."""
    enabled: bool = Field(default=True)
    use_first_perturbation_only: Optional[bool] = None
    base_font_path: Optional[str] = None
    fonts_dir: Optional[str] = None
    generate_all_perturbations: Optional[bool] = None


class InjectionConfig(BaseModel):
    """Injection methods configuration."""
    default_methods: List[str] = Field(default_factory=lambda: ["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"])
    methods: Dict[str, InjectionMethodConfig] = Field(default_factory=dict)


class PDFGenerationConfig(BaseModel):
    """PDF generation configuration."""
    enabled: bool = Field(default=True)
    compile_pdf: bool = Field(default=True)
    output_base_dir: str = Field(default="output_attacked_pdfs")
    latex_compiler: str = Field(default="auto")
    require_xetex_for_fonts: bool = Field(default=True)
    compilation_timeout: int = Field(default=300, gt=0)
    cleanup_fonts_after_compile: bool = Field(default=True)
    cleanup_temp_files: bool = Field(default=True)
    apply_pdf_overlay: bool = Field(default=True)
    overlay_search_original_pdf: bool = Field(default=True)


class PromptTypeConfig(BaseModel):
    """Configuration for a specific prompt type."""
    include_reasoning: bool = Field(default=False)
    include_answer_guidance: bool = Field(default=False)
    prefix_note: str = Field(default="")
    retry_instructions: str = Field(default="")


class PromptConfig(BaseModel):
    """Prompt customization configuration."""
    mcq: PromptTypeConfig = Field(default_factory=PromptTypeConfig)
    tf: PromptTypeConfig = Field(default_factory=PromptTypeConfig)
    long: PromptTypeConfig = Field(default_factory=PromptTypeConfig)
    system_message: str = Field(default="You are a helpful assistant that generates JSON array responses. Always return valid JSON arrays.")
    json_format_strict: bool = Field(default=True)
    grouped_prompts_folder: str = Field(default="grouped_batch_v2", description="Folder name in prompts/ directory for grouped batch prompts (e.g., 'grouped_batch' or 'grouped_batch_v2')")


class PerformanceConfig(BaseModel):
    """Performance and concurrency configuration."""
    delay_between_requests: float = Field(default=0.0, ge=0.0)
    delay_between_documents: float = Field(default=0.0, ge=0.0)
    delay_on_rate_limit: float = Field(default=1.0, ge=0.0)
    max_concurrent_requests: int = Field(default=1, gt=0)
    max_concurrent_documents: int = Field(default=1, gt=0)


class ExperimentalConfig(BaseModel):
    """Experimental features configuration."""
    icw_use_replacement_for_long: bool = Field(default=True)
    icw_use_target_wrong_for_mcq: bool = Field(default=True)
    dual_layer_allow_multiple_perturbations: bool = Field(default=False)
    font_attack_cleanup_after_compile: bool = Field(default=True)
    include_metadata_in_output: bool = Field(default=True)
    include_timing_in_output: bool = Field(default=True)
    include_cost_estimates_in_output: bool = Field(default=True)


class PathsConfig(BaseModel):
    """Paths and directories configuration."""
    base_font: str = Field(default="fonts/Roboto-Regular.ttf")
    latex_compiler_path: Optional[str] = None
    output_perturbation: str = Field(default="output_perturbation")
    output_pdfs: str = Field(default="output_attacked_pdfs")
    logs: str = Field(default="logs")
    temp: Optional[str] = None


class ValidationConfig(BaseModel):
    """Validation and quality control configuration."""
    validate_perturbations: bool = Field(default=True)
    validate_latex_paths: bool = Field(default=True)
    validate_question_numbers: bool = Field(default=True)
    min_perturbations_per_question: int = Field(default=1, gt=0)
    max_perturbations_per_question: int = Field(default=10, gt=0)
    require_replacement_substring: bool = Field(default=True)
    require_original_substring: bool = Field(default=True)


class Config(BaseSettings):
    """Main configuration model."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    batch_api: BatchAPIConfig = Field(default_factory=BatchAPIConfig)
    injection: InjectionConfig = Field(default_factory=InjectionConfig)
    pdf_generation: PDFGenerationConfig = Field(default_factory=PDFGenerationConfig)
    prompts: PromptConfig = Field(default_factory=PromptConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    experimental: ExperimentalConfig = Field(default_factory=ExperimentalConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "Config":
        """Load configuration from YAML file."""
        import yaml
        
        config_file = Path(config_path)
        if not config_file.exists():
            # Return defaults if file doesn't exist
            return cls()
        
        with open(config_file, 'r') as f:
            yaml_data = yaml.safe_load(f) or {}
        
        # Handle injection methods dict conversion
        if "injection" in yaml_data and "methods" in yaml_data["injection"]:
            methods_dict = yaml_data["injection"]["methods"]
            # Convert dict values to InjectionMethodConfig
            converted_methods = {}
            for method_name, method_data in methods_dict.items():
                if isinstance(method_data, dict):
                    converted_methods[method_name] = InjectionMethodConfig(**method_data)
                else:
                    converted_methods[method_name] = InjectionMethodConfig()
            yaml_data["injection"]["methods"] = converted_methods
        
        # Handle prompt type configs
        if "prompts" in yaml_data:
            prompts_data = yaml_data["prompts"]
            for prompt_type in ["mcq", "tf", "long"]:
                if prompt_type in prompts_data and isinstance(prompts_data[prompt_type], dict):
                    prompts_data[prompt_type] = PromptTypeConfig(**prompts_data[prompt_type])
        
        # Convert YAML dict to Config model
        return cls.model_validate(yaml_data)
    
    def __init__(self, config_path: str = None, **kwargs):
        """Initialize config with environment variable support."""
        # If config_path is provided, load from YAML first
        if config_path:
            yaml_config = Config.from_yaml(config_path)
            # Merge YAML config with kwargs (YAML takes precedence)
            yaml_dict = yaml_config.model_dump(mode='python', exclude_none=False)
            # Update with any provided kwargs
            for key, value in kwargs.items():
                if key in yaml_dict and isinstance(yaml_dict[key], dict) and isinstance(value, dict):
                    yaml_dict[key].update(value)
                else:
                    yaml_dict[key] = value
            kwargs = yaml_dict
        
        super().__init__(**kwargs)
        # Override API key from environment if not set
        if not self.openai.api_key:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai.api_key = api_key

