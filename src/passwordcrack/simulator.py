"""
Simulator module for demo scenarios and testing.

Creates synthetic test hashes and automated demo flows.
NOTE: EDUCATIONAL DEMOS ONLY - NO REAL ATTACKS
"""

from typing import Dict, Any, List, Optional
import secrets
import random
from .hash_utils import HashUtils, HashAlgorithm
from .wordlist_manager import WordlistManager


class DemoSimulator:
    """Simulates cracking scenarios for demos and training."""
    
    # Common demo passwords
    DEMO_PASSWORDS = [
        "password",
        "password123",
        "admin",
        "letmein",
        "qwerty",
        "welcome",
        "monkey",
        "dragon",
        "master",
        "sunshine",
    ]
    
    def __init__(self):
        """Initialize demo simulator."""
        self.scenarios: List[Dict[str, Any]] = []
    
    def create_demo_hash(
        self,
        password: Optional[str] = None,
        algorithm: HashAlgorithm = HashAlgorithm.MD5
    ) -> Dict[str, str]:
        """
        Create a demo hash for testing.
        
        Args:
            password: Password to hash (random if None)
            algorithm: Hash algorithm to use
            
        Returns:
            Dict with password and hash
        """
        if password is None:
            password = random.choice(self.DEMO_PASSWORDS)
        
        hash_value = HashUtils.generate_hash(password, algorithm)
        
        return {
            "password": password,
            "hash": hash_value,
            "algorithm": algorithm.value
        }
    
    def create_demo_scenario(
        self,
        scenario_type: str = "easy",
        algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> Dict[str, Any]:
        """
        Create a complete demo scenario.
        
        Args:
            scenario_type: Difficulty (easy, medium, hard)
            algorithm: Hash algorithm
            
        Returns:
            Demo scenario dictionary
        """
        scenarios = {
            "easy": {
                "description": "Easy demo: Common password with MD5",
                "password": "password123",
                "algorithm": HashAlgorithm.MD5,
                "recommended_attack": "dictionary",
                "wordlist": "common.txt",
                "estimated_time": "< 1 second"
            },
            "medium": {
                "description": "Medium demo: Modified word with SHA-256",
                "password": "P@ssw0rd!",
                "algorithm": HashAlgorithm.SHA256,
                "recommended_attack": "rule-based",
                "wordlist": "common.txt",
                "estimated_time": "< 5 seconds"
            },
            "hard": {
                "description": "Hard demo: Short password with brute-force",
                "password": "abc123",
                "algorithm": HashAlgorithm.SHA256,
                "recommended_attack": "brute-force",
                "charset": "lowercase+digits",
                "max_length": 6,
                "estimated_time": "< 30 seconds"
            }
        }
        
        scenario = scenarios.get(scenario_type, scenarios["easy"])
        
        # Generate hash
        password = scenario["password"]
        algo = scenario.get("algorithm", algorithm)
        hash_value = HashUtils.generate_hash(password, algo)
        
        scenario["hash"] = hash_value
        scenario["scenario_type"] = scenario_type
        
        return scenario
    
    def create_multiple_hashes(
        self,
        count: int = 10,
        algorithm: HashAlgorithm = HashAlgorithm.MD5,
        use_common: bool = True
    ) -> List[Dict[str, str]]:
        """
        Create multiple demo hashes.
        
        Args:
            count: Number of hashes to create
            algorithm: Hash algorithm
            use_common: Use common passwords vs random strings
            
        Returns:
            List of hash dictionaries
        """
        hashes = []
        
        for i in range(count):
            if use_common and i < len(self.DEMO_PASSWORDS):
                password = self.DEMO_PASSWORDS[i]
            else:
                # Generate random password
                password = secrets.token_urlsafe(8)
            
            hash_dict = self.create_demo_hash(password, algorithm)
            hash_dict["index"] = i + 1
            hashes.append(hash_dict)
        
        return hashes
    
    def simulate_weak_passwords(self, count: int = 50) -> List[str]:
        """
        Generate a list of intentionally weak passwords for demos.
        
        Args:
            count: Number of passwords to generate
            
        Returns:
            List of weak passwords
        """
        weak_patterns = [
            lambda: random.choice(self.DEMO_PASSWORDS),
            lambda: random.choice(self.DEMO_PASSWORDS) + str(random.randint(0, 99)),
            lambda: random.choice(self.DEMO_PASSWORDS) + str(random.randint(2000, 2025)),
            lambda: random.choice(['admin', 'user', 'test']) + str(random.randint(1, 999)),
            lambda: random.choice(['qwerty', 'abc', 'xyz']) + str(random.randint(100, 999)),
        ]
        
        passwords = []
        for _ in range(count):
            pattern = random.choice(weak_patterns)
            passwords.append(pattern())
        
        return passwords
    
    def create_training_dataset(
        self,
        output_dir: str = "demo/training_data"
    ) -> Dict[str, Any]:
        """
        Create a complete training dataset with hashes and wordlists.
        
        Args:
            output_dir: Directory to save training files
            
        Returns:
            Dict with dataset information
        """
        from pathlib import Path
        import json
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create hashes for different algorithms
        algorithms = [HashAlgorithm.MD5, HashAlgorithm.SHA1, HashAlgorithm.SHA256]
        all_hashes = {}
        
        for algo in algorithms:
            hashes = self.create_multiple_hashes(10, algo, use_common=True)
            all_hashes[algo.value] = hashes
            
            # Save to file
            hash_file = output_path / f"hashes_{algo.value}.json"
            with open(hash_file, 'w') as f:
                json.dump(hashes, f, indent=2)
        
        # Create weak password wordlist
        weak_passwords = self.simulate_weak_passwords(100)
        wordlist_file = output_path / "weak_passwords.txt"
        with open(wordlist_file, 'w') as f:
            for pwd in weak_passwords:
                f.write(f"{pwd}\n")
        
        # Create README
        readme_file = output_path / "README.txt"
        with open(readme_file, 'w') as f:
            f.write("TRAINING DATASET - EDUCATIONAL USE ONLY\n")
            f.write("=" * 50 + "\n\n")
            f.write("This dataset contains:\n")
            f.write(f"- Hash files for {len(algorithms)} algorithms\n")
            f.write(f"- {len(weak_passwords)} weak passwords for testing\n\n")
            f.write("Use these files to practice password cracking in a safe,\n")
            f.write("controlled environment.\n\n")
            f.write("NEVER use these techniques on real systems without permission!\n")
        
        return {
            "output_dir": str(output_path),
            "algorithms": [algo.value for algo in algorithms],
            "hash_count_per_algo": 10,
            "wordlist_size": len(weak_passwords),
            "files_created": [
                str(f.name) for f in output_path.glob("*")
            ]
        }
    
    def get_demo_script(self, scenario_type: str = "easy") -> str:
        """
        Get a demo script with instructions.
        
        Args:
            scenario_type: Demo difficulty
            
        Returns:
            Demo script as string
        """
        scenario = self.create_demo_scenario(scenario_type)
        
        script = f"""
DEMO SCRIPT - {scenario_type.upper()} SCENARIO
{'=' * 60}

Description: {scenario['description']}

Target Hash: {scenario['hash']}
Algorithm: {scenario.get('algorithm', 'N/A')}

Recommended Attack: {scenario['recommended_attack']}
Estimated Time: {scenario['estimated_time']}

STEPS:
1. Copy the hash above
2. Select hash algorithm: {scenario.get('algorithm', 'N/A')}
3. Choose attack type: {scenario['recommended_attack']}
"""
        
        if scenario['recommended_attack'] == 'dictionary':
            script += f"4. Select wordlist: {scenario.get('wordlist', 'common.txt')}\n"
        elif scenario['recommended_attack'] == 'brute-force':
            script += f"4. Set charset: {scenario.get('charset', 'all')}\n"
            script += f"5. Set max length: {scenario.get('max_length', 6)}\n"
        
        script += f"""
5. Start the attack
6. Wait for results

Expected Password: {scenario['password']}

NOTE: This is a controlled demo environment for learning purposes only.
{'=' * 60}
"""
        
        return script
