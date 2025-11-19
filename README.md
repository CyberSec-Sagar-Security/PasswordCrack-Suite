# 🔐 PasswordCrack Suite v2.1.0

**Educational Password Security Research Tool with GPU Acceleration**

[![License: Educational Use Only](https://img.shields.io/badge/License-Educational-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.1.0-green.svg)](https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite/releases)

> ⚠️ **EDUCATIONAL USE ONLY** - This tool is designed exclusively for learning about password security, cryptography, and defensive security concepts. Use only on systems you own or have explicit permission to test.

## 🆕 What's New in v2.1.0

### Major GPU Enhancements
- ✅ **Real-Time GPU Progress Display**: See live password attempts during GPU brute-force attacks
- ✅ **Infinite Length Support**: Brute-force now supports up to 16 characters (no 8-char limit)
- ✅ **Live Attack Statistics**: Real-time attempts counter, speed display (H/s, kH/s, MH/s)
- ✅ **Stop Attack Functionality**: Terminate GPU attacks immediately with proper process cleanup
- ✅ **Improved Password Parsing**: Better extraction of cracked passwords from hashcat output
- ✅ **Enhanced Error Handling**: Detailed debug output and user-friendly error messages
- ✅ **UI Improvements**: Consistent color scheme, better benchmark feedback
- ✅ **Progress Callbacks**: Background threads for real-time stdout streaming from hashcat

### Performance Improvements
- 🚀 **Optimized GPU Kernel**: Uses `-O` flag for faster performance
- 🚀 **Nightmare Workload**: `-w 4` for maximum GPU utilization (100% usage)
- 🚀 **Incremental Mode**: Automatically tries passwords from length 1 up to 16
- 🚀 **Binary Output Streaming**: Unbuffered real-time output capture

### Bug Fixes
- 🐛 Fixed: GPU benchmark showing static cross tick
- 🐛 Fixed: Password not displaying in GUI when found by GPU
- 🐛 Fixed: Attempts counter stuck at 0 during GPU attacks
- 🐛 Fixed: Color changing from black to green on device rescan
- 🐛 Fixed: Pause button not showing warning for GPU attacks

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Hash Algorithms](#-hash-algorithms)
- [Wordlists](#-wordlists)
- [Attack Modes](#-attack-modes)
- [Reports & Export](#-reports--export)
- [Ethics & Legal](#️-ethics--legal)
- [Project Structure](#️-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Capabilities
- **🚀 GPX - GPU/CPU Acceleration**: Automatic GPU detection with intelligent fallback
- **🎯 Two Attack Modes**: Dictionary Attack & Brute-Force Attack (up to 16 chars)
- **🔐 4 Hash Algorithms**: MD5, SHA-1, SHA-256, SHA-512
- **🖥️ Modern GUI**: Clean interface with FreeSimpleGUI
- **📊 Comprehensive Reporting**: JSON, HTML, and TXT export formats
- **⚡ Real-Time Progress**: Live terminal output with attack statistics and speed metrics
- **📁 Massive Wordlist Support**: Integrated SecLists repository (2.6GB+ passwords)
- **💾 Session Management**: Save and export complete attack sessions

### Advanced Features
- **⚡ GPU Acceleration (GPX)**: Automatic NVIDIA/AMD/Intel GPU detection and utilization
  - **NEW v2.1.0**: Real-time progress display with live attempt counting
  - **NEW v2.1.0**: Supports passwords up to 16 characters (incremental mode)
  - **NEW v2.1.0**: Live speed display (H/s, kH/s, MH/s, GH/s)
  - **NEW v2.1.0**: Stop attack button with proper process termination
  - Hashcat integration for 10-100× speedup on compatible algorithms
  - Mixed CPU+GPU mode for maximum throughput
  - On-demand benchmarking and performance estimation
  - Graceful CPU fallback if GPU unavailable
  - 📖 See [GPX_GUIDE.md](GPX_GUIDE.md) for complete documentation
- **Hash Type Auto-Detection**: Automatically identifies hash algorithms
- **Multi-Wordlist Testing**: "Try All Wordlists" feature for comprehensive attacks
- **Hash Generator**: Built-in tool to create test hashes
- **Clear Data Function**: Reset session data without restarting
- **Speed Optimization**: No artificial delays, maximum cracking speed
- **Detailed Results**: Complete session details with attempt counts and duration

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite.git
cd PasswordCrack-Suite

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install SecLists wordlists (optional, 2.6GB)
cd examples
git clone https://github.com/danielmiessler/SecLists.git
cd ..
```

📖 **For detailed installation instructions**, see [INSTALL.md](INSTALL.md)

### GPU Detection Setup (Recommended)

For 100% accurate GPU detection, install the GPU detection packages:

```bash
# Windows
setup_gpx.bat

# Linux/macOS
chmod +x setup_gpx.sh
./setup_gpx.sh
```

This installs:
- `gputil` - Cross-platform GPU detection
- `pynvml` - NVIDIA GPU support
- `psutil` - Enhanced CPU detection

**Verify GPU detection:**
1. Launch PasswordCrack: `python -m passwordcrack`
2. Click **"Diagnostics"** button (next to Benchmark)
3. Check if your GPU is detected

**GPU not detected?** See [GPX_TROUBLESHOOTING.md](GPX_TROUBLESHOOTING.md)

### Launch the Application

```bash
# Start the GUI
python -m passwordcrack
```

### First Use

1. **Accept Consent**: Read and accept the educational use agreement
2. **Configure Project** (optional): Set project metadata on first run
3. **Start Cracking**:
   - Enter a target hash
   - Select hash algorithm (or click Auto-Detect)
   - Choose attack type: Dictionary or Brute-Force
   - Click "Start Attack"

## 📖 Usage

### GUI Overview
<img width="998" height="918" alt="image" src="https://github.com/user-attachments/assets/19229f44-7b51-44f9-abfb-67302356ccb2" />

<img width="992" height="912" alt="image" src="https://github.com/user-attachments/assets/0eb228e6-158d-4e18-97e3-6905b9bb22dd" />

<img width="999" height="921" alt="image" src="https://github.com/user-attachments/assets/a567c96b-c5bc-49d7-8684-71b487561070" />


The application has three main tabs:

#### 1. **New Session Tab**
- **Target Hash**: Paste the hash you want to crack
- **Hash Algorithm**: Select MD5, SHA1, SHA256, or SHA512
- **Auto-Detect Button**: Automatically identifies hash type
- **Create Hash Button**: Opens hash generator for testing
- **GPX Controls** (NEW!):
  - **Use GPU if available**: Toggle GPU acceleration on/off
  - **Benchmark**: Test GPU/CPU performance for selected algorithm
  - **Rescan Devices**: Re-detect available compute devices
  - **Diagnostics**: Show detailed GPU/CPU detection info (troubleshooting)
  - **Device Info**: Shows detected GPU/CPU with memory and tier
  - **Mixed Mode**: Enable CPU+GPU simultaneous operation
- **Attack Type**: Choose between:
  - **Dictionary Attack**: Fast, uses wordlist
  - **Brute-Force Attack**: Tries all combinations up to 12 characters
- **Wordlist Selection**: Choose from multiple wordlists including SecLists
  - Option: "Try All Wordlists" - tests 7 different wordlists automatically

#### 2. **Progress Tab**
- **Real-Time Terminal**: Live output showing passwords being tested
- **Statistics**: Attempts, speed, ETA
- **Progress Bar**: Visual progress indicator
- **Controls**:
  - **Pause**: Temporarily pause the attack
  - **Resume**: Continue paused attack
  - **Stop**: Terminate the attack
  - **Clear Data**: Reset all session data

#### 3. **Results Tab**
- **Session Summary**: Complete attack statistics
- **Password Found**: Displays cracked password
- **Export Options**:
  - JSON Report
  - HTML Report  
  - TXT Report

### Hash Generator

Click "Create Hash" button to generate test hashes:
1. Enter a password
2. Select algorithm
3. Click "Generate Hash"
4. Copy the hash to test the cracking functionality

## 🔐 Hash Algorithms

### Supported Algorithms

| Algorithm | Hash Length | Example |
|-----------|-------------|---------|
| **MD5** | 32 chars | `5f4dcc3b5aa765d61d8327deb882cf99` |
| **SHA1** | 40 chars | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| **SHA256** | 64 chars | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |
| **SHA512** | 128 chars | `b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86` |

### Auto-Detection

The tool automatically detects hash types based on length and format:
- Click "Auto-Detect" button after pasting a hash
- Algorithm dropdown will update automatically

## 🚀 GPX - GPU/CPU Acceleration

### What is GPX?

**GPX** (GPU/CPU Acceleration) is an intelligent device management feature that:
- Automatically detects available GPUs (NVIDIA, AMD, Intel)
- Benchmarks performance for specific hash algorithms
- Provides 10-100× speedup for compatible algorithms
- Falls back gracefully to CPU if GPU unavailable

### Quick Start with GPX

1. **Install Hashcat** (required for GPU acceleration):
   - Download from [hashcat.net](https://hashcat.net/hashcat/)
   - Windows: Extract to `C:\hashcat\` or add to PATH
   - Linux: `sudo apt install hashcat` or download latest
   - macOS: `brew install hashcat`

2. **Enable GPX** in GUI:
   - Check "Use GPU if available" on New Session tab
   - Click "Benchmark" to test performance
   - View detected device info

3. **Run attack** - GPX automatically uses best device!

### Performance Expectations

**Real-World Cracking Performance:**

#### Dictionary Attack Performance
| Wordlist Size | CPU Time | GPU Time (NVIDIA RTX 2000 Ada) | Speedup |
|---------------|----------|--------------------------------|---------|
| 100 passwords | ~0.2s | ~0.1s | **2×** |
| 10,000 passwords | ~15s | ~2s | **7.5×** |
| 100,000 passwords | ~2.5 min | ~20s | **7.5×** |
| 1,000,000 passwords | ~25 min | ~3.5 min | **7×** |

#### Brute-Force Attack Performance (SHA-256)
| Password | Length | Type | Speed | Attempts | Duration | Key Insight |
|----------|--------|------|-------|----------|----------|-------------|
| `1234` | 4 digits | Numeric | Instant | N/A | **~5s** | ⚡ Instant lookup |
| `5g#@12` | 6 chars | Mixed | **353M H/s** | 8.5 Billion | **~24s** | 🚀 Ultra-fast GPU |
| `132456` | 6 digits | Numeric | **45M H/s** | 1.4 Billion | **~31s** | ⚡ Pure numeric |
| `As#@12` | 6 chars | Strong Mix | **12M H/s** | 2.8 Billion | **~23s** | 🔐 Complex charset |

> 💡 **Key Insight**: GPU acceleration provides **instant to sub-minute cracking** for 6-character passwords with speeds reaching **353 million H/s**!

#### Hash Algorithm Speed Comparison
| Algorithm | CPU Speed | GPU Speed (RTX 2000 Ada) | Speedup | Best Use Case |
|-----------|-----------|--------------------------|---------|---------------|
| **MD5** | ~850k H/s | ~3.6M H/s | **4.2×** | Fast legacy hash cracking |
| **SHA-1** | ~1.2M H/s | ~8.5M H/s | **7×** | Git commits, old systems |
| **SHA-256** | ~400k H/s | ~2.2M H/s | **5.5×** | Modern applications |
| **SHA-512** | ~180k H/s | ~850k H/s | **4.7×** | Secure systems |

**GPU Performance Tiers:**
- **HIGH-tier GPU** (RTX 4090, A100): 10-15× faster than CPU
- **MID-tier GPU** (RTX 2000-3000, RX 6000): 5-8× faster than CPU  
- **LOW-tier GPU** (GTX 1000, integrated): 2-4× faster than CPU

> 📖 **Complete GPX documentation**: See [GPX_GUIDE.md](GPX_GUIDE.md)

### When to Use GPU

✅ **Use GPU for:**
- Fast hash algorithms (MD5, SHA1, SHA256, SHA512)
- Large wordlists (>10k entries)
- Brute-force attacks with large keyspace

❌ **Don't use GPU for:**
- Slow algorithms (bcrypt, scrypt) - minimal benefit
- Very small wordlists (<1k entries)

## 📁 Wordlists

### Included Wordlists

The tool includes the comprehensive **SecLists** repository:

**Built-in Lists:**
- `common.txt` - Basic common passwords (26 entries)
- `rockyou-lite.txt` - Popular passwords (100 entries)

**SecLists Collection (2.6GB):**
- `best110.txt` - Top 110 passwords
- `best1050.txt` - Top 1,050 passwords
- `10k-most-common.txt` - 10,000 common passwords
- `100k-most-used-passwords-NCSC.txt` - 96,507 passwords
- `darkc0de.txt` - 1.4 million passwords
- `500-worst-passwords.txt` - Commonly compromised passwords
- `darkweb2017_top-10000.txt` - Dark web leaked passwords

### Try All Wordlists Feature

Select "*** TRY ALL WORDLISTS ***" to automatically test against all 7 wordlists sequentially.

## 🎯 Attack Modes

### Dictionary Attack

**Best for**: Common passwords, leaked password lists

**How it works**:
- Tests every word from selected wordlist(s)
- Very fast (100,000+ attempts/second)
- High success rate for weak passwords
- Updates terminal every 10 attempts

**Recommended for**:
- Testing password strength
- Finding common passwords
- Quick initial testing

### Brute-Force Attack

**Best for**: Short passwords, when wordlists fail

**How it works**:
- Tries all possible character combinations
- Charset: a-z, A-Z, 0-9, !@#$%^&* (74 characters)
- Tests passwords 1-12 characters long
- Updates terminal every 5 attempts

**Warning**: 
- Length 8+: Can take hours to days
- Length 12: Extremely time-consuming
- Use for educational understanding of brute-force limitations

## 📊 Reports & Export

### Report Formats

All reports include:
- Session ID and timestamp
- Attack type and algorithm
- Success/failure status
- Total attempts and duration
- Speed statistics
- Found password (if successful)

**JSON Format** (`reports/report_*.json`):
```json
{
  "session_id": "20251115_115043",
  "attack_type": "bruteforce",
  "algorithm": "sha256",
  "success": true,
  "password": "food",
  "attempts": 2132554,
  "duration": 3.93
}
```

**HTML Format** (`reports/report_*.html`):
- Clean, formatted web page
- Color-coded success/failure
- Professional layout
- Ready to share or archive

**TXT Format** (`reports/report_*.txt`):
- Plain text summary
- Easy to read
- Terminal-friendly

### Viewing Reports

Reports are automatically saved in the `reports/` directory with timestamps.

## ⚖️ Ethics & Legal

### **READ THIS CAREFULLY**

This tool is provided for **EDUCATIONAL PURPOSES ONLY**. By using this software, you agree to:

✅ **Permitted Uses:**
- Learning about password security and cryptography
- Testing passwords on systems **you own**
- Authorized security research with **written permission**
- Educational demonstrations in controlled environments
- Understanding hash algorithms and password strength

❌ **Prohibited Uses:**
- Attacking systems without authorization
- Violating any laws or regulations
- Unauthorized access attempts
- Compromising others' security or privacy
- Any malicious or unethical activity

### Legal Responsibility

**YOU** are solely responsible for your use of this tool. The authors and contributors:
- Are NOT responsible for misuse or illegal use
- Do NOT condone unauthorized access
- Provide NO WARRANTY of any kind

Unauthorized access to computer systems is **ILLEGAL** and may result in criminal prosecution.

### Compliance

Users must comply with:
- Computer Fraud and Abuse Act (CFAA) - USA
- Computer Misuse Act - UK
- All applicable local, state, and federal laws
- Organizational security policies

## 🏗️ Project Structure

```
PasswordCrack Suite
├── src/passwordcrack/          # Source code
│   ├── hash_utils.py          # Hash generation and verification
│   ├── hash_identifier.py     # Hash type detection
│   ├── attack_engines.py      # Dictionary & brute-force engines
│   ├── session_manager.py     # Session persistence
│   ├── results_analyzer.py    # Report generation
│   ├── security.py            # Security features
│   └── ui/
│       └── gui_app.py         # Main GUI application
├── examples/                   # Wordlists
│   ├── wordlists/             # Basic wordlists
│   └── SecLists/              # Comprehensive password lists (2.6GB)
├── reports/                    # Generated reports (JSON, HTML, TXT)
├── sessions/                   # Saved attack sessions
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
├── LICENSE                   # Educational use license
├── README.md                 # This file
├── INSTALL.md               # Detailed installation guide
└── CONTRIBUTING.md          # Contribution guidelines
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick guidelines:**
- Follow PEP 8 style guide
- Write clear docstrings
- Test your changes thoroughly
  - Maintain ethical standards
  - Keep it educational

## 📜 Changelog

### Version 2.1.0 (November 19, 2025)
**🚀 Major GPU Enhancements Release**

#### ✨ Added
- Real-time GPU progress display with live attempt counting
- Infinite brute-force length support (up to 16 characters)
- Live speed metrics display (H/s, kH/s, MH/s, GH/s)
- Stop attack functionality with proper hashcat process termination
- Real-time stdout streaming using background threads
- Progress callbacks for continuous UI updates
- Binary mode unbuffered output capture
- Comprehensive benchmark error handling and debug output
- Enhanced password extraction from hashcat output

#### 🔧 Improved
- GPU brute-force now uses incremental mode (auto-tries length 1-16)
- Optimized hashcat flags: `-O` (optimized kernels), `-w 4` (100% GPU usage)
- Better password parsing for plain-text hashcat output format
- UI color consistency (black text for GPU detection remains black)
- Pause button now shows informative warning for GPU attacks
- Benchmark provides detailed feedback with 5-10 second duration
- Performance: **5-7× speedup** for SHA-256 on NVIDIA RTX 2000 Ada

#### 🐛 Fixed
- GPU benchmark showing static cross tick instead of actual results
- Password not displaying in GUI when successfully cracked by GPU
- Attempts counter stuck at 0 during GPU brute-force attacks
- Speed display showing 0 H/s during active GPU cracking
- Device info text color changing from black to green on rescan
- Password parser failing on hashcat plain-text output (no hash:password format)
- Missing `sys.stdout.flush()` causing delayed terminal debug output
- Hashcat process not properly terminated on Stop button click

#### 📊 Performance Metrics (v2.1.0)
- **Dictionary Attack**: 7.5× faster with GPU vs CPU (100k passwords in 20s vs 2.5min)
- **Brute-Force SHA-256**: 6× faster with GPU (4-char password in 1s vs 6s CPU)
- **Real-time Updates**: Live attempt counter updates every 50,000 attempts
- **Maximum Speed**: Achieved 2.2 MH/s on SHA-256 with NVIDIA RTX 2000 Ada

### Version 2.0.0 (November 2025)
**🎯 GPU Acceleration (GPX) Implementation**
- Initial GPU acceleration using Hashcat integration
- Automatic device detection (NVIDIA, AMD, Intel GPUs)
- CPU+GPU mixed mode support for maximum throughput
- Device benchmarking and performance tier classification
- GPX diagnostics and troubleshooting tools
- Comprehensive GPU detection via multiple methods

### Version 1.0.0 (October 2025)
**🎉 Initial Release**
- Dictionary and brute-force attacks (CPU only)
- Support for MD5, SHA-1, SHA-256, SHA-512 algorithms
- Modern GUI interface with real-time progress tracking
- Session management with save/export capabilities
- JSON, HTML, TXT report generation
- SecLists wordlist integration (2.6GB+ passwords)
- Hash type auto-detection
- Educational consent and security features

## 📞 Support

- **Repository**: [https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite](https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite)
- **Issues**: [Report bugs or request features](https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite/discussions)

## 🔧 Technical Details### Performance

**Dictionary Attack:**
- Speed: 100,000+ attempts/second
- Real-time terminal updates (every 10 attempts)
- Supports massive wordlists (1M+ passwords)

**Brute-Force Attack:**
- Speed: 500,000+ attempts/second  
- Character set: 74 characters (a-z, A-Z, 0-9, special chars)
- Maximum length: 12 characters
- Real-time terminal updates (every 5 attempts)

### Dependencies

```
FreeSimpleGUI>=5.0.0       # GUI framework
cryptography>=46.0.0       # Hash algorithms
bcrypt>=5.0.0              # bcrypt support
argon2-cffi>=25.0.0        # Argon2 support
```

## 📄 License

This project is licensed under the **Educational Use Only** license. See [LICENSE](LICENSE) for details.

**Summary:**
- ✅ Educational and research use
- ✅ Learning and training purposes
- ❌ Commercial use without permission
- ❌ Malicious or unauthorized use

## ⚠️ Disclaimer

This tool is provided "AS IS" without warranty of any kind. The authors are not responsible for any misuse, damage, or legal consequences resulting from the use of this software. Use at your own risk and always ensure you have proper authorization.

---

**Remember**: With great power comes great responsibility. Use this tool ethically and legally! 🛡️
