# Contributing to PasswordCrack Suite

Thank you for your interest in contributing to PasswordCrack Suite! This document provides guidelines for contributing to this educational security research tool.

## 🎯 Project Mission

PasswordCrack Suite is an **educational tool** designed to teach password security, cryptography, and defensive security concepts. All contributions must align with this educational mission and ethical use policy.

## 📋 Code of Conduct

### Ethical Guidelines

By contributing, you agree to:

✅ **Support educational use only**
- Focus on learning and security research
- Maintain ethical standards
- Include proper warnings and disclaimers

❌ **Never contribute features that:**
- Enable malicious use
- Bypass authorization mechanisms
- Violate ethical hacking principles
- Compromise security or privacy

## 🔧 How to Contribute

### 1. Setting Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/PasswordCrack-Suite.git
cd PasswordCrack-Suite

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Making Changes

1. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test thoroughly** - ensure nothing breaks

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add: Brief description of changes"
   ```

### 3. Submitting Pull Requests

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub

3. **Describe your changes**:
   - What does this PR do?
   - Why is it needed?
   - How was it tested?

4. **Wait for review** - maintainers will review and provide feedback

## 💻 Coding Standards

### Python Style Guide

- Follow **PEP 8** guidelines
- Use **type hints** where appropriate
- Write **clear docstrings** for functions and classes
- Keep functions **focused and small**
- Use **meaningful variable names**

### Example:

```python
def generate_hash(password: str, algorithm: HashAlgorithm) -> str:
    """
    Generate a hash from a password using the specified algorithm.
    
    Args:
        password: The password to hash
        algorithm: The hashing algorithm to use
        
    Returns:
        The generated hash as a hexadecimal string
        
    Raises:
        ValueError: If algorithm is not supported
    """
    password_bytes = password.encode('utf-8')
    
    if algorithm == HashAlgorithm.SHA256:
        return hashlib.sha256(password_bytes).hexdigest()
    # ... more implementations
```

### Code Organization

- **One class per file** when possible
- **Group related functions** in modules
- **Keep UI separate** from business logic
- **Use dependency injection** for testability

## 🧪 Testing

### Before Submitting

1. **Test your changes manually**:
   ```bash
   python -m passwordcrack
   ```

2. **Verify all features still work**:
   - Dictionary attack
   - Brute-force attack
   - Hash generation
   - Auto-detection
   - Report generation

3. **Check for errors**:
   - No console errors
   - All buttons functional
   - No crashes

## 📝 Documentation

### Update Documentation

When adding features, update:

- **README.md** - User-facing features
- **Code comments** - Implementation details
- **Docstrings** - Function/class documentation

### Documentation Style

```python
class AttackEngine:
    """
    Base class for password attack engines.
    
    This class provides common functionality for all attack types
    including progress tracking, pause/resume, and result handling.
    
    Attributes:
        running: Whether the attack is currently running
        paused: Whether the attack is paused
        attempts: Number of passwords tried
    """
```

## 🎯 Contribution Ideas

### Welcome Contributions

- **Performance improvements** to attack engines
- **New wordlists** or wordlist sources
- **UI/UX enhancements** for better usability
- **Bug fixes** and error handling
- **Documentation improvements**
- **Code optimization** and refactoring
- **Additional hash algorithms** (ethical ones only)
- **Better progress indicators**
- **Export format improvements**

### Not Accepting

- Features for unauthorized access
- Malicious attack methods
- Privacy-violating capabilities
- Commercial/paid features
- Cryptocurrency miners
- Network attack tools

## 🐛 Reporting Bugs

### Bug Reports Should Include

1. **Description** - What happened?
2. **Steps to reproduce** - How can we recreate it?
3. **Expected behavior** - What should happen?
4. **Actual behavior** - What actually happened?
5. **Environment**:
   - OS (Windows/Linux/Mac)
   - Python version
   - Tool version

### Example Bug Report

```markdown
**Description**: Dictionary attack fails with large wordlists

**Steps to Reproduce**:
1. Select darkc0de.txt wordlist
2. Start dictionary attack
3. Application crashes after 10,000 attempts

**Expected**: Attack should complete successfully

**Actual**: Application crashes with MemoryError

**Environment**:
- Windows 11
- Python 3.13.8
- PasswordCrack Suite v1.0
```

## 🔒 Security

### Reporting Security Issues

If you find a security vulnerability:

1. **DO NOT** open a public issue
2. **Email** the maintainers privately
3. **Include** details of the vulnerability
4. **Wait** for a response before disclosure

## 📜 License

By contributing, you agree that your contributions will be licensed under the same **Educational Use Only** license as the project.

## ❓ Questions?

- Open a **Discussion** on GitHub
- Check existing **Issues** and **Pull Requests**
- Read the **README.md** for basic usage

## 🙏 Thank You!

Your contributions help make security education better for everyone. We appreciate your time and effort!

---

**Remember**: This is an educational tool. Keep it ethical, keep it legal, keep it educational! 🎓🛡️
