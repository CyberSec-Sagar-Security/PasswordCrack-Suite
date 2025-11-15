"""
Wordlist management module.

Handles loading, saving, merging, and cleaning wordlists.
All operations are local file-based only.
"""

import os
from typing import List, Set, Iterator, Optional
from pathlib import Path


class WordlistManager:
    """Manages wordlist files for dictionary attacks."""
    
    def __init__(self, wordlist_dir: Optional[Path] = None):
        """
        Initialize the wordlist manager.
        
        Args:
            wordlist_dir: Directory containing wordlists (default: examples/wordlists)
        """
        if wordlist_dir is None:
            # Use examples/wordlists relative to project root
            self.wordlist_dir = Path(__file__).parent.parent.parent / "examples" / "wordlists"
        else:
            self.wordlist_dir = Path(wordlist_dir)
        
        self.wordlist_dir.mkdir(parents=True, exist_ok=True)
    
    def load_wordlist(self, filename: str, encoding: str = 'utf-8') -> Iterator[str]:
        """
        Load a wordlist file and yield words.
        
        Args:
            filename: Name of the wordlist file
            encoding: File encoding (default: utf-8)
            
        Yields:
            Individual words from the wordlist
        """
        filepath = self.wordlist_dir / filename if not os.path.isabs(filename) else Path(filename)
        
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):  # Skip empty lines and comments
                        yield word
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist not found: {filepath}")
        except Exception as e:
            raise IOError(f"Error reading wordlist {filepath}: {e}")
    
    def load_wordlist_to_list(self, filename: str, max_words: Optional[int] = None) -> List[str]:
        """
        Load entire wordlist into memory.
        
        Args:
            filename: Name of the wordlist file
            max_words: Maximum number of words to load (None = all)
            
        Returns:
            List of words
        """
        words = []
        for i, word in enumerate(self.load_wordlist(filename)):
            if max_words and i >= max_words:
                break
            words.append(word)
        return words
    
    def save_wordlist(self, filename: str, words: List[str], overwrite: bool = False) -> None:
        """
        Save words to a wordlist file.
        
        Args:
            filename: Name of the output file
            words: List of words to save
            overwrite: Whether to overwrite existing file
        """
        filepath = self.wordlist_dir / filename if not os.path.isabs(filename) else Path(filename)
        
        if filepath.exists() and not overwrite:
            raise FileExistsError(f"Wordlist already exists: {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word}\n")
    
    def merge_wordlists(
        self,
        input_files: List[str],
        output_file: str,
        deduplicate: bool = True,
        sort: bool = False
    ) -> int:
        """
        Merge multiple wordlists into one.
        
        Args:
            input_files: List of input wordlist filenames
            output_file: Output filename
            deduplicate: Remove duplicate words
            sort: Sort the output alphabetically
            
        Returns:
            Number of words in merged wordlist
        """
        words: Set[str] = set() if deduplicate else []
        
        for input_file in input_files:
            for word in self.load_wordlist(input_file):
                if deduplicate:
                    words.add(word)
                else:
                    words.append(word)
        
        word_list = sorted(words) if sort else list(words)
        self.save_wordlist(output_file, word_list, overwrite=True)
        
        return len(word_list)
    
    def clean_wordlist(
        self,
        input_file: str,
        output_file: str,
        min_length: int = 1,
        max_length: int = 128,
        remove_non_ascii: bool = False
    ) -> int:
        """
        Clean and filter a wordlist.
        
        Args:
            input_file: Input wordlist filename
            output_file: Output wordlist filename
            min_length: Minimum word length
            max_length: Maximum word length
            remove_non_ascii: Remove words with non-ASCII characters
            
        Returns:
            Number of words in cleaned wordlist
        """
        cleaned_words = []
        
        for word in self.load_wordlist(input_file):
            # Length filter
            if len(word) < min_length or len(word) > max_length:
                continue
            
            # ASCII filter
            if remove_non_ascii and not word.isascii():
                continue
            
            cleaned_words.append(word)
        
        self.save_wordlist(output_file, cleaned_words, overwrite=True)
        return len(cleaned_words)
    
    def deduplicate_wordlist(self, input_file: str, output_file: str) -> int:
        """
        Remove duplicates from a wordlist while preserving order.
        
        Args:
            input_file: Input wordlist filename
            output_file: Output wordlist filename
            
        Returns:
            Number of unique words
        """
        seen: Set[str] = set()
        unique_words = []
        
        for word in self.load_wordlist(input_file):
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        self.save_wordlist(output_file, unique_words, overwrite=True)
        return len(unique_words)
    
    def get_wordlist_info(self, filename: str) -> dict:
        """
        Get information about a wordlist.
        
        Args:
            filename: Wordlist filename
            
        Returns:
            Dict with wordlist statistics
        """
        filepath = self.wordlist_dir / filename if not os.path.isabs(filename) else Path(filename)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Wordlist not found: {filepath}")
        
        word_count = 0
        total_length = 0
        min_len = float('inf')
        max_len = 0
        
        for word in self.load_wordlist(filename):
            word_count += 1
            length = len(word)
            total_length += length
            min_len = min(min_len, length)
            max_len = max(max_len, length)
        
        avg_len = total_length / word_count if word_count > 0 else 0
        
        return {
            "filename": filename,
            "path": str(filepath),
            "word_count": word_count,
            "file_size": filepath.stat().st_size,
            "min_length": min_len if min_len != float('inf') else 0,
            "max_length": max_len,
            "avg_length": round(avg_len, 2)
        }
    
    def list_wordlists(self) -> List[str]:
        """
        List all wordlist files in the wordlist directory.
        
        Returns:
            List of wordlist filenames
        """
        if not self.wordlist_dir.exists():
            return []
        
        return [f.name for f in self.wordlist_dir.glob("*.txt")]
