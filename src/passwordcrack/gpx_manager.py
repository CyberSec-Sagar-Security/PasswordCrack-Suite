"""
GPX (GPU/CPU Acceleration) Manager.

Handles device detection, benchmarking, and intelligent device selection
for password cracking operations. Supports OpenCL/CUDA devices with
automatic fallback to CPU.

NOTE: EDUCATIONAL USE ONLY
"""

import json
import subprocess
import platform
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum


class DeviceTier(Enum):
    """Device performance tier classification."""
    LOW = "low"
    MID = "mid"
    HIGH = "high"
    UNKNOWN = "unknown"


class DeviceType(Enum):
    """Device type classification."""
    GPU = "gpu"
    CPU = "cpu"
    UNKNOWN = "unknown"


class GPXDevice:
    """Represents a compute device (GPU or CPU)."""
    
    def __init__(
        self,
        device_id: int,
        device_type: DeviceType,
        name: str,
        vendor: str = "Unknown",
        memory_mb: int = 0,
        compute_capability: Optional[str] = None,
        driver_version: Optional[str] = None,
        tier: DeviceTier = DeviceTier.UNKNOWN
    ):
        """
        Initialize device.
        
        Args:
            device_id: Device ID (as reported by backend)
            device_type: GPU or CPU
            name: Device name/model
            vendor: Vendor (NVIDIA, AMD, Intel, etc.)
            memory_mb: Dedicated memory in MB
            compute_capability: CUDA compute capability or OpenCL version
            driver_version: Driver version
            tier: Performance tier
        """
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.vendor = vendor
        self.memory_mb = memory_mb
        self.compute_capability = compute_capability
        self.driver_version = driver_version
        self.tier = tier
        self.benchmark_results: Dict[str, float] = {}  # hash_mode -> H/s
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "name": self.name,
            "vendor": self.vendor,
            "memory_mb": self.memory_mb,
            "compute_capability": self.compute_capability,
            "driver_version": self.driver_version,
            "tier": self.tier.value,
            "benchmark_results": self.benchmark_results
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GPXDevice':
        """Create device from dictionary."""
        device = GPXDevice(
            device_id=data["device_id"],
            device_type=DeviceType(data["device_type"]),
            name=data["name"],
            vendor=data.get("vendor", "Unknown"),
            memory_mb=data.get("memory_mb", 0),
            compute_capability=data.get("compute_capability"),
            driver_version=data.get("driver_version"),
            tier=DeviceTier(data.get("tier", "unknown"))
        )
        device.benchmark_results = data.get("benchmark_results", {})
        return device
    
    def __repr__(self) -> str:
        """String representation."""
        memory_str = f"{self.memory_mb / 1024:.1f} GB" if self.memory_mb > 0 else "N/A"
        return f"{self.vendor} {self.name} ({memory_str}) - {self.tier.value.upper()}"


