# Contributing to Metochina

Thank you for your interest in contributing to Metochina. This document provides guidelines and instructions for contributing to the project.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub by clicking the "Fork" button on the project page.

2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/your-username/metochina.git
   cd metochina
   ```

3. **Install dependencies**:

   ```bash
   python -m pip install Pillow click
   ```

4. **Verify everything works**:

   ```bash
   python -m unittest discover -s tests -v
   ```

---

## Contribution Workflow

We follow a standard fork-and-branch workflow:

### 1. Create a Branch

Create a descriptive branch from `main` for your work:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Use these branch naming conventions:

| Type          | Prefix       | Example                           |
| ------------- | ------------ | --------------------------------- |
| New feature   | `feature/`   | `feature/add-xmp-support`         |
| Bug fix       | `fix/`       | `fix/gps-parsing-negative-coords` |
| Documentation | `docs/`      | `docs/update-install-guide`       |
| Refactor      | `refactor/`  | `refactor/extractor-cleanup`      |
| Tests         | `test/`      | `test/add-analyzer-coverage`      |

### 2. Make Your Changes

- Write clean, well-documented code (see Code Style below).
- Keep commits focused and atomic.
- Write meaningful commit messages.

### 3. Test Your Changes

```bash
python -m unittest discover -s tests -v
```

### 4. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub against the `main` branch.

---

## Code Style

- **Python version**: 3.11+
- **Formatting**: PEP 8, max 99 chars per line
- **Type hints**: Required on all function signatures
- **Docstrings**: Google style on all public APIs

---

## Architecture

Place your code in the appropriate module:

- `metochina/core/` -- Low-level extraction and parsing
- `metochina/analysis/` -- Risk assessment and interpretation
- `metochina/models/` -- Data models
- `metochina/output/` -- Console display and file export
- `metochina/ui/` -- Interactive terminal UI (banners, menus, effects)
- `metochina/cli.py` -- CLI commands

---

## Dependencies

Only **Pillow** and **Click**. Do not add new dependencies without prior discussion.

## Ethical Guidelines

- No features designed to facilitate stalking, harassment, or doxxing.
- No features that transmit data to external services without explicit user consent.
- Privacy-respecting by default.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
