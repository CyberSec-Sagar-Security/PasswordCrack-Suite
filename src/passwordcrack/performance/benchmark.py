"""
Performance and benchmarking module.

Measures hashing performance and provides multi-threading support.
NOTE: LOCAL BENCHMARKING ONLY - NO NETWORK
"""

import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Dict, Any
from ..hash_utils import HashUtils, HashAlgorithm


class PerformanceBenchmark:
    """Performance benchmarking for hash algorithms."""
    
    def __init__(self, test_duration: float = 2.0):
        """
        Initialize benchmark.
        
        Args:
            test_duration: Duration in seconds for each test
        """
        self.test_duration = test_duration
        self.results: Dict[str, Any] = {}
    
    def benchmark_algorithm(
        self,
        algorithm: HashAlgorithm,
        test_data: str = "benchmark_test_password"
    ) -> Dict[str, Any]:
        """
        Benchmark a specific hashing algorithm.
        
        Args:
            algorithm: Algorithm to benchmark
            test_data: Test string to hash
            
        Returns:
            Benchmark results dictionary
        """
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < self.test_duration:
            try:
                HashUtils.generate_hash(test_data, algorithm)
                attempts += 1
            except Exception as e:
                return {
                    "algorithm": algorithm.value,
                    "error": str(e),
                    "hashes_per_second": 0
                }
        
        elapsed = time.time() - start_time
        hashes_per_sec = attempts / elapsed
        
        return {
            "algorithm": algorithm.value,
            "total_hashes": attempts,
            "duration": round(elapsed, 2),
            "hashes_per_second": round(hashes_per_sec, 2),
            "ms_per_hash": round(1000 / hashes_per_sec, 4) if hashes_per_sec > 0 else 0
        }
    
    def benchmark_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Benchmark all available algorithms.
        
        Returns:
            Dictionary mapping algorithm names to results
        """
        results = {}
        available = HashUtils.get_available_algorithms()
        
        for algo_name, is_available in available.items():
            if is_available:
                try:
                    algo_enum = HashAlgorithm[algo_name]
                    results[algo_name] = self.benchmark_algorithm(algo_enum)
                except Exception as e:
                    results[algo_name] = {"error": str(e)}
        
        self.results = results
        return results
    
    def get_fastest_algorithm(self) -> Optional[str]:
        """
        Get the fastest algorithm from benchmark results.
        
        Returns:
            Algorithm name or None
        """
        if not self.results:
            return None
        
        fastest = None
        max_speed = 0
        
        for algo, data in self.results.items():
            speed = data.get("hashes_per_second", 0)
            if speed > max_speed:
                max_speed = speed
                fastest = algo
        
        return fastest
    
    def print_results(self) -> None:
        """Print benchmark results in a formatted table."""
        if not self.results:
            print("No benchmark results available. Run benchmark_all() first.")
            return
        
        print("\n" + "=" * 70)
        print("HASH ALGORITHM PERFORMANCE BENCHMARK")
        print("=" * 70)
        print(f"{'Algorithm':<20} {'Hashes/sec':<15} {'ms/hash':<12} {'Status':<10}")
        print("-" * 70)
        
        for algo, data in sorted(self.results.items()):
            if "error" in data:
                print(f"{algo:<20} {'N/A':<15} {'N/A':<12} {'Error':<10}")
            else:
                hps = f"{data['hashes_per_second']:,.0f}"
                ms = f"{data['ms_per_hash']:.4f}"
                print(f"{algo:<20} {hps:<15} {ms:<12} {'OK':<10}")
        
        print("=" * 70 + "\n")


class MultiThreadedCracker:
    """Multi-threaded password cracking support."""
    
    def __init__(self, num_threads: int = 4):
        """
        Initialize multi-threaded cracker.
        
        Args:
            num_threads: Number of worker threads
        """
        self.num_threads = num_threads
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        self.active_tasks: List = []
    
    def split_work(
        self,
        candidates: List[str],
        worker_func: Callable,
        *args
    ) -> List[Any]:
        """
        Split work across threads.
        
        Args:
            candidates: List of password candidates
            worker_func: Function to execute for each batch
            *args: Additional arguments for worker_func
            
        Returns:
            List of results from all workers
        """
        # Split candidates into chunks
        chunk_size = max(1, len(candidates) // self.num_threads)
        chunks = [
            candidates[i:i + chunk_size]
            for i in range(0, len(candidates), chunk_size)
        ]
        
        # Submit tasks
        futures = []
        for chunk in chunks:
            future = self.executor.submit(worker_func, chunk, *args)
            futures.append(future)
            self.active_tasks.append(future)
        
        # Gather results
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        
        return results
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the thread pool.
        
        Args:
            wait: Whether to wait for tasks to complete
        """
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


def estimate_crack_time(
    keyspace_size: int,
    hashes_per_second: float
) -> Dict[str, Any]:
    """
    Estimate time to crack based on keyspace and speed.
    
    Args:
        keyspace_size: Total number of possible passwords
        hashes_per_second: Cracking speed
        
    Returns:
        Dictionary with time estimates
    """
    if hashes_per_second <= 0:
        return {"error": "Invalid hashing speed"}
    
    total_seconds = keyspace_size / hashes_per_second
    
    # Convert to various units
    minutes = total_seconds / 60
    hours = minutes / 60
    days = hours / 24
    years = days / 365.25
    
    # Determine best unit
    if total_seconds < 60:
        time_str = f"{total_seconds:.2f} seconds"
    elif minutes < 60:
        time_str = f"{minutes:.2f} minutes"
    elif hours < 24:
        time_str = f"{hours:.2f} hours"
    elif days < 365:
        time_str = f"{days:.2f} days"
    else:
        time_str = f"{years:.2f} years"
    
    return {
        "keyspace_size": keyspace_size,
        "hashes_per_second": hashes_per_second,
        "total_seconds": total_seconds,
        "formatted_time": time_str,
        "minutes": minutes,
        "hours": hours,
        "days": days,
        "years": years
    }
