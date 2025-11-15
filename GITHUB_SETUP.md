# PasswordCrack Suite - GitHub Setup Guide

This guide will help you push your project to GitHub.

## 📋 Prerequisites

- Git installed on your system
- GitHub account created
- Repository created: `https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite`

## 🚀 Push to GitHub

### Step 1: Initialize Git (if not already done)

```bash
cd PasswordCrack-Suite
git init
```

### Step 2: Add Remote Repository

```bash
git remote add origin https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite.git
```

### Step 3: Stage Files

```bash
# Add all files
git add .

# Or add specific files/directories:
git add src/
git add examples/wordlists/
git add requirements.txt
git add README.md
git add LICENSE
git add .gitignore
git add CONTRIBUTING.md
git add INSTALL.md
```

### Step 4: Commit Changes

```bash
git commit -m "Initial commit: PasswordCrack Suite - Educational Password Security Tool"
```

### Step 5: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

## ⚠️ Important Notes

### What NOT to Push

The `.gitignore` file already excludes:
- `config.json` - User configuration
- `sessions/` - Saved sessions (privacy)
- `reports/` - Generated reports (user data)
- `.venv/` - Virtual environment
- `examples/SecLists/` - Large wordlist repository (2.6GB)

### SecLists Installation

**Do NOT push SecLists to your repository!**

Users should clone it separately:
```bash
cd examples
git clone https://github.com/danielmiessler/SecLists.git
```

Add this to README if not already present.

## 📁 What Will Be Pushed

- ✅ Source code (`src/passwordcrack/`)
- ✅ Built-in wordlists (`examples/wordlists/`)
- ✅ Documentation (README.md, INSTALL.md, CONTRIBUTING.md)
- ✅ Configuration files (requirements.txt, pyproject.toml)
- ✅ License file
- ✅ .gitignore
- ✅ Empty directories (sessions/, reports/) with .gitkeep

## 🔄 Subsequent Pushes

After the initial push, use:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Your commit message here"

# Push to GitHub
git push
```

## 🏷️ Create a Release (Optional)

### Tag a Version

```bash
git tag -a v1.0.0 -m "PasswordCrack Suite v1.0.0 - Initial Release"
git push origin v1.0.0
```

### Create Release on GitHub

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select tag: `v1.0.0`
4. Release title: `v1.0.0 - Initial Release`
5. Description: Add release notes
6. Click "Publish release"

## 📝 Recommended Commit Message Format

```
Type: Brief description

Longer description if needed
- Bullet point 1
- Bullet point 2

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- perf: Performance improvements
- test: Adding tests
- chore: Maintenance tasks
```

### Examples:

```bash
git commit -m "feat: Add brute-force attack engine with 74-char charset"
git commit -m "fix: Resolve hash detection issue for SHA512"
git commit -m "docs: Update README with SecLists installation"
git commit -m "perf: Optimize dictionary attack speed (100k+ H/s)"
```

## 🌳 Branch Strategy

### Main Branch

- Keep `main` stable and production-ready
- Only merge tested, working code

### Feature Branches

```bash
# Create feature branch
git checkout -b feature/new-hash-algorithm

# Work on feature...
git add .
git commit -m "feat: Add SHA3-256 support"

# Push feature branch
git push -u origin feature/new-hash-algorithm

# Create Pull Request on GitHub
# Merge after review
```

## 🛡️ Security Checks

Before pushing, verify:

```bash
# Check what will be committed
git status

# Review changes
git diff

# Ensure no sensitive data
grep -r "password\|secret\|key" .
```

## 📊 Repository Settings

### Recommended GitHub Settings

1. **Branch Protection**:
   - Protect `main` branch
   - Require pull request reviews

2. **Topics/Tags**:
   - `password-security`
   - `cryptography`
   - `educational`
   - `hash-cracking`
   - `python`
   - `security-tools`

3. **Description**:
   ```
   Educational password security research tool with dictionary and brute-force attack engines. Supports MD5, SHA1, SHA256, SHA512 hashing. Built with Python & FreeSimpleGUI. For learning purposes only.
   ```

4. **Website**:
   - Add your documentation site (if any)

## ✅ Verification

After pushing, verify on GitHub:

1. ✅ All files uploaded correctly
2. ✅ README.md displays properly
3. ✅ .gitignore working (no config.json, .venv, etc.)
4. ✅ License shows in repository
5. ✅ Repository topics/tags set

## 🎉 You're Done!

Your project is now on GitHub! Share the link:

```
https://github.com/CyberSec-Sagar-Security/PasswordCrack-Suite
```

## 🔗 Useful Git Commands

```bash
# View current status
git status

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- <file>

# Pull latest changes
git pull origin main

# View remote URL
git remote -v

# Update remote URL
git remote set-url origin <new-url>
```

---

**Remember**: Keep your code clean, commit often, and always verify before pushing! 🚀
