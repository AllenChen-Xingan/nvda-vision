"""Configuration management with encryption support.

This module manages plugin configuration with encrypted API keys
to satisfy real.md constraint 2.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from ..security.encryption import DPAPIEncryption
from .logger import logger


class ConfigManager:
    """Manage configuration with validation and encryption."""

    DEFAULT_CONFIG_PATH = Path.home() / ".nvda_vision" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file (default: ~/.nvda_vision/config.yaml)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.load()

    def load(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self.config = self._get_default_config()
            self.save()
            logger.info("Created default configuration")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}

            # Decrypt API keys
            self._decrypt_api_keys()

            logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            logger.exception("Failed to load configuration")
            self.config = self._get_default_config()

    def save(self):
        """Save configuration to YAML file."""
        try:
            # Create copy without decrypted keys
            config_to_save = self._prepare_for_save()

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    config_to_save,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.exception("Failed to save configuration")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Supports nested keys with dot notation: "models.uitars.enabled"

        Args:
            key: Configuration key (dot-separated for nested)
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("models.timeout_seconds")
            15.0
            >>> config.get("nonexistent.key", default=42)
            42
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by key.

        Args:
            key: Configuration key (dot-separated for nested)
            value: Value to set

        Example:
            >>> config.set("models.timeout_seconds", 20.0)
        """
        keys = key.split('.')
        target = self.config

        # Navigate to parent
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value

    def save_api_key(self, key_name: str, plaintext_key: str):
        """Save API key with DPAPI encryption.

        Args:
            key_name: Key identifier (e.g., "doubao_api_key")
            plaintext_key: Plaintext API key
        """
        # Encrypt key
        encrypted = DPAPIEncryption.encrypt(plaintext_key)

        # Store encrypted version
        self.set(f"security.{key_name}_encrypted", encrypted)

        # Keep decrypted in memory for current session
        self.config[key_name] = plaintext_key

        # Save to file (only encrypted version)
        self.save()

        logger.info(f"API key '{key_name}' saved securely")

    def _decrypt_api_keys(self):
        """Decrypt API keys from config."""
        security = self.config.get("security", {})

        for key, value in security.items():
            if key.endswith("_encrypted"):
                api_key_name = key.replace("_encrypted", "")
                try:
                    decrypted = DPAPIEncryption.decrypt(value)
                    self.config[api_key_name] = decrypted
                    logger.debug(f"Decrypted API key: {api_key_name}")
                except Exception as e:
                    logger.error(f"Failed to decrypt {api_key_name}: {e}")

    def _prepare_for_save(self) -> Dict[str, Any]:
        """Prepare config for saving (remove decrypted keys).

        Returns:
            Config dict safe to save to file
        """
        import copy
        config_copy = copy.deepcopy(self.config)

        # Remove decrypted API keys
        for key in list(config_copy.keys()):
            if key.endswith("_api_key") and not key.endswith("_encrypted"):
                del config_copy[key]

        return config_copy

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "version": "1.0.0",
            "language": "zh-CN",
            "enable_cloud_api": False,
            "models": {
                "preference": "auto",
                "timeout_seconds": 15.0,
                "confidence_threshold": 0.7,
                "uitars": {
                    "enabled": True,
                    "model_path": "models/uitars-7b",
                    "device": "cuda",
                    "dtype": "float16",
                },
                "minicpm": {
                    "enabled": True,
                    "model_path": "models/minicpm-v-2.6",
                    "device": "cpu",
                },
                "doubao": {
                    "enabled": False,
                    "api_endpoint": "https://ark.cn-beijing.volces.com/api/v3/visual",
                },
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 300,
                "max_size": 100,
            },
            "ui": {
                "announce_confidence": True,
                "announce_position": True,
                "auto_recognize_on_focus": False,
                "progress_feedback_delay": 5.0,
            },
            "shortcuts": {
                "recognize_screen": "NVDA+shift+v",
                "recognize_at_cursor": "NVDA+shift+c",
                "next_element": "NVDA+shift+n",
                "previous_element": "NVDA+shift+p",
            },
            "privacy": {
                "local_processing_only": True,
                "blur_sensitive_regions": False,
                "log_screenshots": False,
            },
            "security": {},
            "logging": {
                "level": "INFO",
                "retention_days": 7,
                "max_file_size_mb": 10,
            },
        }


__all__ = ["ConfigManager"]
