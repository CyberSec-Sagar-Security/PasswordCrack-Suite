"""
Mask attack engine.

Uses mask patterns like ?l?l?d?d (lowercase+lowercase+digit+digit).
NOTE: OFFLINE TESTING ONLY - NO NETWORK ATTACKS
"""

import itertools
from typing import Iterator, Optional, Callable, Dict
from ..hash_utils import HashUtils, HashAlgorithm


class MaskEngine:
    """Mask-based attack implementation."""
    
    # Mask placeholders
    MASK_CHARS = {
        '?l': 'abcdefghijklmnopqrstuvwxyz',  # lowercase
        '?u': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',  # uppercase
        '?d': '0123456789',                   # digits
        '?s': '!@#$%^&*()_+-=[]{}|;:,.<>?',  # special
        '?a': None,  # all (will be computed)
        '?h': '0123456789abcdef',             # hex lowercase
        '?H': '0123456789ABCDEF',             # hex uppercase
    }
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        mask: str
    ):
        """
        Initialize mask attack engine.
        
        Args:
            hash_value: Target hash to crack
            algorithm: Hash algorithm used
            mask: Mask pattern (e.g., "?l?l?l?d?d?d")
        """
        self.hash_value = hash_value.strip().lower()
        self.algorithm = algorithm
        self.mask = mask
        self.attempts = 0
        self.found = False
        self.found_password: Optional[str] = None
        
        # Compute ?a (all printable)
        self.MASK_CHARS['?a'] = (
            self.MASK_CHARS['?l'] +
            self.MASK_CHARS['?u'] +
            self.MASK_CHARS['?d'] +
            self.MASK_CHARS['?s']
        )
        
        # Parse mask
        self.mask_positions = self._parse_mask(mask)
    
    def _parse_mask(self, mask: str) -> list:
        """
        Parse mask into position definitions.
        
        Args:
            mask: Mask string
            
        Returns:
            List of character sets for each position
        """
        positions = []
        i = 0
        
        while i < len(mask):
            # Check for mask placeholder
            if i < len(mask) - 1 and mask[i:i+2] in self.MASK_CHARS:
                placeholder = mask[i:i+2]
                positions.append(self.MASK_CHARS[placeholder])
                i += 2
            else:
                # Literal character
                positions.append(mask[i])
                i += 1
        
        return positions
    
    def attack(
        self,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        max_attempts: Optional[int] = None
    ) -> Optional[str]:
        """
        Perform mask attack.
        
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
            raise RuntimeError(f"Mask attack failed: {e}")
    
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
        Generate all password candidates from mask.
        
        Yields:
            Password candidates
        """
        # Prepare charset lists for each position
        charsets = []
        for pos in self.mask_positions:
            if isinstance(pos, str) and len(pos) == 1:
                # Literal character - single option
                charsets.append([pos])
            else:
                # Character set - multiple options
                charsets.append(list(pos))
        
        # Generate all combinations
        for combo in itertools.product(*charsets):
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
        total = 1
        for pos in self.mask_positions:
            if isinstance(pos, str) and len(pos) == 1:
                # Literal - 1 option
                total *= 1
            else:
                # Character set
                total *= len(pos)
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
            "mask": self.mask,
            "estimated_total": self.estimate_total_attempts()
        }
    
    @staticmethod
    def build_mask(pattern: str) -> str:
        """
        Build a mask from a human-readable pattern.
        
        Args:
            pattern: Pattern description (e.g., "3l2d" = 3 lowercase, 2 digits)
            
        Returns:
            Mask string
        """
        mask = ""
        i = 0
        
        while i < len(pattern):
            # Try to read a number
            num_str = ""
            while i < len(pattern) and pattern[i].isdigit():
                num_str += pattern[i]
                i += 1
            
            count = int(num_str) if num_str else 1
            
            # Read the type
            if i < len(pattern):
                char_type = pattern[i]
                type_map = {
                    'l': '?l',
                    'u': '?u',
                    'd': '?d',
                    's': '?s',
                    'a': '?a',
                    'h': '?h',
                    'H': '?H',
                }
                mask += type_map.get(char_type, char_type) * count
                i += 1
        
        return mask
