# 🔐 PasswordCrack Suite

**Educational Password Security Research Tool**

[![License: Educational Use Only](https://img.shields.io/badge/License-Educational-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

> ⚠️ **EDUCATIONAL USE ONLY** - This tool is designed exclusively for learning about password security, cryptography, and defensive security concepts. Use only on systems you own or have explicit permission to test.

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
- **🎯 Two Attack Modes**: Dictionary Attack & Brute-Force Attack
- **🔐 4 Hash Algorithms**: MD5, SHA-1, SHA-256, SHA-512
- **🖥️ Modern GUI**: Clean interface with FreeSimpleGUI
- **📊 Comprehensive Reporting**: JSON, HTML, and TXT export formats
- **⚡ Real-Time Progress**: Live terminal output with attack statistics
- **📁 Massive Wordlist Support**: Integrated SecLists repository (2.6GB+ passwords)
- **💾 Session Management**: Save and export complete attack sessions

### Advanced Features
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

The application has three main tabs:

#### 1. **New Session Tab**
- **Target Hash**: Paste the hash you want to crack
- **Hash Algorithm**: Select MD5, SHA1, SHA256, or SHA512
- **Auto-Detect Button**: Automatically identifies hash type
- **Create Hash Button**: Opens hash generator for testing
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

## 🔧 Technical Details

### Performance

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
