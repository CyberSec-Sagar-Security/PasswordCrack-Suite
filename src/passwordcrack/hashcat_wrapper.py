"""
Hashcat Wrapper Module.

Provides a clean interface to hashcat for GPU/CPU-accelerated
password cracking operations.

NOTE: EDUCATIONAL USE ONLY - REQUIRES HASHCAT INSTALLATION
"""

import subprocess
import re
import threading
import queue
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any, Tuple
from enum import Enum
from .hash_utils import HashAlgorithm
from .gpx_manager import GPXManager, GPXDevice, DeviceType


class HashcatMode(Enum):
    """Hashcat hash mode mappings."""
    MD5 = "0"
    SHA1 = "100"
    SHA256 = "1400"
    SHA512 = "1700"
    BCRYPT = "3200"
    NTLM = "1000"
    
    @staticmethod
    def from_algorithm(algorithm: HashAlgorithm) -> str:
        """
        Convert HashAlgorithm to hashcat mode.
        
        Args:
            algorithm: HashAlgorithm enum
            
        Returns:
            Hashcat mode string
        """
        mapping = {
            HashAlgorithm.MD5: "0",
            HashAlgorithm.SHA1: "100",
            HashAlgorithm.SHA256: "1400",
            HashAlgorithm.SHA512: "1700",
            HashAlgorithm.BCRYPT: "3200",
            HashAlgorithm.NTLM: "1000"
        }
        return mapping.get(algorithm, "0")


class HashcatAttackMode(Enum):
    """Hashcat attack mode."""
    DICTIONARY = "0"
    COMBINATOR = "1"
    BRUTEFORCE = "3"
    HYBRID_DICT_MASK = "6"
    HYBRID_MASK_DICT = "7"


