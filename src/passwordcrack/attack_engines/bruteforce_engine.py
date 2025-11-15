"""
Brute-force attack engine.

Generates all possible password combinations within constraints.
NOTE: OFFLINE TESTING ONLY - NO NETWORK ATTACKS
"""

import itertools
from typing import Iterator, Optional, Callable, List
from ..hash_utils import HashUtils, HashAlgorithm


class BruteforceEngine:
    """Brute-force attack implementation."""
    
    # Predefined character sets
    CHARSETS = {
        'lowercase': 'abcdefghijklmnopqrstuvwxyz',
        'uppercase': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'digits': '0123456789',
        'special': '!@#$%^&*()_+-=[]{}|;:,.<>?',
        'space': ' ',
    }
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        charset: str = 'lowercase',
        min_length: int = 1,
        max_length: int = 4
    ):
        """
        Initialize brute-force attack engine.
        
        Args:
            hash_value: Target hash to crack
            algorithm: Hash algorithm used
            charset: Character set to use (name or custom string)
            min_length: Minimum password length
            max_length: Maximum password length
        """
        self.hash_value = hash_value.strip().lower()
        self.algorithm = algorithm
        self.min_length = max(1, min_length)
        self.max_length = max(self.min_length, max_length)
        
        # Resolve charset
        if charset in self.CHARSETS:
            self.charset = self.CHARSETS[charset]
        else:
            self.charset = charset  # Custom charset
        
        self.attempts = 0
        self.found = False
        self.found_password: Optional[str] = None
    
    def attack(
        self,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        max_attempts: Optional[int] = None
    ) -> Optional[str]:
        """
        Perform brute-force attack.
        
        Args:
            progress_callback: Optional callback(attempts, current_password)
            max_attempts: Maximum attempts before giving up (safety limit)
            
        Returns:
            Cracked password if found, None otherwise
        """
        self.attempts = 0
        self.found = False
        self.found_password = None
        
        try:
            for candidate in self._generate_candidates():
                self.attempts += 1
                
                if progress_callback and self.attempts % 1000 == 0:
                    progress_callback(self.attempts, candidate)
                
                if max_attempts and self.attempts >= max_attempts:
                    break
                
                # Try the candidate
                if self._try_password(candidate):
                    self.found = True
                    self.found_password = candidate
                    return candidate
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Brute-force attack failed: {e}")
    
    def attack_generator(self) -> Iterator[tuple[str, bool]]:
        """
        Generator version of attack for fine-grained control.
        
        Yields:
            Tuples of (candidate, is_match)
        """
        self.attempts = 0
        
        for candidate in self._generate_candidates():
            self.attempts += 1
            is_match = self._try_password(candidate)
            
            yield (candidate, is_match)
            
            if is_match:
                self.found = True
                self.found_password = candidate
                break
    
    def _generate_candidates(self) -> Iterator[str]:
        """
        Generate all password candidates.
        
        Yields:
            Password candidates
        """
        for length in range(self.min_length, self.max_length + 1):
            for combo in itertools.product(self.charset, repeat=length):
                yield ''.join(combo)
    
    def _try_password(self, password: str) -> bool:
        """
        Try a password candidate.
        
        Args:
            password: Password to try
            
        Returns:
            True if match, False otherwise
        """
        try:
            # Generate hash for candidate
            candidate_hash = HashUtils.generate_hash(password, self.algorithm)
            
            # For PBKDF2, bcrypt, argon2, use verify method
            if self.algorithm in [
                HashAlgorithm.BCRYPT,
                HashAlgorithm.ARGON2,
                HashAlgorithm.PBKDF2_SHA256
            ]:
                return HashUtils.verify_hash(password, self.hash_value, self.algorithm)
            else:
                # For simple hashes, compare directly
                return candidate_hash.lower() == self.hash_value.lower()
                
        except Exception:
            return False
    
    def estimate_total_attempts(self) -> int:
        """
        Estimate total number of attempts needed.
        
        Returns:
            Estimated total attempts (keyspace size)
        """
        total = 0
        charset_size = len(self.charset)
        
        for length in range(self.min_length, self.max_length + 1):
            total += charset_size ** length
        
        return total
    
    def get_stats(self) -> dict:
        """
        Get attack statistics.
        
        Returns:
            Dict with attack statistics
        """
        return {
            "attempts": self.attempts,
            "found": self.found,
            "password": self.found_password,
            "algorithm": self.algorithm.value,
            "hash": self.hash_value,
            "charset": self.charset,
            "charset_size": len(self.charset),
            "min_length": self.min_length,
            "max_length": self.max_length,
            "estimated_total": self.estimate_total_attempts()
        }
    
    @classmethod
    def get_combined_charset(cls, charset_names: List[str]) -> str:
        """
        Combine multiple predefined charsets.
        
        Args:
            charset_names: List of charset names to combine
            
        Returns:
            Combined charset string
        """
        combined = ""
        for name in charset_names:
            if name in cls.CHARSETS:
                combined += cls.CHARSETS[name]
        return combined
