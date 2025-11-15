"""
Hash type identification module.

Attempts to identify hash type based on length, format, and patterns.
"""

import re
from typing import List, Optional, Dict
from .hash_utils import HashAlgorithm


class HashIdentifier:
    """Identifies hash types based on format and length."""
    
    # Hash format patterns and lengths
    HASH_PATTERNS = {
        HashAlgorithm.MD5: {
            "length": 32,
            "pattern": r"^[a-fA-F0-9]{32}$",
            "description": "MD5 (128-bit)"
        },
        HashAlgorithm.SHA1: {
            "length": 40,
            "pattern": r"^[a-fA-F0-9]{40}$",
            "description": "SHA-1 (160-bit)"
        },
        HashAlgorithm.SHA256: {
            "length": 64,
            "pattern": r"^[a-fA-F0-9]{64}$",
            "description": "SHA-256 (256-bit)"
        },
        HashAlgorithm.SHA512: {
            "length": 128,
            "pattern": r"^[a-fA-F0-9]{128}$",
            "description": "SHA-512 (512-bit)"
        },
        HashAlgorithm.NTLM: {
            "length": 32,
            "pattern": r"^[a-fA-F0-9]{32}$",
            "description": "NTLM (also matches MD5 length)"
        },
        HashAlgorithm.BCRYPT: {
            "length": 60,
            "pattern": r"^\$2[ayb]\$.{56}$",
            "description": "bcrypt"
        },
        HashAlgorithm.PBKDF2_SHA256: {
            "length": None,  # Variable
            "pattern": r"^\d+\$[a-fA-F0-9]+\$[a-fA-F0-9]+$",
            "description": "PBKDF2-SHA256 (custom format)"
        },
        HashAlgorithm.ARGON2: {
            "length": None,  # Variable
            "pattern": r"^\$argon2[id]{0,2}\$",
            "description": "Argon2"
        }
    }
    
    @staticmethod
    def identify(hash_value: str) -> List[HashAlgorithm]:
        """
        Identify possible hash algorithms for a given hash.
        
        Args:
            hash_value: The hash string to identify
            
        Returns:
            List of possible HashAlgorithm enum values, ordered by likelihood
        """
        hash_value = hash_value.strip()
        matches: List[HashAlgorithm] = []
        
        for algorithm, info in HashIdentifier.HASH_PATTERNS.items():
            pattern = info["pattern"]
            if re.match(pattern, hash_value):
                matches.append(algorithm)
        
        # Remove duplicates and order by security/likelihood
        # For 32-char hex, prefer NTLM over MD5 for Windows contexts
        # But return both as possibilities
        return matches
    
    @staticmethod
    def identify_with_details(hash_value: str) -> List[Dict[str, str]]:
        """
        Identify hash with detailed information.
        
        Args:
            hash_value: The hash string to identify
            
        Returns:
            List of dicts with algorithm, name, and description
        """
        algorithms = HashIdentifier.identify(hash_value)
        results = []
        
        for algo in algorithms:
            info = HashIdentifier.HASH_PATTERNS[algo]
            results.append({
                "algorithm": algo,
                "name": algo.value,
                "description": info["description"],
                "length": len(hash_value)
            })
        
        return results
    
    @staticmethod
    def is_valid_hash(hash_value: str, algorithm: Optional[HashAlgorithm] = None) -> bool:
        """
        Check if a hash value is valid for a specific algorithm.
        
        Args:
            hash_value: The hash to validate
            algorithm: The algorithm to validate against (None = any)
            
        Returns:
            True if valid, False otherwise
        """
        if algorithm:
            info = HashIdentifier.HASH_PATTERNS.get(algorithm)
            if not info:
                return False
            return bool(re.match(info["pattern"], hash_value.strip()))
        else:
            # Valid if it matches ANY known pattern
            return len(HashIdentifier.identify(hash_value)) > 0
    
    @staticmethod
    def get_hash_length(algorithm: HashAlgorithm) -> Optional[int]:
        """
        Get the expected length of a hash for a given algorithm.
        
        Args:
            algorithm: The hash algorithm
            
        Returns:
            Expected hash length in characters, or None if variable
        """
        info = HashIdentifier.HASH_PATTERNS.get(algorithm)
        return info["length"] if info else None
    
    @staticmethod
    def suggest_algorithm(hash_value: str) -> Optional[HashAlgorithm]:
        """
        Suggest the most likely algorithm for a hash.
        
        Args:
            hash_value: The hash to analyze
            
        Returns:
            Most likely HashAlgorithm, or None if unknown
        """
        matches = HashIdentifier.identify(hash_value)
        
        if not matches:
            return None
        
        # Priority order: specific formats first
        priority = [
            HashAlgorithm.ARGON2,
            HashAlgorithm.BCRYPT,
            HashAlgorithm.PBKDF2_SHA256,
            HashAlgorithm.SHA512,
            HashAlgorithm.SHA256,
            HashAlgorithm.SHA1,
            HashAlgorithm.NTLM,
            HashAlgorithm.MD5,
        ]
        
        for algo in priority:
            if algo in matches:
                return algo
        
        return matches[0]
