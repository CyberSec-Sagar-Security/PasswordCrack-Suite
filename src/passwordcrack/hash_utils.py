"""
Hash generation and utilities module.

Supports multiple hashing algorithms for educational purposes.
All hashing is done locally on user-provided data only.
"""

import hashlib
import hmac
from typing import Optional, Dict, Any
from enum import Enum

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import HashingError
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    NTLM = "ntlm"
    BCRYPT = "bcrypt"
    PBKDF2_SHA256 = "pbkdf2_sha256"
    ARGON2 = "argon2"


class HashUtils:
    """Utility class for generating password hashes."""
    
    @staticmethod
    def generate_hash(
        password: str,
        algorithm: HashAlgorithm,
        salt: Optional[bytes] = None,
        rounds: int = 10
    ) -> str:
        """
        Generate a hash from a password using the specified algorithm.
        
        Args:
            password: The password to hash
            algorithm: The hashing algorithm to use
            salt: Optional salt for algorithms that support it
            rounds: Number of rounds for bcrypt/pbkdf2
            
        Returns:
            The generated hash as a hexadecimal string
            
        Raises:
            ValueError: If algorithm is not supported or library not installed
        """
        password_bytes = password.encode('utf-8')
        
        if algorithm == HashAlgorithm.MD5:
            return hashlib.md5(password_bytes).hexdigest()
            
        elif algorithm == HashAlgorithm.SHA1:
            return hashlib.sha1(password_bytes).hexdigest()
            
        elif algorithm == HashAlgorithm.SHA256:
            return hashlib.sha256(password_bytes).hexdigest()
            
        elif algorithm == HashAlgorithm.SHA512:
            return hashlib.sha512(password_bytes).hexdigest()
            
        elif algorithm == HashAlgorithm.NTLM:
            # NTLM is MD4 of UTF-16LE encoded password
            return hashlib.new('md4', password.encode('utf-16le')).hexdigest()
            
        elif algorithm == HashAlgorithm.BCRYPT:
            if not BCRYPT_AVAILABLE:
                raise ValueError("bcrypt library not installed. Install with: pip install bcrypt")
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=rounds))
            return hashed.decode('utf-8')
            
        elif algorithm == HashAlgorithm.PBKDF2_SHA256:
            if salt is None:
                import os
                salt = os.urandom(16)
            iterations = max(rounds * 10000, 100000)  # PBKDF2 needs many iterations
            key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, iterations)
            # Return in format: iterations$salt$hash
            return f"{iterations}${salt.hex()}${key.hex()}"
            
        elif algorithm == HashAlgorithm.ARGON2:
            if not ARGON2_AVAILABLE:
                raise ValueError("argon2-cffi library not installed. Install with: pip install argon2-cffi")
            ph = PasswordHasher()
            return ph.hash(password)
            
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @staticmethod
    def verify_hash(password: str, hash_value: str, algorithm: HashAlgorithm) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: The password to verify
            hash_value: The hash to verify against
            algorithm: The algorithm used to create the hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            if algorithm == HashAlgorithm.BCRYPT:
                if not BCRYPT_AVAILABLE:
                    return False
                return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))
                
            elif algorithm == HashAlgorithm.ARGON2:
                if not ARGON2_AVAILABLE:
                    return False
                ph = PasswordHasher()
                try:
                    ph.verify(hash_value, password)
                    return True
                except:
                    return False
                    
            elif algorithm == HashAlgorithm.PBKDF2_SHA256:
                # Parse the stored hash
                parts = hash_value.split('$')
                if len(parts) != 3:
                    return False
                iterations = int(parts[0])
                salt = bytes.fromhex(parts[1])
                stored_hash = parts[2]
                
                # Compute hash with same parameters
                key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
                return key.hex() == stored_hash
                
            else:
                # For simple hashes, just generate and compare
                generated = HashUtils.generate_hash(password, algorithm)
                return generated.lower() == hash_value.lower()
                
        except Exception:
            return False
    
    @staticmethod
    def get_available_algorithms() -> Dict[str, bool]:
        """
        Get a dictionary of available algorithms and their availability.
        
        Returns:
            Dict mapping algorithm names to availability status
        """
        return {
            "MD5": True,
            "SHA1": True,
            "SHA256": True,
            "SHA512": True,
            "NTLM": True,
            "BCRYPT": BCRYPT_AVAILABLE,
            "PBKDF2_SHA256": True,
            "ARGON2": ARGON2_AVAILABLE,
        }
    
    @staticmethod
    def get_algorithm_info(algorithm: HashAlgorithm) -> Dict[str, Any]:
        """
        Get information about a specific algorithm.
        
        Returns:
            Dict with algorithm details (length, security, speed)
        """
        info = {
            HashAlgorithm.MD5: {
                "name": "MD5",
                "length": 32,
                "security": "WEAK - Cryptographically broken",
                "speed": "Very Fast",
                "recommended": False
            },
            HashAlgorithm.SHA1: {
                "name": "SHA-1",
                "length": 40,
                "security": "WEAK - Collision attacks exist",
                "speed": "Very Fast",
                "recommended": False
            },
            HashAlgorithm.SHA256: {
                "name": "SHA-256",
                "length": 64,
                "security": "STRONG - But fast to brute force",
                "speed": "Fast",
                "recommended": False
            },
            HashAlgorithm.SHA512: {
                "name": "SHA-512",
                "length": 128,
                "security": "STRONG - But fast to brute force",
                "speed": "Fast",
                "recommended": False
            },
            HashAlgorithm.NTLM: {
                "name": "NTLM",
                "length": 32,
                "security": "WEAK - No salt, fast computation",
                "speed": "Very Fast",
                "recommended": False
            },
            HashAlgorithm.BCRYPT: {
                "name": "bcrypt",
                "length": 60,
                "security": "STRONG - Adaptive, salted",
                "speed": "Slow (by design)",
                "recommended": True
            },
            HashAlgorithm.PBKDF2_SHA256: {
                "name": "PBKDF2-SHA256",
                "length": "Variable",
                "security": "STRONG - Salted, configurable iterations",
                "speed": "Slow (by design)",
                "recommended": True
            },
            HashAlgorithm.ARGON2: {
                "name": "Argon2",
                "length": "Variable",
                "security": "VERY STRONG - Memory-hard, modern",
                "speed": "Slow (by design)",
                "recommended": True
            }
        }
        return info.get(algorithm, {})
