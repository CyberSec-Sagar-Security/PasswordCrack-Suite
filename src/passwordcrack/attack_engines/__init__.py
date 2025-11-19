"""
Attack engines package.

Contains all password cracking attack implementations.
NOTE: ALL ENGINES WORK OFFLINE ONLY - NO NETWORK ATTACKS
"""

from .dictionary_engine import DictionaryEngine
from .bruteforce_engine import BruteforceEngine
from .mask_engine import MaskEngine
from .hybrid_engine import HybridEngine
from .rule_engine import RuleEngine

# GPU-accelerated engines (optional - requires hashcat)
try:
    from .gpx_engine import GPXDictionaryEngine, GPXBruteforceEngine
    __all__ = [
        'DictionaryEngine',
        'BruteforceEngine',
        'MaskEngine',
        'HybridEngine',
        'RuleEngine',
        'GPXDictionaryEngine',
        'GPXBruteforceEngine',
    ]
except ImportError:
    __all__ = [
        'DictionaryEngine',
        'BruteforceEngine',
        'MaskEngine',
        'HybridEngine',
        'RuleEngine',
    ]
