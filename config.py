"""Configuration management system for Record Matcher.

This module provides centralized configuration management with:
- TOML-based configuration files
- Environment-specific configs (dev/prod)
- Schema validation using Pydantic
- Type-safe configuration access
- Hot-reloading support

Example:
    config = ConfigManager()
    ledger_name = config.tally.hdfc_ledger_name
    max_cheque_length = config.validation.max_cheque_number_length
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import toml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Configuration Validation
# ============================================================================

class TallyLedgerConfig(BaseModel):
    """Tally ledger name configuration."""
    
    hdfc_ledger_name: str = Field(
        default="HDFC Bank A/c No.50200008623602",
        description="HDFC bank ledger name in Tally"
    )
    icici_ledger_name_gok: str = Field(
        default="ICICI Bank A/c No.099005000974",
        description="ICICI bank ledger name for GOK company"
    )
    icici_ledger_name_uni: str = Field(
        default="ICICI 1027",
        description="ICICI bank ledger name for UNI company"
    )
    payment_intermediary_ledger: str = Field(
        default="OTHER CREDITORS",
        description="Intermediate ledger for payment vouchers"
    )
    receipt_intermediary_ledger: str = Field(
        default="OTHER DEBTORS",
        description="Intermediate ledger for receipt vouchers"
    )

    class Config:
        frozen = False  # Allow updates
        extra = "forbid"  # Prevent unexpected fields


class ValidationConfig(BaseModel):
    """Validation rules configuration."""
    
    max_cheque_number_length: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum length for cheque numbers"
    )
    cheque_number_padding_length: int = Field(
        default=16,
        ge=1,
        le=50,
        description="Padding length for formatted cheque numbers"
    )
    
    @validator('cheque_number_padding_length')
    def padding_must_exceed_max(cls, v, values):
        """Ensure padding length is greater than max length."""
        if 'max_cheque_number_length' in values and v <= values['max_cheque_number_length']:
            logger.warning(
                f"Padding length ({v}) should be greater than max length "
                f"({values['max_cheque_number_length']})"
            )
        return v

    class Config:
        frozen = False
        extra = "forbid"


class PathConfig(BaseModel):
    """File path configuration."""
    
    temp_directory: str = Field(
        default="./temp",
        description="Directory for temporary files"
    )
    output_directory: str = Field(
        default="./output",
        description="Directory for output files"
    )
    fonts_directory: str = Field(
        default="./fonts",
        description="Directory for font files"
    )
    images_directory: str = Field(
        default="./images",
        description="Directory for image files"
    )
    service_account_directory: str = Field(
        default="./service-account",
        description="Directory for service account credentials"
    )
    
    class Config:
        frozen = False
        extra = "forbid"


class FirebaseConfig(BaseModel):
    """Firebase configuration."""
    
    credentials_file: str = Field(
        default="service-account/recordmatcher-firebase-adminsdk-mfcn7-d0ee2c6bad.json",
        description="Path to Firebase credentials JSON file"
    )
    database_url: Optional[str] = Field(
        default=None,
        description="Firebase Realtime Database URL"
    )
    batch_size: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Batch size for Firebase operations"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout for Firebase operations in seconds"
    )
    
    class Config:
        frozen = False
        extra = "forbid"


class ApplicationConfig(BaseModel):
    """Application-level configuration."""
    
    app_name: str = Field(
        default="Record Matcher",
        description="Application name"
    )
    environment: str = Field(
        default="production",
        description="Environment name (development/staging/production)"
    )
    debug_mode: bool = Field(
        default=False,
        description="Enable debug logging and features"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment name."""
        allowed = {'development', 'staging', 'production'}
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got '{v}'")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}, got '{v}'")
        return v.upper()
    
    class Config:
        frozen = False
        extra = "forbid"


