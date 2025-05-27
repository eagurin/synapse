# Contributing to Synapse

Thank you for your interest in contributing to Synapse! 

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/synapse.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Run tests: `make test`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
make format

# Run linter
make lint
```

## Code Style

- Use Black for formatting
- Follow PEP 8
- Add type hints where possible
- Write docstrings for all functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## Pull Request Process

1. Update README.md with details of changes if needed
2. Update the docs with any new functionality
3. The PR will be merged once you have approval

## Questions?

Feel free to open an issue or join our Discord!