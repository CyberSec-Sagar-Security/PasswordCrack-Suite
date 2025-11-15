"""
Hybrid attack engine.

Combines dictionary words with masks (prefixes/suffixes).
NOTE: OFFLINE TESTING ONLY - NO NETWORK ATTACKS
"""

from typing import Iterator, Optional, Callable
from ..hash_utils import HashUtils, HashAlgorithm
from ..wordlist_manager import WordlistManager
from .mask_engine import MaskEngine


class HybridEngine:
    """Hybrid attack implementation (dictionary + mask)."""
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        wordlist_manager: WordlistManager
    ):
        """
        Initialize hybrid attack engine.
        
        Args:
            hash_value: Target hash to crack
            algorithm: Hash algorithm used
            wordlist_manager: Wordlist manager instance
        """
        self.hash_value = hash_value.strip().lower()
        self.algorithm = algorithm
        self.wordlist_manager = wordlist_manager
        self.attempts = 0
        self.found = False
        self.found_password: Optional[str] = None
    
    def attack(
        self,
        wordlist_file: str,
        mask: str = "?d?d",
        position: str = "suffix",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Perform hybrid attack.
        
        Args:
            wordlist_file: Wordlist filename to use
            mask: Mask pattern to append/prepend (e.g., "?d?d?d")
            position: "suffix" or "prefix" - where to apply mask
            progress_callback: Optional callback(attempts, current_password)
            
        Returns:
            Cracked password if found, None otherwise
        """
        self.attempts = 0
        self.found = False
        self.found_password = None
        
        try:
            # Generate mask expansions
            mask_engine = MaskEngine(self.hash_value, self.algorithm, mask)
            mask_variants = list(mask_engine._generate_candidates())
            
            # Try each word with each mask variant
            for word in self.wordlist_manager.load_wordlist(wordlist_file):
                for variant in mask_variants:
                    self.attempts += 1
                    
                    # Build candidate
                    if position == "suffix":
                        candidate = word + variant
                    else:  # prefix
                        candidate = variant + word
                    
                    if progress_callback and self.attempts % 100 == 0:
                        progress_callback(self.attempts, candidate)
                    
                    # Try the candidate
                    if self._try_password(candidate):
                        self.found = True
                        self.found_password = candidate
                        return candidate
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Hybrid attack failed: {e}")
    
    def attack_generator(
        self,
        wordlist_file: str,
        mask: str = "?d?d",
        position: str = "suffix"
    ) -> Iterator[tuple[str, bool]]:
        """
        Generator version of attack for fine-grained control.
        
        Args:
            wordlist_file: Wordlist filename to use
            mask: Mask pattern to append/prepend
            position: "suffix" or "prefix"
            
        Yields:
            Tuples of (candidate, is_match)
        """
        self.attempts = 0
        
        # Generate mask expansions
        mask_engine = MaskEngine(self.hash_value, self.algorithm, mask)
        mask_variants = list(mask_engine._generate_candidates())
        
        # Try each word with each mask variant
        for word in self.wordlist_manager.load_wordlist(wordlist_file):
            for variant in mask_variants:
                self.attempts += 1
                
                # Build candidate
                if position == "suffix":
                    candidate = word + variant
                else:  # prefix
                    candidate = variant + word
                
                is_match = self._try_password(candidate)
                yield (candidate, is_match)
                
                if is_match:
                    self.found = True
                    self.found_password = candidate
                    return
    
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
            "hash": self.hash_value
        }
