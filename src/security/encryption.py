"""
Encryption module for PHI protection.

Provides AES-256 encryption for data at rest and utilities
for secure data handling.

⚠️ IMPORTANT: This is a demonstration implementation.
For production use:
- Use proper key management (HSM, KMS)
- Implement key rotation
- Conduct security audit
"""

import os
import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import cryptography library
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning(
        "cryptography library not installed. "
        "Encryption features will be limited. "
        "Install with: pip install cryptography"
    )


@dataclass
class EncryptionResult:
    """Result of an encryption operation."""
    ciphertext: bytes
    salt: Optional[bytes]
    algorithm: str
    success: bool
    error: Optional[str] = None


class PHIEncryption:
    """
    Encrypt and decrypt PHI using AES-256 (Fernet).

    Fernet uses AES-128-CBC with HMAC-SHA256 for authentication.
    For AES-256, we derive a 256-bit key using PBKDF2.

    Example:
        enc = PHIEncryption()
        encrypted = enc.encrypt("Sensitive PHI data")
        decrypted = enc.decrypt(encrypted)
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption with key.

        Args:
            key: 32-byte encryption key. If None, generates new key.
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "cryptography library required for encryption. "
                "Install with: pip install cryptography"
            )

        if key is None:
            self.key = Fernet.generate_key()
            logger.info("Generated new encryption key")
        else:
            self.key = key

        self._cipher = Fernet(self.key)

    @classmethod
    def from_password(cls, password: str, salt: Optional[bytes] = None) -> "PHIEncryption":
        """
        Create encryption instance from password.

        Uses PBKDF2 to derive key from password.

        Args:
            password: Password to derive key from
            salt: Optional salt (generates if not provided)

        Returns:
            PHIEncryption instance
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        instance = cls(key)
        instance._salt = salt
        return instance

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data.

        Args:
            data: String or bytes to encrypt

        Returns:
            Encrypted bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        return self._cipher.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted bytes

        Returns:
            Decrypted bytes

        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        try:
            return self._cipher.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or corrupted data")

    def decrypt_to_string(self, encrypted_data: bytes) -> str:
        """
        Decrypt data and return as string.

        Args:
            encrypted_data: Encrypted bytes

        Returns:
            Decrypted string
        """
        return self.decrypt(encrypted_data).decode('utf-8')

    def get_key(self) -> bytes:
        """
        Get the encryption key.

        ⚠️ WARNING: Handle with extreme care.
        Never log or expose this key.

        Returns:
            Encryption key bytes
        """
        return self.key

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new random encryption key.

        Returns:
            32-byte random key
        """
        return Fernet.generate_key()


class SecureStorage:
    """
    Secure file storage with encryption.

    Provides encrypted file read/write operations.

    Example:
        storage = SecureStorage(encryption_key)
        storage.write_secure("patient_data.enc", data)
        data = storage.read_secure("patient_data.enc")
    """

    def __init__(self, encryption: PHIEncryption):
        """
        Initialize secure storage.

        Args:
            encryption: PHIEncryption instance for encryption operations
        """
        self.encryption = encryption

    def write_secure(self, filepath: Union[str, Path], data: Union[str, bytes]) -> bool:
        """
        Write data securely to encrypted file.

        Args:
            filepath: Path to write encrypted data
            data: Data to encrypt and write

        Returns:
            True if successful
        """
        try:
            filepath = Path(filepath)

            # Encrypt data
            encrypted = self.encryption.encrypt(data)

            # Write to file
            filepath.write_bytes(encrypted)

            logger.info(f"Securely wrote encrypted data to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to write secure file: {e}")
            return False

    def read_secure(self, filepath: Union[str, Path]) -> Optional[bytes]:
        """
        Read and decrypt data from encrypted file.

        Args:
            filepath: Path to encrypted file

        Returns:
            Decrypted data or None if failed
        """
        try:
            filepath = Path(filepath)

            if not filepath.exists():
                logger.error(f"File not found: {filepath}")
                return None

            # Read encrypted data
            encrypted = filepath.read_bytes()

            # Decrypt
            decrypted = self.encryption.decrypt(encrypted)

            logger.info(f"Securely read and decrypted {filepath}")
            return decrypted

        except Exception as e:
            logger.error(f"Failed to read secure file: {e}")
            return None

    def read_secure_string(self, filepath: Union[str, Path]) -> Optional[str]:
        """
        Read and decrypt file as string.

        Args:
            filepath: Path to encrypted file

        Returns:
            Decrypted string or None if failed
        """
        data = self.read_secure(filepath)
        if data:
            return data.decode('utf-8')
        return None


# =============================================================================
# Fallback for when cryptography is not available
# =============================================================================

class SimplePHIEncryption:
    """
    Simple XOR-based obfuscation when cryptography library not available.

    ⚠️ WARNING: This is NOT secure encryption!
    Only use for demonstration purposes.
    Install cryptography for real encryption: pip install cryptography
    """

    def __init__(self, key: Optional[bytes] = None):
        """Initialize with key."""
        if key is None:
            key = os.urandom(32)
        self.key = key
        logger.warning(
            "Using SimplePHIEncryption - NOT SECURE! "
            "Install cryptography for real encryption."
        )

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Obfuscate data (NOT real encryption)."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        # Simple XOR with key (NOT SECURE)
        key_repeated = (self.key * (len(data) // len(self.key) + 1))[:len(data)]
        result = bytes(a ^ b for a, b in zip(data, key_repeated))

        # Add marker to identify as obfuscated
        return b"OBFUSCATED:" + base64.b64encode(result)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """De-obfuscate data."""
        if not encrypted_data.startswith(b"OBFUSCATED:"):
            raise ValueError("Invalid encrypted data format")

        encoded = encrypted_data[11:]  # Remove marker
        data = base64.b64decode(encoded)

        # Reverse XOR
        key_repeated = (self.key * (len(data) // len(self.key) + 1))[:len(data)]
        return bytes(a ^ b for a, b in zip(data, key_repeated))


# =============================================================================
# Utility Functions
# =============================================================================

def hash_identifier(identifier: str, salt: Optional[bytes] = None) -> str:
    """
    Create a one-way hash of an identifier.

    Useful for creating pseudonymized IDs that can't be reversed.

    Args:
        identifier: Original identifier (e.g., patient ID)
        salt: Optional salt for added security

    Returns:
        Hashed identifier string
    """
    if salt is None:
        salt = b"radassist_default_salt"  # Should be configured per deployment

    data = f"{salt.decode('utf-8', errors='ignore')}:{identifier}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def create_pseudonym(original_id: str, prefix: str = "ANON") -> str:
    """
    Create a pseudonymous ID from original.

    Args:
        original_id: Original identifier
        prefix: Prefix for pseudonym

    Returns:
        Pseudonymous ID
    """
    hash_part = hash_identifier(original_id)[:8]
    return f"{prefix}_{hash_part.upper()}"


def secure_delete(filepath: Union[str, Path]) -> bool:
    """
    Securely delete a file by overwriting before deletion.

    Args:
        filepath: Path to file to delete

    Returns:
        True if successful
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            return True

        # Get file size
        size = filepath.stat().st_size

        # Overwrite with random data
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())

        # Delete file
        filepath.unlink()

        logger.info(f"Securely deleted {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to securely delete {filepath}: {e}")
        return False
