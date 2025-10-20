# Contributing to Claude Agent Eval Starter

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/kasperjanehag/claude-langfuse-example-project.git
cd claude-langfuse-example-project
```

2. **Create a virtual environment and install dependencies**

```bash
# Using uv (recommended - fast!)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or use make
make dev
```

3. **Install pre-commit hooks**

```bash
uv run pre-commit install
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/unit/test_models.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Or run individually with uv
uv run black src/ tests/ examples/
uv run ruff check src/ tests/ examples/
uv run mypy src/
```

### Testing Changes Locally

```bash
# Start Langfuse
make docker-up

# Run agent demo
make agent

# Run evaluations
make eval

# Interactive testing
make interactive
```

## Contribution Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use descriptive variable names

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Include both unit and integration tests where appropriate
- Test edge cases and error conditions

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Include examples for new features
- Update the CHANGELOG.md

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for custom evaluation metrics
fix: Handle empty knowledge base gracefully
docs: Update installation instructions
test: Add tests for answer relevance metric
refactor: Simplify evaluation result parsing
```

Prefixes:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `style:` Code style changes (formatting, etc.)
- `chore:` Maintenance tasks

### Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feat/your-feature-name
```

2. **Make your changes**
   - Write code following the style guidelines
   - Add tests
   - Update documentation

3. **Commit your changes**

```bash
git add .
git commit -m "feat: description of your changes"
```

4. **Push to your fork**

```bash
git push origin feat/your-feature-name
```

5. **Create a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Describe what you changed and why
   - Include screenshots for UI changes

6. **Code Review**
   - Address reviewer feedback
   - Make requested changes
   - Push updates to your branch

7. **Merge**
   - Once approved, your PR will be merged
   - Delete your feature branch

## Areas for Contribution

We welcome contributions in these areas:

### New Features
- Additional evaluation metrics
- More agent examples (code generation, data analysis, etc.)
- Integration with vector databases
- Multi-turn conversation support
- Batch evaluation support
- A/B testing framework

### Improvements
- Performance optimizations
- Better error handling
- Enhanced logging
- Improved documentation
- More comprehensive tests

### Examples
- Different use cases (code review, content generation, etc.)
- Integration examples (FastAPI, Flask, etc.)
- Production deployment guides
- CI/CD pipeline examples

### Bug Fixes
- Fix reported issues
- Improve error messages
- Handle edge cases

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Open a new issue with the "question" label
3. Reach out to the maintainers

## Code of Conduct

Please be respectful and constructive in all interactions. We're building this together!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
