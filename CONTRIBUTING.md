# Contributing to Ani 💜

Thank you for your interest in contributing to Ani! We welcome all contributions, from bug reports to feature implementations. This guide will help you get started.

---

## 📋 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- Pip

### Development Setup

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub
   ```

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Ani.git
   cd Ani
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Set Up Pre-commit Hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

---

## 📝 Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Keep commits focused and logical
- Write clear commit messages
- Follow the coding style guidelines (see below)

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_api_endpoints.py -v
```

### 4. Code Quality Checks

```bash
# Format code with Black
black .

# Check code style with Flake8
flake8 . --max-line-length=120

# Type checking with mypy
mypy app --ignore-missing-imports

# Security check with Bandit
bandit -r app
```

### 5. Commit and Push

```bash
# Commit with clear message
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to https://github.com/cid-kageno-dev/Ani
- Click "New Pull Request"
- Select your branch
- Fill in the PR template
- Submit!

---

## 🎨 Coding Style Guide

### Python Style (PEP 8 + Black)

```python
# ✅ Good
def get_user_data(user_id: int) -> dict[str, str]:
    """Fetch user data from database.
    
    Args:
        user_id: The unique user identifier.
        
    Returns:
        Dictionary containing user information.
    """
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

# ❌ Bad
def get_user_data(uid):
    q="SELECT * FROM users WHERE id = "+str(uid)
    return execute_query(q)
```

### Naming Conventions

- **Functions/Variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** Prefix with `_`

### Docstrings

```python
def process_message(message: str) -> str:
    """Process a user message.
    
    Args:
        message: The raw user message.
        
    Returns:
        Processed and cleaned message.
        
    Raises:
        ValueError: If message is empty.
    """
    if not message:
        raise ValueError("Message cannot be empty")
    return message.strip().lower()
```

### Type Hints

```python
from typing import Optional, List

def get_repositories(
    username: str,
    limit: Optional[int] = None
) -> List[dict[str, str]]:
    """Get repositories for a user."""
    pass
```

---

## ✅ Testing Guidelines

### Test Structure

```python
import pytest
from app import create_app

def test_health_endpoint():
    """Test the health check endpoint."""
    app = create_app()
    client = app.test_client()
    
    response = client.get('/health')
    
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_chat_with_empty_message():
    """Test chat endpoint with empty message."""
    app = create_app()
    client = app.test_client()
    
    response = client.post('/api/chat', json={'message': ''})
    
    assert response.status_code == 400
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_config_loading():
    pass

@pytest.mark.integration
def test_chat_flow():
    pass

@pytest.mark.slow
def test_large_dataset():
    pass
```

### Minimum Coverage Requirements

- **Target:** 80% code coverage
- **Minimum:** 70% for PRs to pass
- Check: `pytest --cov=app --cov-report=html`

---

## 🐛 Bug Reports

### How to Report

1. **Check existing issues** to avoid duplicates
2. **Use GitHub Issues** with the bug template
3. **Include:**
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version, OS, and environment
   - Relevant logs or error messages

### Example

```markdown
## Description
Chat endpoint returns 500 error when message is very long.

## Steps to Reproduce
1. Send a POST request to `/api/chat`
2. Include a message longer than 5000 characters
3. Observe the response

## Expected
Should truncate or return 400 with message

## Actual
Returns 500 Internal Server Error

## Environment
- Python: 3.11
- OS: Ubuntu 22.04
- Branch: main
```

---

## 🎯 Feature Requests

### How to Request

1. **Search existing issues** first
2. **Use GitHub Issues** with the feature template
3. **Include:**
   - Clear description
   - Use case/motivation
   - Possible implementation approach
   - Any concerns or considerations

---

## 📖 Commit Message Format

We follow the Conventional Commits standard:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation
- **style:** Code style (no functionality)
- **refactor:** Code refactoring
- **perf:** Performance improvement
- **test:** Test additions/changes
- **ci:** CI/CD pipeline changes
- **chore:** Dependency updates, etc.

### Examples

```
feat(api): add user authentication endpoint

Implement JWT-based authentication for API.
Supports login and token refresh.

Closes #123
```

```
fix(cache): prevent cache overflow

Limit cache size to 1000 entries.
Implement LRU eviction policy.

Fixes #456
```

---

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Related Issues
Closes #(issue number)

## Testing
Describe testing done.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No breaking changes
```

---

## 🔄 Code Review Process

1. **Automated Checks**
   - Tests must pass
   - Coverage must be >= 70%
   - Code quality checks pass
   - Security scan passes

2. **Maintainer Review**
   - Code quality
   - Design consistency
   - Documentation
   - Performance implications

3. **Feedback & Iteration**
   - Address review comments
   - Re-request review
   - CI must pass again

4. **Merge**
   - Squash and merge or rebase
   - Follow commit conventions

---

## 📚 Documentation

### Updating Docs

- Update README.md for user-facing changes
- Update docstrings for code changes
- Update CONTRIBUTING.md for process changes

### Running Docs Locally

```bash
# No special setup needed - docs are Markdown
# Preview on GitHub or use a Markdown viewer
```

---

## 🤔 Questions?

- Check [README.md](README.md)
- Review [existing issues](https://github.com/cid-kageno-dev/Ani/issues)
- Start a [discussion](https://github.com/cid-kageno-dev/Ani/discussions)
- Email via GitHub profile

---

## 📜 License

By contributing, you agree your code will be licensed under the MIT License.

---

Thank you for contributing! 💜
