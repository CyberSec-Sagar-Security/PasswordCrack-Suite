# GPU Environment Diagnostics for Hashcat CUDA/OpenCL Support
# Run this script to check if your system is properly configured for GPU-accelerated password cracking

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GPU ENVIRONMENT DIAGNOSTICS FOR HASHCAT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$checks = @()

# Check 1: NVIDIA Driver
Write-Host "[1/8] Checking NVIDIA GPU Driver..." -ForegroundColor Yellow
try {
    $nvidiaSmi = & nvidia-smi --query-gpu=name,driver_version,cuda_version --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PASS: nvidia-smi found" -ForegroundColor Green
        Write-Host "  GPU Info: $nvidiaSmi" -ForegroundColor Gray
        $checks += @{Name="NVIDIA Driver"; Status="PASS"; Details=$nvidiaSmi}
    } else {
        Write-Host "  ❌ FAIL: nvidia-smi not found or failed" -ForegroundColor Red
        $checks += @{Name="NVIDIA Driver"; Status="FAIL"; Details="nvidia-smi command failed"}
    }
} catch {
    Write-Host "  ❌ FAIL: nvidia-smi not in PATH" -ForegroundColor Red
    Write-Host "  Install NVIDIA drivers from: https://www.nvidia.com/Download/index.aspx" -ForegroundColor Yellow
    $checks += @{Name="NVIDIA Driver"; Status="FAIL"; Details="nvidia-smi not found"}
}

# Check 2: CUDA Toolkit (nvcc)
Write-Host "`n[2/8] Checking CUDA Toolkit (nvcc)..." -ForegroundColor Yellow
try {
    $nvccVersion = & nvcc --version 2>&1 | Select-String "release"
    if ($nvccVersion) {
        Write-Host "  ✅ PASS: CUDA Toolkit installed" -ForegroundColor Green
        Write-Host "  $nvccVersion" -ForegroundColor Gray
        $checks += @{Name="CUDA Toolkit"; Status="PASS"; Details=$nvccVersion}
    } else {
        Write-Host "  ❌ FAIL: nvcc found but version check failed" -ForegroundColor Red
        $checks += @{Name="CUDA Toolkit"; Status="FAIL"; Details="nvcc command failed"}
    }
} catch {
    Write-Host "  ❌ FAIL: CUDA Toolkit not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Install from: https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
    Write-Host "  Required for CUDA RTC (Runtime Compilation) support" -ForegroundColor Yellow
    $checks += @{Name="CUDA Toolkit"; Status="FAIL"; Details="nvcc not found"}
}

# Check 3: CUDA PATH Environment
Write-Host "`n[3/8] Checking CUDA PATH environment..." -ForegroundColor Yellow
$cudaPaths = @(
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin"
)

$cudaFound = $false
foreach ($path in $cudaPaths) {
    if (Test-Path $path) {
        Write-Host "  ✅ FOUND: $path" -ForegroundColor Green
        $cudaFound = $true
        
        # Check if in PATH
        if ($env:PATH -like "*$path*") {
            Write-Host "  ✅ In PATH: Yes" -ForegroundColor Green
            $checks += @{Name="CUDA PATH"; Status="PASS"; Details=$path}
        } else {
            Write-Host "  ⚠️  In PATH: No (add to PATH manually)" -ForegroundColor Yellow
            $checks += @{Name="CUDA PATH"; Status="WARN"; Details="$path exists but not in PATH"}
        }
        break
    }
}

if (-not $cudaFound) {
    Write-Host "  ❌ FAIL: CUDA Toolkit directory not found" -ForegroundColor Red
    $checks += @{Name="CUDA PATH"; Status="FAIL"; Details="CUDA directory not found"}
}

# Check 4: NVRTC DLL (CUDA Runtime Compiler)
Write-Host "`n[4/8] Checking NVRTC library..." -ForegroundColor Yellow
$nvrtcPaths = @(
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvrtc64_*.dll",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\nvrtc64_*.dll",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin\nvrtc64_*.dll",
    "C:\Windows\System32\nvrtc64_*.dll"
)