class GPXManager:
    """
    Manages GPU/CPU device detection, selection, and benchmarking.
    
    Provides automatic device detection with intelligent fallback,
    performance benchmarking, and device tier classification.
    """
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize GPX Manager.
        
        Args:
            cache_file: Path to device cache file (default: .gpx_cache.json)
        """
        if cache_file is None:
            self.cache_file = Path.cwd() / ".gpx_cache.json"
        else:
            self.cache_file = Path(cache_file)
        
        self.devices: List[GPXDevice] = []
        self.cpu_device: Optional[GPXDevice] = None
        self.selected_devices: List[GPXDevice] = []
        self.gpx_enabled = False
        self.allow_mixed_mode = True  # Allow CPU + GPU
        
        # Load cached device info
        self._load_cache()
    
    def detect_devices(self, force_rescan: bool = False) -> List[GPXDevice]:
        """
        Detect available compute devices.
        
        Args:
            force_rescan: Force device re-detection even if cached
            
        Returns:
            List of detected devices
        """
        if not force_rescan and self.devices:
            return self.devices
        
        self.devices = []
        
        # Detect CPU
        self.cpu_device = self._detect_cpu()
        self.devices.append(self.cpu_device)
        
        # Detect GPUs via hashcat
        gpu_devices = self._detect_gpus_hashcat()
        self.devices.extend(gpu_devices)
        
        # Save to cache
        self._save_cache()
        
        return self.devices
    
    def _detect_cpu(self) -> GPXDevice:
        """Detect CPU device with detailed information."""
        import multiprocessing
        
        cpu_name = "Unknown CPU"
        cpu_cores = multiprocessing.cpu_count()
        cpu_freq = 0.0
        
        # Try to get detailed CPU info based on platform
        if platform.system() == "Windows":
            try:
                # Get CPU name
                result = subprocess.run(
                    ["wmic", "cpu", "get", "Name,MaxClockSpeed,NumberOfCores,NumberOfLogicalProcessors", "/format:csv"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 2:
                        parts = [p.strip() for p in lines[2].split(',')]
                        if len(parts) >= 4:
                            cpu_freq = float(parts[1]) if parts[1].isdigit() else 0.0
                            cpu_name = parts[2]
                            # parts[3] = cores, parts[4] = logical processors
                
                # Also try PowerShell for more info
                if cpu_name == "Unknown CPU":
                    ps_result = subprocess.run(
                        ["powershell", "-Command", 
                         "Get-WmiObject -Class Win32_Processor | Select-Object Name,MaxClockSpeed | ConvertTo-Json"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if ps_result.returncode == 0:
                        import json
                        try:
                            cpu_data = json.loads(ps_result.stdout)
                            if isinstance(cpu_data, list):
                                cpu_data = cpu_data[0]
                            cpu_name = cpu_data.get("Name", cpu_name)
                            cpu_freq = float(cpu_data.get("MaxClockSpeed", 0))
                        except:
                            pass
            
            except Exception as e:
                print(f"Windows CPU detection error: {e}")
        
        elif platform.system() == "Linux":
            try:
                # Read /proc/cpuinfo
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_name = line.split(":")[1].strip()
                            break
                        elif "cpu MHz" in line:
                            cpu_freq = float(line.split(":")[1].strip())
                
                # Try lscpu for more info
                result = subprocess.run(
                    ["lscpu"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "Model name:" in line:
                            cpu_name = line.split(":")[1].strip()
                        elif "CPU MHz:" in line:
                            cpu_freq = float(line.split(":")[1].strip())
            
            except Exception as e:
                print(f"Linux CPU detection error: {e}")
        
        elif platform.system() == "Darwin":  # macOS
            try:
                # Get CPU brand
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    cpu_name = result.stdout.strip()
                
                # Get CPU frequency
                freq_result = subprocess.run(
                    ["sysctl", "-n", "hw.cpufrequency"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if freq_result.returncode == 0:
                    cpu_freq = float(freq_result.stdout.strip()) / 1_000_000  # Convert to MHz
            
            except Exception as e:
                print(f"macOS CPU detection error: {e}")
        
        # Fallback to platform.processor()
        if cpu_name == "Unknown CPU":
            cpu_name = platform.processor() or "Unknown CPU"
        
        # Determine vendor
        vendor = "Unknown"
        if "Intel" in cpu_name:
            vendor = "Intel"
        elif "AMD" in cpu_name:
            vendor = "AMD"
        elif "ARM" in cpu_name or "Apple" in cpu_name:
            vendor = "ARM/Apple"
        
        # Classify tier based on cores and frequency
        if cpu_cores >= 16:
            tier = DeviceTier.HIGH
        elif cpu_cores >= 8:
            tier = DeviceTier.MID
        elif cpu_cores >= 4:
            tier = DeviceTier.LOW
        else:
            tier = DeviceTier.LOW
        
        # Boost tier if high frequency
        if cpu_freq >= 4000:  # 4+ GHz
            if tier == DeviceTier.MID:
                tier = DeviceTier.HIGH
            elif tier == DeviceTier.LOW:
                tier = DeviceTier.MID
        
        return GPXDevice(
            device_id=0,
            device_type=DeviceType.CPU,
            name=cpu_name,
            vendor=vendor,
            memory_mb=0,  # Not applicable for CPU
            compute_capability=f"{cpu_cores} cores @ {cpu_freq/1000:.2f} GHz" if cpu_freq > 0 else f"{cpu_cores} cores",
            tier=tier
        )
    
    def _detect_gpus_hashcat(self) -> List[GPXDevice]:
        """
        Detect GPU devices using multiple methods.
        
        Returns:
            List of GPU devices
        """
        gpus = []
        
        # Method 1: Try hashcat (if available)
        try:
            hashcat_cmd = self._find_hashcat_executable()
            if hashcat_cmd:
                result = subprocess.run(
                    [hashcat_cmd, "-I"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    gpus = self._parse_hashcat_device_list(result.stdout)
                    if gpus:
                        return gpus
        except Exception as e:
            print(f"Hashcat detection failed: {e}")
        
        # Method 2: Try Windows WMIC (Windows only)
        if platform.system() == "Windows":
            try:
                gpus = self._detect_gpus_windows()
                if gpus:
                    return gpus
            except Exception as e:
                print(f"Windows GPU detection failed: {e}")
        
        # Method 3: Try lspci (Linux only)
        if platform.system() == "Linux":
            try:
                gpus = self._detect_gpus_linux()
                if gpus:
                    return gpus
            except Exception as e:
                print(f"Linux GPU detection failed: {e}")
        
        # Method 4: Try Python packages (GPUtil, py3nvml for NVIDIA)
        try:
            gpus_python = self._detect_gpus_python()
            if gpus_python:
                return gpus_python
        except Exception as e:
            print(f"Python package GPU detection failed: {e}")
        
        # Method 5: Try system_profiler (macOS only)
        if platform.system() == "Darwin":
            try:
                gpus = self._detect_gpus_macos()
                if gpus:
                    return gpus
            except Exception as e:
                print(f"macOS GPU detection failed: {e}")
        
        return gpus
    
    def _detect_gpus_python(self) -> List[GPXDevice]:
        """
        Detect GPUs using Python packages (GPUtil, py3nvml).
        
        Returns:
            List of GPU devices
        """
        gpus = []
        device_id = 1
        
        # Try GPUtil (cross-platform)
        try:
            import GPUtil
            gpu_list = GPUtil.getGPUs()
            
            for gpu in gpu_list:
                vendor = "NVIDIA"  # GPUtil primarily works with NVIDIA
                if hasattr(gpu, 'name'):
                    name = gpu.name
                else:
                    name = f"GPU {gpu.id}"
                
                memory_mb = int(gpu.memoryTotal) if hasattr(gpu, 'memoryTotal') else 0
                driver = gpu.driver if hasattr(gpu, 'driver') else "Unknown"
                
                tier = self._classify_gpu_tier(name, memory_mb)
                
                device = GPXDevice(
                    device_id=device_id,
                    device_type=DeviceType.GPU,
                    name=name,
                    vendor=vendor,
                    memory_mb=memory_mb,
                    driver_version=driver,
                    compute_capability="CUDA",
                    tier=tier
                )
                
                gpus.append(device)
                device_id += 1
        
        except ImportError:
            pass  # GPUtil not installed
        except Exception as e:
            print(f"GPUtil detection error: {e}")
        
        # Try py3nvml for NVIDIA
        if not gpus:
            try:
                import pynvml
                pynvml.nvmlInit()
                
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')
                    
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_mb = int(memory_info.total / (1024 * 1024))
                    
                    driver_version = pynvml.nvmlSystemGetDriverVersion()
                    if isinstance(driver_version, bytes):
                        driver_version = driver_version.decode('utf-8')
                    
                    tier = self._classify_gpu_tier(name, memory_mb)
                    
                    device = GPXDevice(
                        device_id=device_id,
                        device_type=DeviceType.GPU,
                        name=name,
                        vendor="NVIDIA",
                        memory_mb=memory_mb,
                        driver_version=driver_version,
                        compute_capability="CUDA",
                        tier=tier
                    )
                    
                    gpus.append(device)
                    device_id += 1
                
                pynvml.nvmlShutdown()
            
            except ImportError:
                pass  # pynvml not installed
            except Exception as e:
                print(f"pynvml detection error: {e}")
        
        return gpus
    
    def _detect_gpus_windows(self) -> List[GPXDevice]:
        """
        Detect GPU devices on Windows using WMIC.
        
        Returns:
            List of GPU devices
        """
        gpus = []
        device_id = 1
        
        try:
            # Get GPU info using WMIC
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", 
                 "Name,AdapterRAM,DriverVersion,VideoProcessor", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return gpus
            
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Skip header and empty line
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 4:
                    continue
                
                # Parse fields: Node,AdapterRAM,DriverVersion,Name,VideoProcessor
                try:
                    adapter_ram = int(parts[1]) if parts[1] and parts[1].isdigit() else 0
                    driver_version = parts[2]
                    name = parts[3]
                    video_processor = parts[4] if len(parts) > 4 else ""
                    
                    # Skip virtual/software adapters
                    if any(skip in name.upper() for skip in ["MICROSOFT", "REMOTE", "VIRTUAL", "BASIC"]):
                        continue
                    
                    # Determine vendor
                    vendor = "Unknown"
                    if "NVIDIA" in name.upper():
                        vendor = "NVIDIA"
                    elif "AMD" in name.upper() or "RADEON" in name.upper():
                        vendor = "AMD"
                    elif "INTEL" in name.upper():
                        vendor = "Intel"
                    
                    # Convert RAM to MB
                    memory_mb = adapter_ram // (1024 * 1024) if adapter_ram > 0 else 0
                    
                    # Classify tier
                    tier = self._classify_gpu_tier(name, memory_mb)
                    
                    device = GPXDevice(
                        device_id=device_id,
                        device_type=DeviceType.GPU,
                        name=name,
                        vendor=vendor,
                        memory_mb=memory_mb,
                        driver_version=driver_version,
                        compute_capability="DirectX/OpenCL",
                        tier=tier
                    )
                    
                    gpus.append(device)
                    device_id += 1
                
                except (ValueError, IndexError) as e:
                    continue
        
        except Exception as e:
            print(f"Windows WMIC detection error: {e}")
        
        return gpus
    
    def _detect_gpus_linux(self) -> List[GPXDevice]:
        """
        Detect GPU devices on Linux using lspci.
        
        Returns:
            List of GPU devices
        """
        gpus = []
        device_id = 1
        
        try:
            # Use lspci to list GPUs
            result = subprocess.run(
                ["lspci", "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return gpus
            
            # Parse lspci output for VGA/3D controllers
            lines = result.stdout.split('\n')
            current_gpu = None
            
            for line in lines:
                if "VGA compatible controller" in line or "3D controller" in line:
                    # Extract GPU name
                    parts = line.split(': ')
                    if len(parts) > 1:
                        name = parts[1].strip()
                        
                        # Determine vendor
                        vendor = "Unknown"
                        if "" in name.upper():
                            vendor = "NVIDIA"
                        elif "AMD" in name.upper() or "ATI" in name.upper():
                            vendor = "AMD"
                        elif "INTEL" in name.upper():
                            vendor = "Intel"
                        
                        current_gpu = {
                            "name": name,
                            "vendor": vendor,
                            "memory_mb": 0
                        }
                
                elif current_gpu and "Memory at" in line:
                    # Try to extract memory size
                    # This is approximate from address range
                    pass
            
            if current_gpu:
                tier = self._classify_gpu_tier(current_gpu["name"], current_gpu["memory_mb"])
                
                device = GPXDevice(
                    device_id=device_id,
                    device_type=DeviceType.GPU,
                    name=current_gpu["name"],
                    vendor=current_gpu["vendor"],
                    memory_mb=current_gpu["memory_mb"],
                    compute_capability="OpenCL/CUDA",
                    tier=tier
                )
                
                gpus.append(device)
        
        except Exception as e:
            print(f"Linux lspci detection error: {e}")
        
        return gpus
    
    def _detect_gpus_macos(self) -> List[GPXDevice]:
        """
        Detect GPU devices on macOS using system_profiler.
        
        Returns:
            List of GPU devices
        """
        gpus = []
        device_id = 1
        
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return gpus
            
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if "Chipset Model:" in line:
                    name = line.split(':')[1].strip()
                    
                    # Determine vendor
                    vendor = "Unknown"
                    if "NVIDIA" in name.upper():
                        vendor = "NVIDIA"
                    elif "AMD" in name.upper() or "RADEON" in name.upper():
                        vendor = "AMD"
                    elif "INTEL" in name.upper() or "APPLE" in name.upper():
                        vendor = "Apple/Intel"
                    
                    # Try to find VRAM
                    memory_mb = 0
                    for j in range(i, min(i + 10, len(lines))):
                        if "VRAM" in lines[j]:
                            mem_str = lines[j].split(':')[1].strip()
                            # Parse memory (e.g., "8 GB")
                            mem_match = re.search(r'(\d+)\s*(MB|GB)', mem_str)
                            if mem_match:
                                value = int(mem_match.group(1))
                                unit = mem_match.group(2)
                                memory_mb = value * 1024 if unit == "GB" else value
                            break
                    
                    tier = self._classify_gpu_tier(name, memory_mb)
                    
                    device = GPXDevice(
                        device_id=device_id,
                        device_type=DeviceType.GPU,
                        name=name,
                        vendor=vendor,
                        memory_mb=memory_mb,
                        compute_capability="Metal/OpenCL",
                        tier=tier
                    )
                    
                    gpus.append(device)
                    device_id += 1
        
        except Exception as e:
            print(f"macOS system_profiler detection error: {e}")
        
        return gpus
    
    def _find_hashcat_executable(self) -> Optional[str]:
        """
        Find hashcat executable in PATH or common locations.
        
        Returns:
            Path to hashcat executable or None
        """
        # Try hashcat in PATH
        try:
            result = subprocess.run(
                ["hashcat", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "hashcat"
        except Exception:
            pass
        
        # Try common installation paths
        if platform.system() == "Windows":
            common_paths = [
                "C:\\hashcat-7.1.2\\hashcat.exe",
                "C:\\hashcat\\hashcat.exe",
                "C:\\Program Files\\hashcat\\hashcat.exe",
                "C:\\Tools\\hashcat\\hashcat.exe"
            ]
        else:
            common_paths = [
                "/usr/bin/hashcat",
                "/usr/local/bin/hashcat",
                "/opt/hashcat/hashcat"
            ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def _parse_hashcat_device_list(self, output: str) -> List[GPXDevice]:
        """
        Parse hashcat -I output to extract device information.
        
        Args:
            output: hashcat -I output
            
        Returns:
            List of GPU devices
        """
        devices = []
        current_backend = None
        device_id = 1  # Start from 1, 0 is CPU
        
        lines = output.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect backend (OpenCL, CUDA, etc.)
            if "Backend" in line or "Platform" in line:
                if "CUDA" in line:
                    current_backend = "CUDA"
                elif "OpenCL" in line:
                    current_backend = "OpenCL"
            
            # Detect device entry
            if line.startswith("Device ID #") or line.startswith("Backend Device ID"):
                device_info = self._parse_hashcat_device_block(lines[i:i+20])
                if device_info:
                    device_info["device_id"] = device_id
                    device_info["compute_capability"] = current_backend
                    
                    # Classify tier
                    tier = self._classify_gpu_tier(device_info["name"], device_info["memory_mb"])
                    
                    device = GPXDevice(
                        device_id=device_id,
                        device_type=DeviceType.GPU,
                        name=device_info["name"],
                        vendor=device_info["vendor"],
                        memory_mb=device_info["memory_mb"],
                        compute_capability=device_info["compute_capability"],
                        tier=tier
                    )
                    devices.append(device)
                    device_id += 1
            
            i += 1
        
        return devices
    
    def _parse_hashcat_device_block(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single device block from hashcat output.
        
        Args:
            lines: Lines containing device info
            
        Returns:
            Device info dict or None
        """
        info = {
            "name": "Unknown GPU",
            "vendor": "Unknown",
            "memory_mb": 0
        }
        
        for line in lines:
            line = line.strip()
            
            if not line:
                break
            
            # Extract device name
            if "Name:" in line or "Device Name:" in line:
                info["name"] = line.split(":", 1)[1].strip()
            
            # Extract vendor
            if "Vendor:" in line:
                vendor = line.split(":", 1)[1].strip()
                if "NVIDIA" in vendor.upper():
                    info["vendor"] = "NVIDIA"
                elif "AMD" in vendor.upper() or "ATI" in vendor.upper():
                    info["vendor"] = "AMD"
                elif "INTEL" in vendor.upper():
                    info["vendor"] = "Intel"
                else:
                    info["vendor"] = vendor
            
            # Extract memory
            if "Global Memory:" in line or "Device Memory:" in line:
                memory_str = line.split(":", 1)[1].strip()
                # Parse memory (e.g., "8192 MB" or "8 GB")
                memory_match = re.search(r'(\d+)\s*(MB|GB)', memory_str, re.IGNORECASE)
                if memory_match:
                    value = int(memory_match.group(1))
                    unit = memory_match.group(2).upper()
                    if unit == "GB":
                        value *= 1024
                    info["memory_mb"] = value
        
        return info if info["name"] != "Unknown GPU" else None
    
    def _classify_gpu_tier(self, gpu_name: str, memory_mb: int) -> DeviceTier:
        """
        Classify GPU into performance tier.
        
        Args:
            gpu_name: GPU model name
            memory_mb: GPU memory in MB
            
        Returns:
            Device tier
        """
        gpu_upper = gpu_name.upper()
        
        # High-tier GPUs
        high_tier_keywords = [
            "RTX 4090", "RTX 4080", "RTX 3090", "RTX 3080",
            "A100", "H100", "V100", "A6000", "A5000",
            "TITAN", "RX 7900", "RX 6900"
        ]
        
        for keyword in high_tier_keywords:
            if keyword.upper() in gpu_upper:
                return DeviceTier.HIGH
        
        # Mid-tier GPUs
        mid_tier_keywords = [
            "RTX 4070", "RTX 4060", "RTX 3070", "RTX 3060",
            "RTX 2080", "RTX 2070", "RTX 2060",
            "GTX 1080", "GTX 1070",
            "RX 7800", "RX 7700", "RX 6800", "RX 6700",
            "A4000", "A2000"
        ]
        
        for keyword in mid_tier_keywords:
            if keyword.upper() in gpu_upper:
                return DeviceTier.MID
        
        # Memory-based fallback
        if memory_mb >= 8192:
            return DeviceTier.MID
        elif memory_mb >= 4096:
            return DeviceTier.LOW
        
        return DeviceTier.LOW
    
    def get_gpu_devices(self) -> List[GPXDevice]:
        """Get list of GPU devices only."""
        return [d for d in self.devices if d.device_type == DeviceType.GPU]
    
    def get_cpu_device(self) -> Optional[GPXDevice]:
        """Get CPU device."""
        return self.cpu_device
    
    def get_best_device(self) -> GPXDevice:
        """
        Get the best available device.
        
        Returns:
            Best device (highest tier GPU or CPU if no GPU)
        """
        gpus = self.get_gpu_devices()
        
        if gpus:
            # Sort by tier (HIGH > MID > LOW) and memory
            sorted_gpus = sorted(
                gpus,
                key=lambda d: (
                    ["unknown", "low", "mid", "high"].index(d.tier.value),
                    d.memory_mb
                ),
                reverse=True
            )
            return sorted_gpus[0]
        
        return self.cpu_device or self.devices[0]
    
    def auto_select_devices(self, prefer_gpu: bool = True) -> List[GPXDevice]:
        """
        Automatically select devices for cracking.
        
        Args:
            prefer_gpu: Prefer GPU if available
            
        Returns:
            List of selected devices
        """
        self.selected_devices = []
        
        if prefer_gpu and self.get_gpu_devices():
            # Use best GPU
            best_gpu = self.get_best_device()
            self.selected_devices.append(best_gpu)
            
            # Add CPU if mixed mode enabled
            if self.allow_mixed_mode and self.cpu_device:
                self.selected_devices.append(self.cpu_device)
        else:
            # CPU only
            if self.cpu_device:
                self.selected_devices.append(self.cpu_device)
        
        return self.selected_devices
    
    def benchmark_device(
        self,
        device: GPXDevice,
        hash_mode: str = "0",  # MD5 by default
        duration_seconds: int = 5
    ) -> float:
        """
        Benchmark a specific device.
        
        Args:
            device: Device to benchmark
            hash_mode: Hash mode to test (hashcat mode number)
            duration_seconds: Benchmark duration
            
        Returns:
            Hashes per second (H/s)
        """
        try:
            hashcat_cmd = self._find_hashcat_executable()
            if not hashcat_cmd:
                print("DEBUG: Hashcat executable not found for benchmark")
                return 0.0
            
            # Build hashcat benchmark command
            cmd = [hashcat_cmd, "-b", "-m", hash_mode]
            
            # Select device
            if device.device_type == DeviceType.GPU:
                cmd.extend(["-d", str(device.device_id)])
            else:
                cmd.extend(["-D", "1"])  # CPU only
            
            print(f"DEBUG: Running benchmark command: {' '.join(cmd)}")
            
            # Run benchmark
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration_seconds + 10,
                cwd=Path(hashcat_cmd).parent  # Run from hashcat directory
            )
            
            print(f"DEBUG: Benchmark return code: {result.returncode}")
            if result.stdout:
                print(f"DEBUG: Benchmark stdout:\n{result.stdout}")
            if result.stderr:
                print(f"DEBUG: Benchmark stderr:\n{result.stderr}")
            
            if result.returncode != 0:
                print(f"DEBUG: Benchmark failed with code {result.returncode}")
                return 0.0
            
            # Parse benchmark result
            h_per_s = self._parse_benchmark_result(result.stdout)
            print(f"DEBUG: Parsed benchmark speed: {h_per_s} H/s")
            
            # Cache result
            device.benchmark_results[hash_mode] = h_per_s
            self._save_cache()
            
            return h_per_s
            
        except subprocess.TimeoutExpired:
            print(f"DEBUG: Benchmark timeout after {duration_seconds + 10}s")
            return 0.0
        except Exception as e:
            print(f"DEBUG: Benchmark failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return 0.0
    
    def _parse_benchmark_result(self, output: str) -> float:
        """
        Parse hashcat benchmark output to extract H/s.
        
        Args:
            output: Benchmark output
            
        Returns:
            Hashes per second
        """
        # Look for speed line (e.g., "Speed.#1.........:  1234.5 MH/s")
        lines = output.split('\n')
        
        for line in lines:
            if "Speed" in line and "H/s" in line:
                # Extract number and unit
                match = re.search(r':\s*([\d.]+)\s*([kMGT]?H/s)', line)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    
                    # Convert to H/s
                    multipliers = {
                        "H/s": 1,
                        "kH/s": 1_000,
                        "MH/s": 1_000_000,
                        "GH/s": 1_000_000_000,
                        "TH/s": 1_000_000_000_000
                    }
                    
                    return value * multipliers.get(unit, 1)
        
        return 0.0
    
    def get_speedup_estimate(
        self,
        gpu_device: GPXDevice,
        hash_mode: str = "0"
    ) -> Tuple[float, str]:
        """
        Estimate speedup of GPU vs CPU.
        
        Args:
            gpu_device: GPU to compare
            hash_mode: Hash mode
            
        Returns:
            Tuple of (speedup_factor, description)
        """
        if not self.cpu_device:
            return (1.0, "No CPU detected")
        
        # Get or benchmark both devices
        gpu_speed = gpu_device.benchmark_results.get(hash_mode, 0.0)
        if gpu_speed == 0.0:
            gpu_speed = self.benchmark_device(gpu_device, hash_mode)
        
        cpu_speed = self.cpu_device.benchmark_results.get(hash_mode, 0.0)
        if cpu_speed == 0.0:
            cpu_speed = self.benchmark_device(self.cpu_device, hash_mode)
        
        if cpu_speed == 0.0:
            return (1.0, "CPU benchmark failed")
        
        speedup = gpu_speed / cpu_speed
        
        # Format description
        if speedup >= 10:
            desc = f"~{speedup:.0f}× faster than CPU"
        elif speedup >= 2:
            desc = f"~{speedup:.1f}× faster than CPU"
        elif speedup >= 1.2:
            desc = f"~{speedup:.1f}× faster than CPU"
        else:
            desc = "Similar to CPU (GPU-resistant algorithm)"
        
        return (speedup, desc)
    
    def format_hash_rate(self, h_per_s: float) -> str:
        """
        Format hash rate in human-readable form.
        
        Args:
            h_per_s: Hashes per second
            
        Returns:
            Formatted string
        """
        if h_per_s >= 1_000_000_000_000:
            return f"{h_per_s / 1_000_000_000_000:.2f} TH/s"
        elif h_per_s >= 1_000_000_000:
            return f"{h_per_s / 1_000_000_000:.2f} GH/s"
        elif h_per_s >= 1_000_000:
            return f"{h_per_s / 1_000_000:.2f} MH/s"
        elif h_per_s >= 1_000:
            return f"{h_per_s / 1_000:.2f} kH/s"
        else:
            return f"{h_per_s:.0f} H/s"
    
    def _load_cache(self) -> None:
        """Load cached device information."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            self.devices = [GPXDevice.from_dict(d) for d in data.get("devices", [])]
            
            # Find CPU device
            for device in self.devices:
                if device.device_type == DeviceType.CPU:
                    self.cpu_device = device
                    break
            
        except Exception as e:
            print(f"Failed to load device cache: {e}")
    
    def _save_cache(self) -> None:
        """Save device information to cache."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "devices": [d.to_dict() for d in self.devices]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save device cache: {e}")
    
    def reset_cache(self) -> None:
        """Reset device cache and force re-detection."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        
        self.devices = []
        self.cpu_device = None
        self.selected_devices = []
    
    def get_device_summary(self) -> str:
        """
        Get human-readable device summary.
        
        Returns:
            Summary string
        """
        gpus = self.get_gpu_devices()
        
        if gpus:
            best_gpu = self.get_best_device()
            memory_str = f"{best_gpu.memory_mb / 1024:.0f} GB" if best_gpu.memory_mb > 0 else "N/A"
            
            summary = f"Detected: {best_gpu.vendor} {best_gpu.name} — {memory_str} (GPU)"
            
            if len(gpus) > 1:
                summary += f" + {len(gpus) - 1} more GPU(s)"
            
            return summary
        else:
            return "No GPU detected — using CPU"
    
    def get_detailed_device_info(self) -> str:
        """
        Get detailed device information for diagnostics.
        
        Returns:
            Detailed device info
        """
        info = []
        info.append("="* 60)
        info.append("GPX DEVICE DETECTION DIAGNOSTICS")
        info.append("=" * 60)
        info.append(f"Platform: {platform.system()} {platform.release()}")
        info.append(f"Python: {platform.python_version()}")
        info.append("")
        
        # CPU Info
        if self.cpu_device:
            info.append("CPU DEVICE:")
            info.append(f"  Name: {self.cpu_device.name}")
            info.append(f"  Vendor: {self.cpu_device.vendor}")
            info.append(f"  Capability: {self.cpu_device.compute_capability}")
            info.append(f"  Tier: {self.cpu_device.tier.value.upper()}")
        else:
            info.append("CPU: Not detected")
        
        info.append("")
        
        # GPU Info
        gpus = self.get_gpu_devices()
        if gpus:
            info.append(f"GPU DEVICES ({len(gpus)} found):")
            for i, gpu in enumerate(gpus, 1):
                info.append(f"  GPU {i}:")
                info.append(f"    Name: {gpu.name}")
                info.append(f"    Vendor: {gpu.vendor}")
                info.append(f"    Memory: {gpu.memory_mb / 1024:.1f} GB ({gpu.memory_mb} MB)")
                info.append(f"    Driver: {gpu.driver_version or 'Unknown'}")
                info.append(f"    Capability: {gpu.compute_capability or 'Unknown'}")
                info.append(f"    Tier: {gpu.tier.value.upper()}")
                info.append("")
        else:
            info.append("GPU DEVICES: None detected")
            info.append("")
            info.append("Troubleshooting:")
            info.append("  1. Check if GPU drivers are installed")
            info.append("  2. Verify GPU is enabled in BIOS/UEFI")
            info.append("  3. Run 'nvidia-smi' (NVIDIA) or 'lspci | grep VGA' (Linux)")
            info.append("  4. Install hashcat and run 'hashcat -I'")
            info.append("  5. Install Python packages: pip install gputil pynvml")
            info.append("")
        
        # Hashcat availability
        hashcat_path = self._find_hashcat_executable()
        info.append(f"Hashcat: {'Found at ' + hashcat_path if hashcat_path else 'Not found'}")
        
        # Python package availability
        info.append("")
        info.append("Python GPU Packages:")
        try:
            import GPUtil
            info.append("  ✓ GPUtil: Installed")
        except ImportError:
            info.append("  ✗ GPUtil: Not installed (pip install gputil)")
        
        try:
            import pynvml
            info.append("  ✓ pynvml: Installed")
        except ImportError:
            info.append("  ✗ pynvml: Not installed (pip install pynvml)")
        
        try:
            import psutil
            info.append("  ✓ psutil: Installed")
        except ImportError:
            info.append("  ✗ psutil: Not installed (pip install psutil)")
        
        info.append("=" * 60)
        
        return "\n".join(info)
    
    def is_gpu_available(self) -> bool:
        """Check if any GPU is available."""
        return len(self.get_gpu_devices()) > 0
    
    def get_hashcat_device_args(self) -> List[str]:
        """
        Get hashcat command-line arguments for device selection.
        
        Returns:
            List of arguments
        """
        args = []
        
        if not self.selected_devices:
            return args
        
        # Check if we have both GPU and CPU selected
        has_gpu = any(d.device_type == DeviceType.GPU for d in self.selected_devices)
        has_cpu = any(d.device_type == DeviceType.CPU for d in self.selected_devices)
        
        if has_gpu and has_cpu:
            # Mixed mode - select all devices
            gpu_ids = [str(d.device_id) for d in self.selected_devices if d.device_type == DeviceType.GPU]
            args.extend(["-d", ",".join(gpu_ids)])
            args.extend(["-D", "1,2"])  # OpenCL + CUDA
        elif has_gpu:
            # GPU only
            gpu_ids = [str(d.device_id) for d in self.selected_devices]
            args.extend(["-d", ",".join(gpu_ids)])
        else:
            # CPU only
            args.extend(["-D", "1"])  # CPU device type
        
        return args