class HashcatStatus(Enum):
    """Hashcat session status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CRACKED = "cracked"
    EXHAUSTED = "exhausted"
    ABORTED = "aborted"
    ERROR = "error"


class HashcatWrapper:
    """
    Wrapper for hashcat command-line tool.
    
    Provides high-level interface for GPU/CPU-accelerated cracking.
    """
    
    def __init__(self, gpx_manager: GPXManager):
        """
        Initialize hashcat wrapper.
        
        Args:
            gpx_manager: GPX manager instance
        """
        self.gpx_manager = gpx_manager
        self.hashcat_path = self._find_hashcat()
        self.hashcat_dir = None  # Working directory for hashcat
        self.process: Optional[subprocess.Popen] = None
        self.status = HashcatStatus.IDLE
        self.output_queue: queue.Queue = queue.Queue()
        self.progress_data: Dict[str, Any] = {}
        self.result: Optional[str] = None
        
        # Don't raise error - just warn. This allows CPU mode to work.
        if not self.hashcat_path:
            print("⚠️ Warning: Hashcat not found. GPU acceleration will not be available.")
            print("   Download from: https://hashcat.net/hashcat/")
            # Don't raise - allow object creation but GPU methods will fail gracefully
        
        # Determine hashcat working directory
        if self.hashcat_path != "hashcat":
            # Absolute path - use its directory
            hashcat_file = Path(self.hashcat_path)
            if hashcat_file.exists():
                self.hashcat_dir = str(hashcat_file.parent)
        else:
            # In PATH - find actual location
            import shutil
            hashcat_full = shutil.which("hashcat")
            if hashcat_full:
                self.hashcat_dir = str(Path(hashcat_full).parent)
    
    def _find_hashcat(self) -> Optional[str]:
        """Find hashcat executable."""
        return self.gpx_manager._find_hashcat_executable()
    
    def is_available(self) -> bool:
        """Check if hashcat is available."""
        return self.hashcat_path is not None
    
    def benchmark(
        self,
        hash_mode: str,
        device: Optional[GPXDevice] = None,
        duration: int = 5
    ) -> Dict[str, Any]:
        """
        Run hashcat benchmark for specific hash mode and device.
        
        Args:
            hash_mode: Hashcat hash mode
            device: Device to benchmark (None = auto-select)
            duration: Benchmark duration in seconds
            
        Returns:
            Benchmark results dict
        """
        if not self.hashcat_path:
            return {"error": "Hashcat not available"}
        
        cmd = [self.hashcat_path, "-b", "-m", hash_mode, "--runtime", str(duration)]
        
        # Add device selection
        if device:
            if device.device_type == DeviceType.GPU:
                cmd.extend(["-d", str(device.device_id)])
            else:
                cmd.extend(["-D", "1"])  # CPU only
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration + 15,
                cwd=self.hashcat_dir  # Run from hashcat directory
            )
            
            if result.returncode != 0:
                return {"error": f"Benchmark failed: {result.stderr}"}
            
            # Parse results
            h_per_s = self.gpx_manager._parse_benchmark_result(result.stdout)
            
            return {
                "hash_mode": hash_mode,
                "device": device.name if device else "Auto",
                "speed_h_per_s": h_per_s,
                "speed_formatted": self.gpx_manager.format_hash_rate(h_per_s),
                "output": result.stdout
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def crack_dictionary(
        self,
        hash_value: str,
        hash_mode: str,
        wordlist_path: Path,
        devices: Optional[List[GPXDevice]] = None,
        rules_file: Optional[Path] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Perform dictionary attack using hashcat.
        
        Args:
            hash_value: Hash to crack
            hash_mode: Hashcat hash mode
            wordlist_path: Path to wordlist
            devices: List of devices to use
            rules_file: Optional rules file
            progress_callback: Callback for progress updates
            output_file: Optional output file for results
            
        Returns:
            Result dictionary
        """
        if not self.hashcat_path:
            return {"status": "error", "message": "Hashcat not available"}
        
        # Create temporary hash file (use absolute path)
        hash_file = Path.cwd() / ".temp_hash.txt"
        hash_file = hash_file.resolve()  # Convert to absolute path
        hash_file.write_text(hash_value)
        
        # Create output file for cracked passwords
        if not output_file:
            output_file = Path.cwd() / ".temp_output_dict.txt"
            output_file = output_file.resolve()
        if output_file.exists():
            output_file.unlink()  # Delete old results
        
        # Build command
        cmd = [
            self.hashcat_path,
            "-m", hash_mode,
            "-a", HashcatAttackMode.DICTIONARY.value,
            str(hash_file),
            str(wordlist_path.resolve()),  # Use absolute path for wordlist too
            "-o", str(output_file),  # Output file for results
            "--outfile-format", "2"  # Format: hash:password
        ]
        
        # Add device selection
        if devices:
            # Store selected devices in GPX manager
            self.gpx_manager.selected_devices = devices
            device_args = self.gpx_manager.get_hashcat_device_args()
            cmd.extend(device_args)
        
        # Add rules
        if rules_file and rules_file.exists():
            cmd.extend(["-r", str(rules_file)])
        
        # Add status output for progress tracking
        cmd.append("--status")
        cmd.extend(["--status-timer", "1"])
        
        # Disable potfile to force fresh crack
        cmd.append("--potfile-disable")
        
        # DEBUG: Print command
        print(f"\n{'='*60}")
        print(f"HASHCAT DICTIONARY COMMAND:")
        print(f"Command: {' '.join(cmd)}")
        print(f"Working Dir: {self.hashcat_dir}")
        print(f"Hash File: {hash_file} (exists: {hash_file.exists()})")
        print(f"Wordlist: {wordlist_path} (exists: {wordlist_path.exists()})")
        print(f"{'='*60}\n")
        
        try:
            # Run hashcat
            self.status = HashcatStatus.RUNNING
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None,  # No timeout for actual cracking
                cwd=self.hashcat_dir  # Run from hashcat directory
            )
            
            # DEBUG: Print result
            print(f"\n{'='*60}")
            print(f"HASHCAT DICTIONARY RESULT:")
            print(f"Return Code: {result.returncode}")
            print(f"STDOUT (COMPLETE OUTPUT):\n{result.stdout}")
            print(f"\nSTDERR:\n{result.stderr}")
            print(f"{'='*60}\n")
            
            # Parse result from output file first, then from stdout
            cracked_password = None
            if output_file.exists() and output_file.stat().st_size > 0:
                output_content = output_file.read_text().strip()
                print(f"DEBUG: Output file content: {output_content}")
                cracked_password = self._parse_cracked_password(output_content, hash_value)
            
            if not cracked_password:
                # Fallback to parsing stdout
                cracked_password = self._parse_cracked_password(result.stdout, hash_value)
            
            # Clean up
            if hash_file.exists():
                hash_file.unlink()
            if output_file.exists():
                output_file.unlink()
            
            # Check for hashcat errors (dictionary attack)
            if result.returncode not in [0, 1]:  # 0=cracked, 1=exhausted
                error_msg = f"Hashcat exited with code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout[:500]}"
                self.status = HashcatStatus.ERROR
                return {"status": "error", "message": error_msg}
            
            if cracked_password:
                self.status = HashcatStatus.CRACKED
                return {
                    "status": "cracked",
                    "password": cracked_password,
                    "hash": hash_value,
                    "output": result.stdout
                }
            else:
                self.status = HashcatStatus.EXHAUSTED
                return {
                    "status": "exhausted",
                    "message": "Wordlist exhausted without finding password",
                    "output": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            self.status = HashcatStatus.ABORTED
            if hash_file.exists():
                hash_file.unlink()
            return {"status": "timeout", "message": "Operation timed out"}
        
        except Exception as e:
            self.status = HashcatStatus.ERROR
            if hash_file.exists():
                hash_file.unlink()
            import traceback
            return {"status": "error", "message": f"{str(e)}\n{traceback.format_exc()}"}
        
        finally:
            # Cleanup
            if hash_file.exists():
                hash_file.unlink()
    
    def crack_bruteforce(
        self,
        hash_value: str,
        hash_mode: str,
        mask: str,
        devices: Optional[List[GPXDevice]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Perform brute-force/mask attack using hashcat.
        
        Args:
            hash_value: Hash to crack
            hash_mode: Hashcat hash mode
            mask: Character mask (e.g., "?l?l?l?l?d?d")
            devices: List of devices to use
            progress_callback: Callback for progress updates
            output_file: Optional output file
            
        Returns:
            Result dictionary
        """
        if not self.hashcat_path:
            return {"status": "error", "message": "Hashcat not available"}
        
        # Create temporary hash file (use absolute path)
        hash_file = Path.cwd() / ".temp_hash_brute.txt"
        hash_file = hash_file.resolve()  # Convert to absolute path
        hash_file.write_text(hash_value)
        
        # Create output file for cracked passwords
        output_file = Path.cwd() / ".temp_output_brute.txt"
        output_file = output_file.resolve()
        if output_file.exists():
            output_file.unlink()  # Delete old results
        
        # Build command
        cmd = [
            self.hashcat_path,
            "-m", hash_mode,
            "-a", HashcatAttackMode.BRUTEFORCE.value,
            str(hash_file),
            mask,
            "-o", str(output_file),  # Output file for results
            "--outfile-format", "2"  # Format: hash:password
        ]
        
        # Add device selection
        if devices:
            self.gpx_manager.selected_devices = devices
            device_args = self.gpx_manager.get_hashcat_device_args()
            cmd.extend(device_args)
        
        # Add optimization flags for maximum GPU performance
        cmd.append("-O")  # Enable optimized kernels (faster, max 32 char passwords)
        cmd.append("-w")  # Workload profile
        cmd.append("4")   # 4 = Nightmare mode (max GPU usage, may freeze UI)
        
        # Add INCREMENTAL mode - automatically tries all lengths from 1 onwards (NO MAX LIMIT)
        cmd.append("--increment")  # Enable incremental mode
        cmd.append("--increment-min")  # Start from length 1
        cmd.append("1")
        # NOTE: No --increment-max = will continue until mask length (16 chars) or password found
        
        # Add status output for real-time progress
        cmd.append("--status")
        cmd.extend(["--status-timer", "1"])  # Update every 1 second
        
        # Disable potfile to force fresh crack
        cmd.append("--potfile-disable")
        
        # DEBUG: Print command
        print(f"\n{'='*60}")
        print(f"HASHCAT BRUTE-FORCE COMMAND:")
        print(f"Command: {' '.join(cmd)}")
        print(f"Working Dir: {self.hashcat_dir}")
        print(f"Hash File: {hash_file} (exists: {hash_file.exists()})")
        print(f"Mask: {mask}")
        print(f"{'='*60}\n")
        
        try:
            # Run hashcat with real-time stdout streaming
            self.status = HashcatStatus.RUNNING
            
            # Use Popen for real-time output streaming WITHOUT text mode (binary)
            import os
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # Unbuffered
                cwd=self.hashcat_dir,
                env=os.environ.copy()
            )
            
            # Store process reference for stop functionality
            self.current_process = process
            
            # Collect output
            stdout_lines = []
            stderr_lines = []
            
            def read_stdout():
                """Read stdout in binary mode for immediate output"""
                try:
                    for line in iter(process.stdout.readline, b''):
                        if not line:
                            break
                        try:
                            line_str = line.decode('utf-8', errors='ignore').strip()
                            if line_str:
                                stdout_lines.append(line_str + '\n')
                                print(f"HASHCAT STDOUT: {line_str}")
                                import sys
                                sys.stdout.flush()
                                
                                # Call progress callback
                                if progress_callback:
                                    # Parse candidates
                                    if 'Candidates' in line_str and ':' in line_str:
                                        try:
                                            parts = line_str.split(':', 1)
                                            if len(parts) == 2:
                                                candidate_info = parts[1].strip()
                                                progress_callback({
                                                    'type': 'candidate',
                                                    'info': candidate_info
                                                })
                                        except Exception as e:
                                            print(f"DEBUG: Candidate parse error: {e}")
                                    
                                    # Parse progress
                                    if any(keyword in line_str for keyword in ['Progress', 'Speed', 'Recovered']):
                                        try:
                                            stats = self._parse_hashcat_stats('\n'.join(stdout_lines))
                                            if stats.get('progress', 0) > 0:
                                                progress_callback({
                                                    'type': 'progress',
                                                    'attempts': stats.get('progress', 0),
                                                    'total': stats.get('total', 0),
                                                    'speed': stats.get('speed', 0)
                                                })
                                        except Exception as e:
                                            print(f"DEBUG: Progress parse error: {e}")
                        except Exception as e:
                            print(f"DEBUG: Line decode error: {e}")
                    process.stdout.close()
                except Exception as e:
                    print(f"DEBUG: read_stdout error: {e}")
            
            def read_stderr():
                """Read stderr in binary mode"""
                try:
                    for line in iter(process.stderr.readline, b''):
                        if not line:
                            break
                        try:
                            line_str = line.decode('utf-8', errors='ignore').strip()
                            if line_str:
                                stderr_lines.append(line_str + '\n')
                                print(f"HASHCAT STDERR: {line_str}")
                                import sys
                                sys.stdout.flush()
                        except Exception as e:
                            print(f"DEBUG: Stderr decode error: {e}")
                    process.stderr.close()
                except Exception as e:
                    print(f"DEBUG: read_stderr error: {e}")
            
            # Start background threads to read stdout/stderr
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            print("DEBUG: Started output reader threads")
            import sys
            sys.stdout.flush()
            
            # Wait for process to complete
            returncode = process.wait()
            
            print(f"DEBUG: Process completed with return code: {returncode}")
            sys.stdout.flush()
            
            # Wait for threads to finish reading
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            
            # Clear process reference
            self.current_process = None
            
            print(f"DEBUG: Threads joined, collected {len(stdout_lines)} stdout lines")
            sys.stdout.flush()
            
            # Combine output
            result_stdout = ''.join(stdout_lines)
            result_stderr = ''.join(stderr_lines)
            
            # DEBUG: Print result
            print(f"\n{'='*60}")
            print(f"HASHCAT BRUTE-FORCE RESULT:")
            print(f"Return Code: {returncode}")
            print(f"STDOUT (COMPLETE OUTPUT):\n{result_stdout}")
            print(f"\nSTDERR:\n{result_stderr}")
            print(f"{'='*60}\n")
            
            # Parse statistics from stdout (progress, speed, etc.)
            stats = self._parse_hashcat_stats(result_stdout)
            print(f"DEBUG: Parsed stats: {stats}")
            
            # Parse result from output file first, then from stdout
            cracked_password = None
            if output_file.exists() and output_file.stat().st_size > 0:
                output_content = output_file.read_text().strip()
                print(f"DEBUG: Output file content: '{output_content}'")
                print(f"DEBUG: Output file size: {output_file.stat().st_size} bytes")
                
                # First try: If file contains ONLY the password (no hash), use it directly
                # This happens when hashcat outputs just the plaintext
                if ':' not in output_content:
                    # File contains only the password!
                    cracked_password = output_content
                    print(f"DEBUG: Password extracted directly from file: '{cracked_password}'")
                else:
                    # Try normal parsing with hash:password format
                    cracked_password = self._parse_cracked_password(output_content, hash_value)
                    if not cracked_password:
                        # Try simpler parsing - sometimes it's just "hash:password"
                        parts = output_content.split(':', 1)
                        if len(parts) == 2:
                            cracked_password = parts[1].strip()
                            print(f"DEBUG: Extracted password from simple split: '{cracked_password}'")
            else:
                print(f"DEBUG: Output file does not exist or is empty")
                print(f"DEBUG: File exists: {output_file.exists()}")
                if output_file.exists():
                    print(f"DEBUG: File size: {output_file.stat().st_size}")
            
            if not cracked_password:
                # Fallback to parsing stdout
                print(f"DEBUG: Trying to parse from stdout...")
                cracked_password = self._parse_cracked_password(result_stdout, hash_value)
            
            # Clean up
            if hash_file.exists():
                hash_file.unlink()
            if output_file.exists():
                output_file.unlink()
            
            # Interpret return codes:
            # 0 = cracked successfully
            # 1 = exhausted (all combinations tried, no match)
            # -1 or 255 = error (device issue, invalid input, etc.)
            # -2 = aborted by user
            
            if returncode == 0:
                # Success - password should be found
                if cracked_password:
                    self.status = HashcatStatus.CRACKED
                    return {
                        "status": "cracked",
                        "password": cracked_password,
                        "hash": hash_value,
                        "output": result_stdout,
                        "stats": stats
                    }
                else:
                    # Weird case: code 0 but no password
                    self.status = HashcatStatus.EXHAUSTED
                    return {
                        "status": "exhausted",
                        "message": "Hashcat returned success but no password in output",
                        "output": result_stdout,
                        "stats": stats
                    }
            
            elif returncode == 1:
                # Exhausted - tried all combinations
                self.status = HashcatStatus.EXHAUSTED
                return {
                    "status": "exhausted",
                    "message": f"Mask space exhausted ({stats['progress']}/{stats['total']} attempts)",
                    "output": result_stdout,
                    "stats": stats
                }
            
            else:
                # Error occurred
                error_msg = f"Hashcat exited with code {returncode}\n"
                
                # Add parsed errors and warnings
                if stats['errors']:
                    error_msg += "\nERRORS:\n" + "\n".join(stats['errors'])
                if stats['warnings']:
                    error_msg += "\nWARNINGS:\n" + "\n".join(stats['warnings'])
                
                # Add stderr if present
                if result_stderr.strip():
                    error_msg += f"\n\nSTDERR: {result_stderr.strip()}"
                
                # Suggest fixes for common errors
                if 'CUDA' in result_stdout and 'Failed to initialize' in result_stdout:
                    error_msg += "\n\n💡 SUGGESTED FIX:\n"
                    error_msg += "CUDA RTC library failed to initialize.\n"
                    error_msg += "1. Install CUDA Toolkit 12.x from: https://developer.nvidia.com/cuda-downloads\n"
                    error_msg += "2. Verify installation: Open CMD and run 'nvcc --version'\n"
                    error_msg += "3. Add to PATH: C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.x\\bin\n"
                    error_msg += "4. Restart application\n"
                    error_msg += "\nNOTE: Hashcat may fall back to OpenCL which still works but slower."
                
                self.status = HashcatStatus.ERROR
                return {
                    "status": "error",
                    "message": error_msg,
                    "stats": stats
                }
        
        except Exception as e:
            self.status = HashcatStatus.ERROR
            if hash_file.exists():
                hash_file.unlink()
            if output_file.exists():
                output_file.unlink()
            import traceback
            return {"status": "error", "message": f"{str(e)}\n{traceback.format_exc()}"}
        
        finally:
            # Cleanup
            if hash_file.exists():
                hash_file.unlink()
            if output_file.exists():
                output_file.unlink()
    
    def stop_attack(self) -> bool:
        """Stop the currently running hashcat process.
        
        Returns:
            True if process was stopped, False if no process running
        """
        if self.current_process and self.current_process.poll() is None:
            print("DEBUG: Stopping hashcat process...")
            import sys
            sys.stdout.flush()
            try:
                self.current_process.terminate()
                # Give it 2 seconds to terminate gracefully
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    self.current_process.kill()
                    self.current_process.wait()
                print("DEBUG: Hashcat process stopped")
                sys.stdout.flush()
                self.status = HashcatStatus.IDLE
                self.current_process = None
                return True
            except Exception as e:
                print(f"DEBUG: Error stopping process: {e}")
                sys.stdout.flush()
                return False
        return False
    
    def _parse_cracked_password(self, output: str, hash_value: str) -> Optional[str]:
        """
        Parse cracked password from hashcat output.
        
        Args:
            output: Hashcat output
            hash_value: Original hash
            
        Returns:
            Cracked password or None
        """
        print(f"\nDEBUG: Parsing password from output...")
        print(f"DEBUG: Looking for hash: {hash_value[:32]}...")
        
        lines = output.split('\n')
        
        for line in lines:
            # Look for "hash:password" format
            if hash_value.lower() in line.lower():
                print(f"DEBUG: Found matching line: {line}")
                parts = line.split(':')
                if len(parts) >= 2:
                    # Last part is the password
                    password = parts[-1].strip()
                    print(f"DEBUG: Extracted password: {password}")
                    return password
        
        print(f"DEBUG: No password found in output")
        return None
    
    def _parse_hashcat_stats(self, stdout: str) -> Dict[str, Any]:
        """
        Parse statistics from hashcat stdout (progress, speed, status, attempts).
        
        Args:
            stdout: Complete hashcat stdout
            
        Returns:
            Dictionary with parsed stats: {
                'status': 'Running'/'Exhausted'/'Cracked'/etc,
                'progress': int (attempts so far),
                'total': int (total keyspace),
                'speed': float (H/s),
                'recovered': '0/1',
                'errors': [list of error messages],
                'warnings': [list of warnings],
                'backend': 'CUDA'/'OpenCL'/'CPU',
                'device_name': str
            }
        """
        import re
        stats = {
            'status': 'Unknown',
            'progress': 0,
            'total': 0,
            'speed': 0.0,
            'recovered': '0/0',
            'errors': [],
            'warnings': [],
            'backend': 'Unknown',
            'device_name': ''
        }
        
        lines = stdout.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Status line: "Status...........: Exhausted"
            if line_stripped.startswith('Status'):
                match = re.search(r'Status\.+:\s*(.+)', line_stripped)
                if match:
                    stats['status'] = match.group(1).strip()
            
            # Progress line: "Progress.........: 10000/10000 (100.00%)"
            elif line_stripped.startswith('Progress'):
                match = re.search(r'Progress\.+:\s*(\d+)/(\d+)', line_stripped)
                if match:
                    stats['progress'] = int(match.group(1))
                    stats['total'] = int(match.group(2))
            
            # Speed line: "Speed.#01........: 10636.0 kH/s"
            elif 'Speed.#' in line_stripped:
                match = re.search(r'Speed\.#\d+\.+:\s*([\d.]+)\s*(H/s|kH/s|MH/s|GH/s)', line_stripped)
                if match:
                    speed_value = float(match.group(1))
                    speed_unit = match.group(2)
                    # Convert to H/s
                    multipliers = {'H/s': 1, 'kH/s': 1000, 'MH/s': 1000000, 'GH/s': 1000000000}
                    stats['speed'] = speed_value * multipliers.get(speed_unit, 1)
            
            # Recovered line: "Recovered........: 0/1 (0.00%) Digests"
            elif line_stripped.startswith('Recovered'):
                match = re.search(r'Recovered\.+:\s*(\d+/\d+)', line_stripped)
                if match:
                    stats['recovered'] = match.group(1)
            
            # Backend detection
            elif 'CUDA' in line and 'Platform' in line:
                stats['backend'] = 'CUDA'
            elif 'OpenCL' in line and 'Platform' in line:
                stats['backend'] = 'OpenCL'
            elif 'Falling back to OpenCL' in line:
                stats['backend'] = 'OpenCL (CUDA fallback)'
                stats['warnings'].append('CUDA RTC initialization failed, using OpenCL backend')
            
            # Device name: "* Device #01: NVIDIA RTX 2000..."
            elif line_stripped.startswith('* Device #'):
                match = re.search(r'\* Device #\d+: (.+?)(?:,|$)', line_stripped)
                if match:
                    stats['device_name'] = match.group(1).strip()
            
            # Error detection
            elif 'Failed to initialize' in line:
                stats['errors'].append(line_stripped)
            elif 'not installed or incorrectly installed' in line:
                stats['errors'].append(line_stripped)
            
            # Warnings
            elif 'wordlist or mask that you are using is too small' in line:
                stats['warnings'].append('Small mask: Hashcat cannot use full GPU parallel power')
        
        return stats
    
    def get_estimated_time(
        self,
        keyspace: int,
        speed_h_per_s: float
    ) -> Tuple[float, str]:
        """
        Estimate time to complete based on keyspace and speed.
        
        Args:
            keyspace: Total number of candidates
            speed_h_per_s: Hashing speed in H/s
            
        Returns:
            Tuple of (seconds, formatted_string)
        """
        if speed_h_per_s == 0:
            return (float('inf'), "Unknown")
        
        seconds = keyspace / speed_h_per_s
        
        # Format time
        if seconds < 60:
            return (seconds, f"{seconds:.1f} seconds")
        elif seconds < 3600:
            return (seconds, f"{seconds / 60:.1f} minutes")
        elif seconds < 86400:
            return (seconds, f"{seconds / 3600:.1f} hours")
        elif seconds < 2592000:
            return (seconds, f"{seconds / 86400:.1f} days")
        elif seconds < 31536000:
            return (seconds, f"{seconds / 2592000:.1f} months")
        else:
            return (seconds, f"{seconds / 31536000:.1f} years")
    
    def calculate_wordlist_size(self, wordlist_path: Path) -> int:
        """
        Calculate number of words in wordlist.
        
        Args:
            wordlist_path: Path to wordlist
            
        Returns:
            Number of words
        """
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def calculate_mask_keyspace(self, mask: str) -> int:
        """
        Calculate keyspace size for a mask.
        
        Args:
            mask: Hashcat mask (e.g., "?l?l?l?l?d?d")
            
        Returns:
            Keyspace size
        """
        # Hashcat mask charsets
        charsets = {
            "?l": 26,  # lowercase
            "?u": 26,  # uppercase
            "?d": 10,  # digits
            "?s": 33,  # special chars
            "?a": 95,  # all printable ASCII
            "?b": 256  # all bytes
        }
        
        keyspace = 1
        i = 0
        
        while i < len(mask):
            if mask[i] == '?' and i + 1 < len(mask):
                charset_key = mask[i:i+2]
                if charset_key in charsets:
                    keyspace *= charsets[charset_key]
                    i += 2
                    continue
            
            # Single character
            keyspace *= 1
            i += 1
        
        return keyspace
    
    def check_gpu_resistance(self, hash_mode: str) -> Tuple[bool, str]:
        """
        Check if hash algorithm is GPU-resistant.
        
        Args:
            hash_mode: Hashcat hash mode
            
        Returns:
            Tuple of (is_resistant, explanation)
        """
        # GPU-resistant algorithms (slow hashing)
        resistant_modes = {
            "3200": "bcrypt - Designed to resist GPU acceleration",
            "7500": "Kerberos 5 - Memory-hard algorithm",
            "9000": "Password Safe v2 - Slow hashing",
            "15700": "Ethereum Wallet - Memory-hard",
            "22000": "WPA-PBKDF2 - Slow hashing"
        }
        
        if hash_mode in resistant_modes:
            return (True, resistant_modes[hash_mode])
        
        return (False, "This algorithm may benefit from GPU acceleration")
    
    def get_device_fallback_message(self) -> str:
        """
        Get message for device fallback scenario.
        
        Returns:
            Fallback message
        """
        return (
            "⚠️ GPU lost or unavailable - falling back to CPU mode.\n"
            "Performance will be reduced. Check your GPU drivers and connections."
        )
    
    def verify_devices_available(self, devices: List[GPXDevice]) -> Tuple[bool, List[GPXDevice]]:
        """
        Verify that selected devices are still available.
        
        Args:
            devices: List of devices to verify
            
        Returns:
            Tuple of (all_available, available_devices)
        """
        # Re-detect devices
        self.gpx_manager.detect_devices(force_rescan=True)
        current_devices = self.gpx_manager.devices
        
        available = []
        
        for device in devices:
            # Check if device still exists
            for current in current_devices:
                if (current.device_type == device.device_type and
                    current.name == device.name):
                    available.append(current)
                    break
        
        all_available = len(available) == len(devices)
        
        return (all_available, available)
    
    def get_gpu_warning_message(self) -> str:
        """Get GPU usage warning message."""
        return (
            "⚠️ GPU Acceleration Warning\n\n"
            "GPU cracking may cause:\n"
            "• Increased system temperature\n"
            "• Higher power consumption\n"
            "• Reduced GPU lifespan if used excessively\n\n"
            "Ensure proper cooling and monitor temperatures."
        )
