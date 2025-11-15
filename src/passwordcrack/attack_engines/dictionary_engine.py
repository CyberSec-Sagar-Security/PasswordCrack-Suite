"""
Dictionary attack engine.

Performs dictionary-based password cracking using wordlists.
NOTE: OFFLINE TESTING ONLY - NO NETWORK ATTACKS
"""

from typing import Iterator, Optional, Callable
from ..hash_utils import HashUtils, HashAlgorithm
from ..wordlist_manager import WordlistManager


class DictionaryEngine:
    """Dictionary attack implementation."""
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        wordlist_manager: WordlistManager
    ):
        """
        Initialize dictionary attack engine.
        
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
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Perform dictionary attack.
        
        Args:
            wordlist_file: Wordlist filename to use
            progress_callback: Optional callback(attempts, current_word)
            
        Returns:
            Cracked password if found, None otherwise
        """
        self.attempts = 0
        self.found = False
        self.found_password = None
        
        try:
            for word in self.wordlist_manager.load_wordlist(wordlist_file):
                self.attempts += 1
                
                if progress_callback and self.attempts % 100 == 0:
                    progress_callback(self.attempts, word)
                
                # Try the word
                if self._try_password(word):
                    self.found = True
                    self.found_password = word
                    return word
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Dictionary attack failed: {e}")
    
    def attack_generator(
        self,
        wordlist_file: str
    ) -> Iterator[tuple[str, bool]]:
        """
        Generator version of attack for fine-grained control.
        
        Args:
            wordlist_file: Wordlist filename to use
            
        Yields:
            Tuples of (candidate, is_match)
        """
        self.attempts = 0
        
        for word in self.wordlist_manager.load_wordlist(wordlist_file):
            self.attempts += 1
            is_match = self._try_password(word)
            
            yield (word, is_match)
            
            if is_match:
                self.found = True
                self.found_password = word
                break
    
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