$nvrtcFound = $false
foreach ($pattern in $nvrtcPaths) {
    $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($files) {
        Write-Host "  ✅ PASS: NVRTC library found" -ForegroundColor Green
        foreach ($file in $files) {
            Write-Host "    $($file.FullName)" -ForegroundColor Gray
        }
        $nvrtcFound = $true
        $checks += @{Name="NVRTC Library"; Status="PASS"; Details=$files[0].FullName}
        break
    }
}

if (-not $nvrtcFound) {
    Write-Host "  ❌ FAIL: nvrtc64_*.dll not found" -ForegroundColor Red
    Write-Host "  This library is required for CUDA runtime compilation in Hashcat" -ForegroundColor Yellow
    $checks += @{Name="NVRTC Library"; Status="FAIL"; Details="nvrtc64_*.dll not found"}
}

# Check 5: Hashcat Installation
Write-Host "`n[5/8] Checking Hashcat installation..." -ForegroundColor Yellow
$hashcatPaths = @(
    "C:\hashcat-7.1.2\hashcat.exe",
    "C:\hashcat\hashcat.exe",
    "$env:ProgramFiles\hashcat\hashcat.exe"
)

$hashcatFound = $false
foreach ($path in $hashcatPaths) {
    if (Test-Path $path) {
        Write-Host "  ✅ PASS: Hashcat found at $path" -ForegroundColor Green
        $hashcatFound = $true
        $hashcatPath = $path
        
        # Get version
        try {
            $version = & $path --version 2>&1 | Select-String "v\d+\.\d+\.\d+"
            Write-Host "  Version: $version" -ForegroundColor Gray
            $checks += @{Name="Hashcat"; Status="PASS"; Details="$path ($version)"}
        } catch {
            $checks += @{Name="Hashcat"; Status="PASS"; Details=$path}
        }
        break
    }
}

if (-not $hashcatFound) {
    Write-Host "  ❌ FAIL: Hashcat not found" -ForegroundColor Red
    Write-Host "  Download from: https://hashcat.net/hashcat/" -ForegroundColor Yellow
    $checks += @{Name="Hashcat"; Status="FAIL"; Details="hashcat.exe not found"}
}

# Check 6: Hashcat Backend Test
Write-Host "`n[6/8] Testing Hashcat backend initialization..." -ForegroundColor Yellow
if ($hashcatFound) {
    try {
        $backendTest = & $hashcatPath -I 2>&1 | Out-String
        
        if ($backendTest -match "CUDA") {
            Write-Host "  ✅ PASS: CUDA backend detected" -ForegroundColor Green
            $checks += @{Name="Hashcat CUDA"; Status="PASS"; Details="CUDA backend available"}
        } elseif ($backendTest -match "OpenCL") {
            Write-Host "  ⚠️  WARN: OpenCL backend only (CUDA failed)" -ForegroundColor Yellow
            Write-Host "  Hashcat will work but CUDA offers better performance" -ForegroundColor Gray
            $checks += @{Name="Hashcat CUDA"; Status="WARN"; Details="OpenCL fallback"}
        } else {
            Write-Host "  ❌ FAIL: No GPU backend detected" -ForegroundColor Red
            $checks += @{Name="Hashcat CUDA"; Status="FAIL"; Details="No backend"}
        }
        
        # Show device list
        Write-Host "`n  Detected devices:" -ForegroundColor Gray
        $backendTest -split "`n" | Where-Object { $_ -match "Device #" } | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Cyan
        }
        
    } catch {
        Write-Host "  ❌ FAIL: Hashcat backend test failed" -ForegroundColor Red
        $checks += @{Name="Hashcat CUDA"; Status="FAIL"; Details="Backend test failed"}
    }
} else {
    Write-Host "  ⏭️  SKIP: Hashcat not found" -ForegroundColor Yellow
    $checks += @{Name="Hashcat CUDA"; Status="SKIP"; Details="Hashcat not installed"}
}

# Check 7: OpenCL Runtime
Write-Host "`n[7/8] Checking OpenCL runtime..." -ForegroundColor Yellow
$openclDlls = @(
    "C:\Windows\System32\OpenCL.dll",
    "C:\Windows\SysWOW64\OpenCL.dll"
)

