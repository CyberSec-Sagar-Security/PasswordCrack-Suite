"""
Command-line interface for PasswordCrack Suite.

Alternative CLI mode for terminal users.
NOTE: EDUCATIONAL USE ONLY
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .hash_utils import HashUtils, HashAlgorithm
from .hash_identifier import HashIdentifier
from .wordlist_manager import WordlistManager
from .attack_engines import DictionaryEngine, BruteforceEngine, MaskEngine
from .session_manager import SessionManager
from .results_analyzer import ResultsAnalyzer
from .performance.benchmark import PerformanceBenchmark
from .simulator import DemoSimulator


class PasswordCrackCLI:
    """Command-line interface for password cracking."""
    
    def __init__(self):
        """Initialize CLI."""
        self.wordlist_manager = WordlistManager()
        self.session_manager = SessionManager()
        self.results_analyzer = ResultsAnalyzer()
        self.simulator = DemoSimulator()
    
    def show_ethics_warning(self) -> bool:
        """Show ethics warning and get consent."""
        print("\n" + "=" * 70)
        print("⚠️  ETHICAL USE WARNING ⚠️")
        print("=" * 70)
        print("\nThis tool is for EDUCATIONAL USE ONLY.")
        print("You must only use it on systems you own or have permission to test.")
        print("\nBy continuing, you agree to use this tool ethically and legally.")
        print("=" * 70)
        
        response = input("\nDo you accept these terms? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def cmd_hash(self, args: argparse.Namespace) -> None:
        """Generate a hash from a password."""
        algorithm = HashAlgorithm[args.algorithm.upper()]
        hash_value = HashUtils.generate_hash(args.password, algorithm)
        
        print(f"\nAlgorithm: {algorithm.value}")
        print(f"Password:  {args.password}")
        print(f"Hash:      {hash_value}\n")
    
    def cmd_identify(self, args: argparse.Namespace) -> None:
        """Identify hash type."""
        results = HashIdentifier.identify_with_details(args.hash)
        
        print(f"\nHash: {args.hash}")
        print("\nPossible types:")
        for result in results:
            print(f"  - {result['description']}")
        
        if not results:
            print("  No matches found")
        print()
    
    def cmd_crack(self, args: argparse.Namespace) -> None:
        """Perform password cracking."""
        print(f"\nStarting {args.attack} attack...")
        print(f"Hash: {args.hash}")
        print(f"Algorithm: {args.algorithm}\n")
        
        algorithm = HashAlgorithm[args.algorithm.upper()]
        
        if args.attack == 'dictionary':
            self._run_dictionary_attack(args.hash, algorithm, args.wordlist)
        elif args.attack == 'bruteforce':
            self._run_bruteforce_attack(args.hash, algorithm, args.max_length)
        elif args.attack == 'mask':
            self._run_mask_attack(args.hash, algorithm, args.mask)
        else:
            print(f"Unknown attack type: {args.attack}")
    
    def _run_dictionary_attack(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        wordlist: str
    ) -> None:
        """Run dictionary attack."""
        engine = DictionaryEngine(hash_value, algorithm, self.wordlist_manager)
        
        def progress_callback(attempts: int, word: str) -> None:
            print(f"\rAttempts: {attempts:,} | Current: {word:<30}", end='', flush=True)
        
        result = engine.attack(wordlist, progress_callback)
        
        print(f"\n\nTotal attempts: {engine.attempts:,}")
        
        if result:
            print(f"✓ Password found: {result}")
        else:
            print("✗ Password not found")
    
    def _run_bruteforce_attack(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        max_length: int
    ) -> None:
        """Run brute-force attack."""
        engine = BruteforceEngine(
            hash_value,
            algorithm,
            charset='lowercase',
            min_length=1,
            max_length=max_length
        )
        
        print(f"Keyspace size: {engine.estimate_total_attempts():,}\n")
        
        def progress_callback(attempts: int, candidate: str) -> None:
            print(f"\rAttempts: {attempts:,} | Current: {candidate:<20}", end='', flush=True)
        
        result = engine.attack(progress_callback, max_attempts=100000)
        
        print(f"\n\nTotal attempts: {engine.attempts:,}")
        
        if result:
            print(f"✓ Password found: {result}")
        else:
            print("✗ Password not found (max attempts reached)")
    
    def _run_mask_attack(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        mask: str
    ) -> None:
        """Run mask attack."""
        engine = MaskEngine(hash_value, algorithm, mask)
        
        print(f"Mask: {mask}")
        print(f"Keyspace size: {engine.estimate_total_attempts():,}\n")
        
        def progress_callback(attempts: int, candidate: str) -> None:
            print(f"\rAttempts: {attempts:,} | Current: {candidate:<20}", end='', flush=True)
        
        result = engine.attack(progress_callback, max_attempts=100000)
        
        print(f"\n\nTotal attempts: {engine.attempts:,}")
        
        if result:
            print(f"✓ Password found: {result}")
        else:
            print("✗ Password not found (max attempts reached)")
    
    def cmd_benchmark(self, args: argparse.Namespace) -> None:
        """Run performance benchmark."""
        print("\nRunning benchmark (this may take a few seconds)...\n")
        
        benchmark = PerformanceBenchmark(test_duration=2.0)
        benchmark.benchmark_all()
        benchmark.print_results()
    
    def cmd_demo(self, args: argparse.Namespace) -> None:
        """Run a demo scenario."""
        demo = self.simulator.create_demo_scenario(args.difficulty)
        script = self.simulator.get_demo_script(args.difficulty)
        
        print(script)
        
        if args.run:
            print("\nRunning demo attack...")
            algorithm = HashAlgorithm[demo['algorithm'].name]
            self._run_dictionary_attack(
                demo['hash'],
                algorithm,
                demo.get('wordlist', 'common.txt')
            )
    
    def cmd_wordlist(self, args: argparse.Namespace) -> None:
        """Wordlist management."""
        if args.list:
            wordlists = self.wordlist_manager.list_wordlists()
            print("\nAvailable wordlists:")
            for wl in wordlists:
                info = self.wordlist_manager.get_wordlist_info(wl)
                print(f"  - {wl} ({info['word_count']:,} words)")
            print()
        
        elif args.info:
            info = self.wordlist_manager.get_wordlist_info(args.info)
            print(f"\nWordlist: {info['filename']}")
            print(f"Path: {info['path']}")
            print(f"Words: {info['word_count']:,}")
            print(f"Size: {info['file_size']:,} bytes")
            print(f"Length range: {info['min_length']}-{info['max_length']}")
            print(f"Average length: {info['avg_length']}\n")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PasswordCrack Suite - Educational Password Security Tool",
        epilog="⚠️  EDUCATIONAL USE ONLY - Use responsibly and ethically!"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Hash generation
    hash_parser = subparsers.add_parser('hash', help='Generate hash from password')
    hash_parser.add_argument('password', help='Password to hash')
    hash_parser.add_argument('-a', '--algorithm', default='sha256',
                            choices=['md5', 'sha1', 'sha256', 'sha512', 'ntlm'],
                            help='Hash algorithm')
    
    # Hash identification
    identify_parser = subparsers.add_parser('identify', help='Identify hash type')
    identify_parser.add_argument('hash', help='Hash to identify')
    
    # Cracking
    crack_parser = subparsers.add_parser('crack', help='Crack a password hash')
    crack_parser.add_argument('hash', help='Hash to crack')
    crack_parser.add_argument('-a', '--algorithm', default='sha256',
                             choices=['md5', 'sha1', 'sha256', 'sha512', 'ntlm'],
                             help='Hash algorithm')
    crack_parser.add_argument('-t', '--attack', default='dictionary',
                             choices=['dictionary', 'bruteforce', 'mask'],
                             help='Attack type')
    crack_parser.add_argument('-w', '--wordlist', default='common.txt',
                             help='Wordlist file')
    crack_parser.add_argument('-m', '--mask', default='?l?l?l?d?d',
                             help='Mask pattern')
    crack_parser.add_argument('-l', '--max-length', type=int, default=4,
                             help='Max length for brute-force')
    
    # Benchmark
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmark')
    
    # Demo
    demo_parser = subparsers.add_parser('demo', help='Run demo scenario')
    demo_parser.add_argument('-d', '--difficulty', default='easy',
                            choices=['easy', 'medium', 'hard'],
                            help='Demo difficulty')
    demo_parser.add_argument('-r', '--run', action='store_true',
                            help='Actually run the demo attack')
    
    # Wordlist management
    wordlist_parser = subparsers.add_parser('wordlist', help='Manage wordlists')
    wordlist_parser.add_argument('--list', action='store_true',
                                help='List available wordlists')
    wordlist_parser.add_argument('--info', metavar='FILE',
                                help='Show wordlist info')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Create CLI instance
    cli = PasswordCrackCLI()
    
    # Show ethics warning for crack command
    if args.command == 'crack':
        if not cli.show_ethics_warning():
            print("\nYou must accept the terms to use this tool.")
            return 1
    
    # Dispatch to command handler
    command_handlers = {
        'hash': cli.cmd_hash,
        'identify': cli.cmd_identify,
        'crack': cli.cmd_crack,
        'benchmark': cli.cmd_benchmark,
        'demo': cli.cmd_demo,
        'wordlist': cli.cmd_wordlist,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            handler(args)
            return 0
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
