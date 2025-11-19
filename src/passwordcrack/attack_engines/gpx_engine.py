"""
GPU-Accelerated Attack Engine.

Provides GPU/CPU-accelerated password cracking using Hashcat integration.
Falls back to CPU-only mode if GPU is unavailable.

NOTE: EDUCATIONAL USE ONLY - REQUIRES HASHCAT
"""

from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
from ..hash_utils import HashAlgorithm
from ..gpx_manager import GPXManager, GPXDevice, DeviceType
from ..hashcat_wrapper import HashcatWrapper, HashcatMode
from ..wordlist_manager import WordlistManager


class GPXDictionaryEngine:
    """GPU-accelerated dictionary attack engine."""
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        gpx_manager: GPXManager,
        hashcat_wrapper: HashcatWrapper
    ):
        """
        Initialize GPU-accelerated dictionary engine.
        
        Args:
            hash_value: Target hash to crack
            algorithm: Hash algorithm
            gpx_manager: GPX manager instance
            hashcat_wrapper: Hashcat wrapper instance
        """
        self.hash_value = hash_value.strip().lower()
        self.algorithm = algorithm
        self.gpx_manager = gpx_manager
        self.hashcat_wrapper = hashcat_wrapper
        self.attempts = 0
        self.found = False
        self.found_password: Optional[str] = None
    
    def attack(
        self,
        wordlist_file: str,
        wordlist_manager: WordlistManager,
        use_gpu: bool = True,
        mixed_mode: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Perform GPU-accelerated dictionary attack.
        
        Args:
            wordlist_file: Wordlist filename
            wordlist_manager: Wordlist manager instance
            use_gpu: Use GPU if available
            mixed_mode: Allow CPU + GPU together
            progress_callback: Optional progress callback
            
        Returns:
            Cracked password if found, None otherwise
        """
        # Get wordlist path
        wordlist_path = self._resolve_wordlist_path(wordlist_file)
        if not wordlist_path or not wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist not found: {wordlist_file}")
        
        # Select devices
        devices = self._select_devices(use_gpu, mixed_mode)
        
        # Verify devices are available
        all_available, available_devices = self.hashcat_wrapper.verify_devices_available(devices)
        if not all_available:
            # Fallback to available devices
            devices = available_devices
            if not devices:
                raise RuntimeError("No compute devices available")
        
        # Convert algorithm to hashcat mode
        hash_mode = HashcatMode.from_algorithm(self.algorithm)
        
        # Run hashcat dictionary attack
        result = self.hashcat_wrapper.crack_dictionary(
            hash_value=self.hash_value,
            hash_mode=hash_mode,
            wordlist_path=wordlist_path,
            devices=devices
        )
        
        # Process result
        if result.get("status") == "error":
            error_msg = result.get("message", "Unknown hashcat error")
            raise RuntimeError(f"Hashcat dictionary error: {error_msg}")
        
        if result.get("status") == "cracked":
            self.found = True
            self.found_password = result["password"]
            return result["password"]
        
        return None
    
    def _resolve_wordlist_path(self, wordlist_file: str) -> Optional[Path]:
        """Resolve wordlist path."""
        # Try relative to examples/
        path = Path("examples") / wordlist_file
        if path.exists():
            return path
        
        # Try relative to CWD
        path = Path.cwd() / "examples" / wordlist_file
        if path.exists():
            return path
        
        # Try absolute path
        path = Path(wordlist_file)
        if path.exists():
            return path
        
        return None
    
    def _select_devices(self, use_gpu: bool, mixed_mode: bool) -> List[GPXDevice]:
        """
        Select devices for attack.
        
        Args:
            use_gpu: Use GPU if available
            mixed_mode: Allow CPU + GPU
            
        Returns:
            List of selected devices
        """
        devices = []
        
        if use_gpu and self.gpx_manager.is_gpu_available():
            # Get best GPU
            best_gpu = self.gpx_manager.get_best_device()
            if best_gpu.device_type == DeviceType.GPU:
                devices.append(best_gpu)
            
            # Add CPU if mixed mode
            if mixed_mode:
                cpu = self.gpx_manager.get_cpu_device()
                if cpu:
                    devices.append(cpu)
        else:
            # CPU only
            cpu = self.gpx_manager.get_cpu_device()
            if cpu:
                devices.append(cpu)
        
        return devices


class GPXBruteforceEngine:
    """GPU-accelerated brute-force/mask attack engine."""
    
    def __init__(
        self,
        hash_value: str,
        algorithm: HashAlgorithm,
        gpx_manager: GPXManager,
        hashcat_wrapper: HashcatWrapper
    ):
        """
        Initialize GPU-accelerated brute-force engine.
        
        Args:
            hash_value: Target hash to crack
            algorithm: Hash algorithm
            gpx_manager: GPX manager instance
            hashcat_wrapper: Hashcat wrapper instance
        """
        self.hash_value = hash_value.strip().lower()
        self.algorithm = algorithm
        self.gpx_manager = gpx_manager
        self.hashcat_wrapper = hashcat_wrapper
        self.attempts = 0
        self.found = False
        self.found_password: Optional[str] = None
    
    def attack(
        self,
        mask: str,
        use_gpu: bool = True,
        mixed_mode: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Perform GPU-accelerated brute-force attack.
        
        Args:
            mask: Character mask (e.g., "?l?l?l?l?d?d")
            use_gpu: Use GPU if available
            mixed_mode: Allow CPU + GPU together
            progress_callback: Optional progress callback
            
        Returns:
            Cracked password if found, None otherwise
        """
        # Select devices
        devices = self._select_devices(use_gpu, mixed_mode)
        
        # Verify devices
        all_available, available_devices = self.hashcat_wrapper.verify_devices_available(devices)
        if not all_available:
            devices = available_devices
            if not devices:
                raise RuntimeError("No compute devices available")
        
        # Convert algorithm to hashcat mode
        hash_mode = HashcatMode.from_algorithm(self.algorithm)
        
        # Run hashcat brute-force attack
        result = self.hashcat_wrapper.crack_bruteforce(
            hash_value=self.hash_value,
            hash_mode=hash_mode,
            mask=mask,
            devices=devices,
            progress_callback=progress_callback
        )
        
        # Extract stats from result
        stats = result.get('stats', {})
        self.attempts = stats.get('progress', 0)  # Update attempts from hashcat stats
        
        # Process result
        if result.get("status") == "error":
            error_msg = result.get("message", "Unknown hashcat error")
            raise RuntimeError(f"Hashcat brute-force error: {error_msg}")
        
        if result.get("status") == "cracked":
            self.found = True
            self.found_password = result["password"]
            return result["password"]
        
        return None
    
    def _select_devices(self, use_gpu: bool, mixed_mode: bool) -> List[GPXDevice]:
        """Select devices for attack."""
        devices = []
        
        if use_gpu and self.gpx_manager.is_gpu_available():
            best_gpu = self.gpx_manager.get_best_device()
            if best_gpu.device_type == DeviceType.GPU:
                devices.append(best_gpu)
            
            if mixed_mode:
                cpu = self.gpx_manager.get_cpu_device()
                if cpu:
                    devices.append(cpu)
        else:
            cpu = self.gpx_manager.get_cpu_device()
            if cpu:
                devices.append(cpu)
        
        return devices
    
    def estimate_time(self, mask: str) -> Dict[str, Any]:
        """
        Estimate time to complete mask attack.
        
        Args:
            mask: Character mask
            
        Returns:
            Estimation data
        """
        keyspace = self.hashcat_wrapper.calculate_mask_keyspace(mask)
        
        # Get device speed
        hash_mode = HashcatMode.from_algorithm(self.algorithm)
        best_device = self.gpx_manager.get_best_device()
        
        speed = best_device.benchmark_results.get(hash_mode, 0.0)
        if speed == 0.0:
            speed = self.gpx_manager.benchmark_device(best_device, hash_mode)
        
        seconds, formatted = self.hashcat_wrapper.get_estimated_time(keyspace, speed)
        
        return {
            "keyspace": keyspace,
            "speed_h_per_s": speed,
            "speed_formatted": self.gpx_manager.format_hash_rate(speed),
            "estimated_seconds": seconds,
            "estimated_time": formatted
        }