class AppConfig(BaseModel):
    """Root configuration model."""
    
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    tally: TallyLedgerConfig = Field(default_factory=TallyLedgerConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    firebase: FirebaseConfig = Field(default_factory=FirebaseConfig)
    
    class Config:
        frozen = False
        extra = "forbid"


# ============================================================================
# Configuration Manager
# ============================================================================

class ConfigManager:
    """Centralized configuration manager with validation and environment support.
    
    This class manages application configuration with:
    - TOML file loading
    - Environment-specific overrides (dev/staging/prod)
    - Schema validation using Pydantic
    - Type-safe access to configuration values
    - Configuration merging and hot-reloading
    
    Usage:
        # Initialize with default config
        config = ConfigManager()
        
        # Initialize with specific environment
        config = ConfigManager(environment='development')
        
        # Access configuration values
        ledger_name = config.tally.hdfc_ledger_name
        max_length = config.validation.max_cheque_number_length
        
        # Reload configuration
        config.reload()
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one config manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        environment: Optional[str] = None,
        auto_reload: bool = False
    ):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files. Defaults to current directory.
            environment: Environment name (development/staging/production). 
                        If None, reads from RECORD_MATCHER_ENV environment variable.
            auto_reload: Enable automatic configuration reloading on file changes.
        """
        # Skip re-initialization for singleton
        if self._initialized:
            return
            
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.environment = environment or os.getenv('RECORD_MATCHER_ENV', 'production')
        self.auto_reload = auto_reload
        
        self._config: Optional[AppConfig] = None
        self._config_file_path: Optional[Path] = None
        self._last_modified: Optional[float] = None
        
        # Load configuration
        self.reload()
        self._initialized = True
        
        logger.info(
            f"ConfigManager initialized: environment={self.environment}, "
            f"config_dir={self.config_dir}"
        )
    
    def reload(self) -> None:
        """Reload configuration from files with validation.
        
        Loads configuration in this order:
        1. config.default.toml (default values)
        2. config.{environment}.toml (environment-specific overrides)
        3. config.local.toml (local overrides, gitignored)
        
        Raises:
            FileNotFoundError: If default config file doesn't exist
            ValueError: If configuration validation fails
        """
        try:
            # Load default configuration
            default_config_path = self.config_dir / "config.default.toml"
            if not default_config_path.exists():
                logger.warning(f"Default config not found: {default_config_path}")
                config_data = {}
            else:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
                logger.debug(f"Loaded default config from {default_config_path}")
            
            # Load environment-specific configuration
            env_config_path = self.config_dir / f"config.{self.environment}.toml"
            if env_config_path.exists():
                with open(env_config_path, 'r', encoding='utf-8') as f:
                    env_config = toml.load(f)
                config_data = self._merge_configs(config_data, env_config)
                logger.debug(f"Loaded {self.environment} config from {env_config_path}")
                self._config_file_path = env_config_path
            else:
                logger.debug(f"No environment config found: {env_config_path}")
                self._config_file_path = default_config_path
            
            # Load local overrides (not in version control)
            local_config_path = self.config_dir / "config.local.toml"
            if local_config_path.exists():
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_config = toml.load(f)
                config_data = self._merge_configs(config_data, local_config)
                logger.debug(f"Loaded local config from {local_config_path}")
            
            # Validate and create configuration object
            self._config = AppConfig(**config_data)
            
            # Track file modification time for auto-reload
            if self._config_file_path and self._config_file_path.exists():
                self._last_modified = self._config_file_path.stat().st_mtime
            
            logger.info("Configuration loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to default configuration
            if self._config is None:
                logger.warning("Using default configuration values")
                self._config = AppConfig()
            raise
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _check_reload(self) -> None:
        """Check if configuration file has changed and reload if needed."""
        if not self.auto_reload or not self._config_file_path:
            return
        
        try:
            if self._config_file_path.exists():
                current_mtime = self._config_file_path.stat().st_mtime
                if current_mtime != self._last_modified:
                    logger.info("Configuration file changed, reloading...")
                    self.reload()
        except Exception as e:
            logger.error(f"Error checking config file modification: {e}")
    
    @property
    def application(self) -> ApplicationConfig:
        """Get application configuration."""
        self._check_reload()
        return self._config.application
    
    @property
    def tally(self) -> TallyLedgerConfig:
        """Get Tally ledger configuration."""
        self._check_reload()
        return self._config.tally
    
    @property
    def validation(self) -> ValidationConfig:
        """Get validation configuration."""
        self._check_reload()
        return self._config.validation
    
    @property
    def paths(self) -> PathConfig:
        """Get path configuration."""
        self._check_reload()
        return self._config.paths
    
    @property
    def firebase(self) -> FirebaseConfig:
        """Get Firebase configuration."""
        self._check_reload()
        return self._config.firebase
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get entire configuration as dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        self._check_reload()
        return self._config.dict()
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """Save current configuration to TOML file.
        
        Args:
            file_path: Path to save configuration. If None, saves to config.local.toml
        """
        if file_path is None:
            file_path = self.config_dir / "config.local.toml"
        else:
            file_path = Path(file_path)
        
        try:
            config_dict = self._config.dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise


# ============================================================================
# Global Configuration Instance
# ============================================================================

# Create global config instance (lazy initialization)
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager instance.
    
    Returns:
        Singleton ConfigManager instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


def reset_config() -> None:
    """Reset global configuration instance (useful for testing)."""
    global _global_config
    _global_config = None
    ConfigManager._instance = None
    ConfigManager._initialized = False
