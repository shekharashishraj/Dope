"""Configuration management for IntegrityShield pipeline."""
from dotenv import load_dotenv
from .models.config import Config as PydanticConfig

# Load environment variables
load_dotenv()

# Re-export Config for backward compatibility
Config = PydanticConfig
