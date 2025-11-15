# Installation Guide

This guide will help you set up **PasswordCrack Suite** on your system.

## 📋 Prerequisites

- **Python 3.13+** installed ([Download here](https://www.python.org/downloads/))
- **Git** installed (for cloning SecLists)
- **10GB+ free disk space** (for SecLists wordlists)
- **Windows, Linux, or macOS**

## 🚀 Quick Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite.git
cd PasswordCrack-Suite
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Windows CMD:
.\.venv\Scripts\activate.bat

# Linux/Mac:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install SecLists Wordlists (Optional but Recommended)

```bash
# Navigate to examples directory
cd examples

# Clone SecLists repository (2.6GB download)
git clone https://github.com/danielmiessler/SecLists.git

# Return to project root
cd ..
```

### Step 5: Launch the Application

```bash
python -m passwordcrack
```

## 📦 What Gets Installed

### Python Packages

```
FreeSimpleGUI==5.2.0.post1    # Modern GUI framework
cryptography==46.0.3          # Cryptographic operations
bcrypt==5.0.0                 # bcrypt hashing
argon2-cffi==25.1.0          # Argon2 hashing
```

### Project Structure

```
PasswordCrack-Suite/
├── .venv/                    # Virtual environment (created by you)
├── src/passwordcrack/        # Application source code
├── examples/
│   ├── wordlists/           # Built-in wordlists
│   └── SecLists/            # Large wordlist collection (optional)
├── reports/                  # Generated reports (empty initially)
├── sessions/                 # Saved sessions (empty initially)
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

## 🔧 Troubleshooting

### Python Version Issues

**Error**: `Python 3.13+ required`

**Solution**:
```bash
# Check your Python version
python --version

# If below 3.13, download latest from python.org
```

### FreeSimpleGUI Installation Issues

**Error**: `No module named 'FreeSimpleGUI'`

**Solution**:
```bash
# Ensure virtual environment is activated
pip install --upgrade pip
pip install -r requirements.txt
```

### SecLists Clone Too Slow

**Solution**: Use shallow clone to download faster
```bash
git clone --depth 1 https://github.com/danielmiessler/SecLists.git
```

### Permission Errors (Windows)

**Error**: `Execution policy prevents script`

**Solution**: Run PowerShell as Administrator
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'passwordcrack'`

**Solution**: Ensure you're in the project root directory
```bash
cd PasswordCrack-Suite
python -m passwordcrack
```

## 🖥️ Platform-Specific Notes

### Windows

- Use PowerShell (not CMD) for best experience
- Activate virtual environment: `.\.venv\Scripts\Activate.ps1`
- May need to adjust execution policy (see above)

### Linux/macOS

- Use terminal
- Activate virtual environment: `source .venv/bin/activate`
- May need `sudo` for some package installations

### macOS M1/M2

- All packages have ARM64 support
- No special configuration needed

## 📊 Verifying Installation

### Quick Test

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows

# 2. Launch application
python -m passwordcrack

# 3. You should see:
#    - Consent screen
#    - Project configuration (first run)
#    - Main GUI window
```

### Test Hash Cracking

1. Click "Create Hash" button
2. Enter password: `test`
3. Select algorithm: `SHA256`
4. Click "Generate Hash"
5. Copy the generated hash
6. Paste into "Target Hash" field
7. Click "Auto-Detect"
8. Select "Dictionary Attack"
9. Choose wordlist: `common.txt`
10. Click "Start Attack"
11. Password should be found quickly!

## 🔄 Updating

### Update Application

```bash
cd PasswordCrack-Suite
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update SecLists

```bash
cd examples/SecLists
git pull origin master
cd ../..
```

## 🗑️ Uninstallation

```bash
# 1. Deactivate virtual environment
deactivate

# 2. Delete project directory
cd ..
rm -rf PasswordCrack-Suite  # Linux/Mac
Remove-Item -Recurse -Force PasswordCrack-Suite  # Windows PowerShell
```

## ✅ Next Steps

After successful installation:

1. **Read the README.md** for usage instructions
2. **Review Ethics & Legal** section
3. **Try the Hash Generator** to create test hashes
4. **Run a Dictionary Attack** with common.txt
5. **Explore SecLists** wordlists
6. **Generate Reports** to see export formats

## 📞 Need Help?

- Check [README.md](README.md) for usage guide
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development
- Open an issue on GitHub
- Ensure you're using Python 3.13+

---

**Happy (Ethical) Hacking!** 🔐🛡️
