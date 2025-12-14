"""Configuration management for IntegrityShield pipeline."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

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
        
        # Merge with defaults
        default = self._get_default_config()
        return {**default, **config}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "openai": {
                "model": "gpt-4o",
                "batch_size": 5,
                "max_retries": 3,
                "timeout": 60,
                "temperature": 0.7
            },
            "processing": {
                "input_dir": "output",
                "output_suffix": "_perturbation",
                "resume": True,
                "mappings_per_question": 3
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
        return self.config.get("openai", {}).get("timeout", 60)
    
    @property
    def temperature(self) -> float:
        """Get temperature for API calls."""
        return self.config.get("openai", {}).get("temperature", 0.7)
    
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

