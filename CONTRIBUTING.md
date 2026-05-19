# Contributing to Ani

Thank you for your interest in contributing! This guide covers everything you need to get started — from setting up a development environment to submitting a pull request.

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Ani.git
   cd Ani
   ```

2. **Install dependencies**

   On Replit, dependencies are already installed automatically. Locally:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

   > Virtual environments are optional — Replit manages its own Python environment, and local venvs are supported but not required.

3. **Set up environment variables**

   Copy the example file and fill in your credentials:
   ```bash
   cp .env.example .env
   # Add GOOGLE_API_KEY1 and Firebase credentials to .env
   ```

   On Replit, add secrets via the Secrets tab instead.

4. **Run the app**
   ```bash
   python run.py
   # Opens on http://localhost:5000
   ```

---

## Development Workflow

### 1. Create a branch

```bash
git checkout main && git pull origin main
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/short-description
```

### 2. Make changes

- Keep commits focused and logical.
- Follow the coding style guide below.
- Update docs if your change affects API behaviour or configuration.

### 3. Test your changes

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_api_endpoints.py -v

# Unit tests only
pytest -m "not integration"
```

### 4. Code quality checks

```bash
# Format with Black
black .

# Lint with Flake8
flake8 . --max-line-length=120

# Type check with mypy
mypy app --ignore-missing-imports

# Security scan with Bandit
bandit -r app
```

### 5. Commit and push

```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### 6. Open a pull request

- Go to https://github.com/cid-kageno-dev/Ani and click **New Pull Request**.
- Select your branch and fill in the PR template.

---

## Coding Style

### Python (PEP 8 + Black)

```python
# Good
def get_recent_interactions(limit: int = 20) -> list:
    """Fetch recent chat interactions from the database.

    Args:
        limit: Maximum number of interactions to return (1–100).

    Returns:
        List of interaction dicts ordered newest-first.
    """
    ...

# Bad
def get_interactions(n):
    pass
```

### Naming conventions

| Style | Used for |
|-------|----------|
| `snake_case` | Functions, variables, module names |
| `PascalCase` | Classes |
| `UPPER_SNAKE_CASE` | Module-level constants |
| `_underscore_prefix` | Private/internal functions |

### Type hints

Use them on all public functions:

```python
def save_interaction(user_query: str, ai_response: str, source: str = "AI Response") -> None:
    ...
```

### Docstrings

Use Google-style docstrings for public functions and classes.

---

## Testing Guidelines

### Structure

Tests live in `tests/`. Use `pytest` markers to categorise them:

```python
@pytest.mark.unit
def test_config_loading():
    ...

@pytest.mark.integration
def test_firebase_roundtrip():
    ...
```

### Coverage target

- Minimum 70% coverage for a PR to pass CI.
- Target 80%+ for new code.

### Example test

```python
from app import create_app

def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_chat_rejects_empty_message():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 400
```

---

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

<optional body>

<optional footer>
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Formatting only (no logic change) |
| `refactor` | Code restructuring without behaviour change |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `ci` | CI/CD pipeline changes |
| `chore` | Dependency bumps, config, tooling |

### Examples

```
feat(ai): add support for Gemini 2.0 Flash
fix(db): handle None created_at in Firebase interactions
docs(api): correct /api/chat response shape
test(routes): add integration test for /api/stats
```

---

## Pull Request Template

```markdown
## What does this PR do?
Brief description of the change.

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation / tests only

## Related issues
Closes #(issue number)

## Testing done
Describe what you tested and how.

## Checklist
- [ ] Tests added or updated
- [ ] Documentation updated (README, API.md, etc.)
- [ ] Code follows style guide
- [ ] No breaking changes (or noted above)
```

---

## Bug Reports

Use GitHub Issues and include:

1. Steps to reproduce
2. Expected vs. actual behaviour
3. Python version and OS
4. Relevant log output or error message

---

## Feature Requests

Use GitHub Issues and include:

1. What problem does this solve?
2. Proposed approach (if any)
3. Any concerns or trade-offs

---

## Code Review Process

1. CI runs automatically (tests, linting, coverage, security scan).
2. A maintainer reviews the code, design, and documentation.
3. Address any feedback and re-request review.
4. On approval, changes are merged using squash-merge.

---

## Questions?

- Read [README.md](README.md) and [docs/API.md](docs/API.md)
- Open a [GitHub Discussion](https://github.com/cid-kageno-dev/Ani/discussions)
- Browse [existing issues](https://github.com/cid-kageno-dev/Ani/issues)

---

By contributing, you agree your code will be licensed under the MIT License.

Thank you for contributing!
