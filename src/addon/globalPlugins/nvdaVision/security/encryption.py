"""Encryption utilities for secure data storage.

This module provides Windows DPAPI encryption for API keys
to satisfy real.md constraint 2.
"""

import base64
from typing import Optional


class DPAPIEncryption:
    """Windows DPAPI encryption for API keys.

    DPAPI (Data Protection API) encrypts data using user's Windows credentials.
    Encrypted data can only be decrypted by the same user on the same machine.

    Satisfies real.md constraint 2: API keys must be encrypted.
    """

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """Encrypt plaintext using DPAPI.

        Args:
            plaintext: String to encrypt (e.g., API key)

        Returns:
            Base64-encoded encrypted string

        Raises:
            RuntimeError: If encryption fails

        Example:
            >>> encrypted = DPAPIEncryption.encrypt("my-secret-key")
            >>> print(encrypted)
            AQAAANCMnd8BF...
        """
        try:
            import win32crypt

            # Convert to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Encrypt with DPAPI
            encrypted_bytes = win32crypt.CryptProtectData(
                plaintext_bytes,
                None,  # Optional description
                None,  # Optional entropy
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )

            # Encode as base64 for storage
            encrypted_base64 = base64.b64encode(encrypted_bytes).decode('ascii')

            from ..infrastructure.logger import logger
            logger.debug("API key encrypted successfully")
            return encrypted_base64

        except ImportError:
            # Fallback for non-Windows platforms (development only)
            from ..infrastructure.logger import logger
            logger.warning("win32crypt not available, using base64 encoding (INSECURE)")
            return base64.b64encode(plaintext.encode('utf-8')).decode('ascii')

        except Exception as e:
            from ..infrastructure.logger import logger
            logger.exception("Failed to encrypt API key")
            raise RuntimeError(f"Encryption failed: {e}") from e

    @staticmethod
    def decrypt(encrypted_base64: str) -> str:
        """Decrypt DPAPI-encrypted string.

        Args:
            encrypted_base64: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            RuntimeError: If decryption fails (wrong user/machine)

        Example:
            >>> plaintext = DPAPIEncryption.decrypt(encrypted)
            >>> print(plaintext)
            my-secret-key
        """
        try:
            import win32crypt

            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_base64)

            # Decrypt with DPAPI
            plaintext_bytes = win32crypt.CryptUnprotectData(
                encrypted_bytes,
                None,  # Optional entropy
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )[1]  # Returns (description, plaintext)

            plaintext = plaintext_bytes.decode('utf-8')

            from ..infrastructure.logger import logger
            logger.debug("API key decrypted successfully")
            return plaintext

        except ImportError:
            # Fallback for non-Windows platforms (development only)
            from ..infrastructure.logger import logger
            logger.warning("win32crypt not available, using base64 decoding (INSECURE)")
            return base64.b64decode(encrypted_base64).decode('utf-8')

        except Exception as e:
            from ..infrastructure.logger import logger
            logger.exception("Failed to decrypt API key")
            raise RuntimeError(
                "Decryption failed. Key may have been encrypted by different user."
            ) from e


def mask_api_key(api_key: Optional[str]) -> str:
    """Mask API key for safe logging.

    Args:
        api_key: API key to mask

    Returns:
        Masked version showing only first/last 4 characters

    Example:
        >>> mask_api_key("sk-abc123xyz789")
        "sk-a...x789"
    """
    if not api_key or len(api_key) < 8:
        return "***"

    return f"{api_key[:4]}...{api_key[-4:]}"


__all__ = [
    "DPAPIEncryption",
    "mask_api_key",
]
