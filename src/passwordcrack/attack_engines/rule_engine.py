"""
Rule-based transformation engine.

Applies transformation rules to dictionary words (leetspeak, capitalization, etc.).
NOTE: OFFLINE TESTING ONLY - NO NETWORK ATTACKS
"""

from typing import Iterator, List, Callable, Optional
from ..hash_utils import HashUtils, HashAlgorithm
from ..wordlist_manager import WordlistManager


class RuleEngine:
    """Rule-based word transformation engine."""
    
    # Predefined rule sets
    LEETSPEAK_RULES = {
        'a': ['a', '@', '4'],
        'e': ['e', '3'],
        'i': ['i', '1', '!'],
        'o': ['o', '0'],
        's': ['s', '$', '5'],
        't': ['t', '7'],
        'l': ['l', '1'],
        'g': ['g', '9'],
        'b': ['b', '8'],
    }
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        wordlist_manager: WordlistManager
    ):
        """
        Initialize rule engine.
        
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
        rules: List[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Perform rule-based attack.
        
        Args:
            wordlist_file: Wordlist filename to use
            rules: List of rule names to apply (default: all common rules)
            progress_callback: Optional callback(attempts, current_password)
            
        Returns:
            Cracked password if found, None otherwise
        """
        if rules is None:
            rules = ['original', 'capitalize', 'uppercase', 'lowercase', 
                     'append_digits', 'prepend_digits', 'leetspeak_simple']
        
        self.attempts = 0
        self.found = False
        self.found_password = None
        
        try:
            for word in self.wordlist_manager.load_wordlist(wordlist_file):
                # Generate all variations
                for variant in self._apply_rules(word, rules):
                    self.attempts += 1
                    
                    if progress_callback and self.attempts % 100 == 0:
                        progress_callback(self.attempts, variant)
                    
                    # Try the variant
                    if self._try_password(variant):
                        self.found = True
                        self.found_password = variant
                        return variant
            
            return None
            
        except Exception as e:
            raise RuntimeError(f"Rule-based attack failed: {e}")
    
    def _apply_rules(self, word: str, rules: List[str]) -> Iterator[str]:
        """
        Apply transformation rules to a word.
        
        Args:
            word: Base word
            rules: List of rule names
            
        Yields:
            Word variations
        """
        for rule in rules:
            if rule == 'original':
                yield word
            
            elif rule == 'capitalize':
                yield word.capitalize()
            
            elif rule == 'uppercase':
                yield word.upper()
            
            elif rule == 'lowercase':
                yield word.lower()
            
            elif rule == 'reverse':
                yield word[::-1]
            
            elif rule == 'append_digits':
                for i in range(100):  # 00-99
                    yield f"{word}{i:02d}"
            
            elif rule == 'prepend_digits':
                for i in range(100):
                    yield f"{i:02d}{word}"
            
            elif rule == 'append_year':
                for year in range(1990, 2026):
                    yield f"{word}{year}"
            
            elif rule == 'append_special':
                for char in '!@#$%':
                    yield f"{word}{char}"
            
            elif rule == 'leetspeak_simple':
                # Simple leetspeak (single pass)
                variant = word.lower()
                variant = variant.replace('a', '@')
                variant = variant.replace('e', '3')
                variant = variant.replace('i', '1')
                variant = variant.replace('o', '0')
                variant = variant.replace('s', '$')
                yield variant
            
            elif rule == 'duplicate':
                yield word + word
            
            elif rule == 'toggle_first':
                if word:
                    first = word[0]
                    toggled = first.lower() if first.isupper() else first.upper()
                    yield toggled + word[1:]
            
            elif rule == 'toggle_last':
                if word:
                    last = word[-1]
                    toggled = last.lower() if last.isupper() else last.upper()
                    yield word[:-1] + toggled
    
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
    
    @staticmethod
    def get_available_rules() -> List[str]:
        """
        Get list of available transformation rules.
        
        Returns:
            List of rule names
        """
        return [
            'original',
            'capitalize',
            'uppercase',
            'lowercase',
            'reverse',
            'append_digits',
            'prepend_digits',
            'append_year',
            'append_special',
            'leetspeak_simple',
            'duplicate',
            'toggle_first',
            'toggle_last',
        ]
