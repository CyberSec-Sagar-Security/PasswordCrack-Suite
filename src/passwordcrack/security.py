"""
Security module for encryption and secure data handling.

Provides encryption for session files and secure deletion.
NOTE: ALL OPERATIONS ARE LOCAL ONLY - NO NETWORK
"""

import os
from pathlib import Path
from typing import Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets


class SecurityManager:
    """Manages encryption and security operations."""
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        Initialize security manager.
        
        Args:
            key_file: Path to key file (default: .key in current dir)
        """
        if key_file is None:
            self.key_file = Path.cwd() / ".key"
        else:
            self.key_file = Path(key_file)
        
        self.key: Optional[bytes] = None
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password.
        
        Args:
            password: Password to derive from
            salt: Salt for key derivation
            
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def generate_key(self, password: Optional[str] = None) -> bytes:
        """
        Generate a new encryption key.
        
        Args:
            password: Optional password to derive key from
            
        Returns:
            Generated key (32 bytes)
        """
        if password:
            salt = secrets.token_bytes(16)
            self.key = self._derive_key(password, salt)
            # Store salt with key
            with open(self.key_file, 'wb') as f:
                f.write(salt + self.key)
        else:
            self.key = AESGCM.generate_key(bit_length=256)
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        return self.key
    
    def load_key(self, password: Optional[str] = None) -> bytes:
        """
        Load encryption key from file.
        
        Args:
            password: Password if key was derived
            
        Returns:
            Loaded key
        """
        if not self.key_file.exists():
            raise FileNotFoundError("Key file not found. Generate a key first.")
        
        with open(self.key_file, 'rb') as f:
            data = f.read()
        
        if password:
            # First 16 bytes are salt, rest is key
            salt = data[:16]
            self.key = self._derive_key(password, salt)
        else:
            self.key = data
        
        return self.key
    
    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data using AES-GCM.
        
        Args:
            data: Data to encrypt (str or bytes)
            
        Returns:
            Encrypted data (nonce + ciphertext + tag)
        """
        if self.key is None:
            raise ValueError("No key loaded. Generate or load a key first.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Generate random nonce
        nonce = secrets.token_bytes(12)
        
        # Encrypt
        aesgcm = AESGCM(self.key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # Return nonce + ciphertext
        return nonce + ciphertext
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Decrypt data using AES-GCM.
        
        Args:
            encrypted_data: Encrypted data (nonce + ciphertext + tag)
            
        Returns:
            Decrypted data as string
        """
        if self.key is None:
            raise ValueError("No key loaded. Load a key first.")
        
        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Decrypt
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode('utf-8')
    
    def secure_delete_file(self, filepath: Union[str, Path]) -> bool:
        """
        Securely delete a file by overwriting it first.
        
        Args:
            filepath: Path to file to delete
            
        Returns:
            True if deleted, False otherwise
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return False
        
        try:
            # Get file size
            file_size = filepath.stat().st_size
            
            # Overwrite with random data 3 times
            for _ in range(3):
                with open(filepath, 'wb') as f:
                    f.write(secrets.token_bytes(file_size))
            
            # Finally delete
            filepath.unlink()
            return True
            
        except Exception:
            return False
    
    def secure_delete_directory(self, dirpath: Union[str, Path]) -> bool:
        """
        Securely delete all files in a directory.
        
        Args:
            dirpath: Path to directory
            
        Returns:
            True if all deleted, False otherwise
        """
        dirpath = Path(dirpath)
        
        if not dirpath.exists():
            return False
        
        success = True
        
        # Delete all files
        for file in dirpath.rglob("*"):
            if file.is_file():
                if not self.secure_delete_file(file):
                    success = False
        
        # Try to remove empty directory
        try:
            dirpath.rmdir()
        except Exception:
            success = False
        
        return success
    
    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Random password string
        """
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def is_strong_password(password: str) -> dict:
        """
        Check password strength.
        
        Args:
            password: Password to check
            
        Returns:
            Dict with strength analysis
        """
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        score = sum([has_lower, has_upper, has_digit, has_special])
        length_ok = len(password) >= 8
        
        if length_ok and score >= 3:
            strength = "Strong"
        elif length_ok and score >= 2:
            strength = "Medium"
        else:
            strength = "Weak"
        
        return {
            "strength": strength,
            "length": len(password),
            "has_lowercase": has_lower,
            "has_uppercase": has_upper,
            "has_digits": has_digit,
            "has_special": has_special,
            "score": f"{score}/4",
            "recommendations": SecurityManager._get_recommendations(
                length_ok, has_lower, has_upper, has_digit, has_special
            )
        }
    
    @staticmethod
    def _get_recommendations(
        length_ok: bool,
        has_lower: bool,
        has_upper: bool,
        has_digit: bool,
        has_special: bool
    ) -> list:
        """Get password improvement recommendations."""
        recommendations = []
        
        if not length_ok:
            recommendations.append("Use at least 8 characters")
        if not has_lower:
            recommendations.append("Add lowercase letters")
        if not has_upper:
            recommendations.append("Add uppercase letters")
        if not has_digit:
            recommendations.append("Add numbers")
        if not has_special:
            recommendations.append("Add special characters")
        
        if not recommendations:
            recommendations.append("Password is strong!")
        
        return recommendations