$openclFound = $false
foreach ($dll in $openclDlls) {
    if (Test-Path $dll) {
        Write-Host "  ✅ PASS: OpenCL runtime found" -ForegroundColor Green
        Write-Host "    $dll" -ForegroundColor Gray
        $openclFound = $true
        $checks += @{Name="OpenCL Runtime"; Status="PASS"; Details=$dll}
        break
    }
}

if (-not $openclFound) {
    Write-Host "  ⚠️  WARN: OpenCL.dll not found in System32" -ForegroundColor Yellow
    $checks += @{Name="OpenCL Runtime"; Status="WARN"; Details="OpenCL.dll not found"}
}

# Check 8: GPU Temperature & Driver Compatibility
Write-Host "`n[8/8] Checking GPU status..." -ForegroundColor Yellow
try {
    $gpuTemp = & nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,power.draw --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PASS: GPU accessible" -ForegroundColor Green
        Write-Host "  Status: $gpuTemp" -ForegroundColor Gray
        $checks += @{Name="GPU Status"; Status="PASS"; Details=$gpuTemp}
    } else {
        Write-Host "  ⚠️  WARN: Could not query GPU status" -ForegroundColor Yellow
        $checks += @{Name="GPU Status"; Status="WARN"; Details="Query failed"}
    }
} catch {
    Write-Host "  ⚠️  WARN: nvidia-smi query failed" -ForegroundColor Yellow
    $checks += @{Name="GPU Status"; Status="WARN"; Details="nvidia-smi failed"}
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passCount = ($checks | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($checks | Where-Object { $_.Status -eq "FAIL" }).Count
$warnCount = ($checks | Where-Object { $_.Status -eq "WARN" }).Count

Write-Host "`nResults: $passCount PASS / $failCount FAIL / $warnCount WARN" -ForegroundColor Cyan

foreach ($check in $checks) {
    $color = switch ($check.Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "Gray" }
    }
    Write-Host "  [$($check.Status)] $($check.Name): $($check.Details)" -ForegroundColor $color
}

# Recommendations
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($failCount -eq 0 -and $warnCount -eq 0) {
    Write-Host "✅ All checks passed! Your system is ready for GPU-accelerated cracking." -ForegroundColor Green
} else {
    if (($checks | Where-Object { $_.Name -eq "CUDA Toolkit" -and $_.Status -eq "FAIL" })) {
        Write-Host "🔧 ACTION REQUIRED: Install CUDA Toolkit" -ForegroundColor Red
        Write-Host "  1. Download CUDA 12.8 (or latest 12.x): https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
        Write-Host "  2. Choose: Windows > x86_64 > 11 > exe(local)" -ForegroundColor Yellow
        Write-Host "  3. Run installer with default options" -ForegroundColor Yellow
        Write-Host "  4. Restart computer after installation" -ForegroundColor Yellow
        Write-Host "  5. Verify with: nvcc --version`n" -ForegroundColor Yellow
    }
    
    if (($checks | Where-Object { $_.Name -eq "CUDA PATH" -and $_.Status -ne "PASS" })) {
        Write-Host "🔧 ACTION REQUIRED: Add CUDA to PATH" -ForegroundColor Red
        Write-Host "  1. Open System Properties > Environment Variables" -ForegroundColor Yellow
        Write-Host "  2. Edit 'Path' in System Variables" -ForegroundColor Yellow
        Write-Host "  3. Add: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin" -ForegroundColor Yellow
        Write-Host "  4. Click OK and restart terminal`n" -ForegroundColor Yellow
    }
    
    if (($checks | Where-Object { $_.Name -eq "NVRTC Library" -and $_.Status -eq "FAIL" })) {
        Write-Host "🔧 ACTION REQUIRED: NVRTC library missing" -ForegroundColor Red
        Write-Host "  This is included in CUDA Toolkit - install CUDA to fix.`n" -ForegroundColor Yellow
    }
    
    if (($checks | Where-Object { $_.Name -eq "Hashcat CUDA" -and $_.Status -eq "WARN" })) {
        Write-Host "⚠️  OpenCL fallback active (CUDA failed)" -ForegroundColor Yellow
        Write-Host "  Hashcat will work but slower than CUDA." -ForegroundColor Gray
        Write-Host "  To enable CUDA: Install CUDA Toolkit as shown above.`n" -ForegroundColor Gray
    }
}

Write-Host "`nDiagnostics complete. Save this output for troubleshooting." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
