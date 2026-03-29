# Contributing to File Upload Validation Analyzer

Thank you for your interest in contributing!

## Development Setup

### Prerequisites
- Python 3.12+
- pip

### Clone and Install

```bash
git clone https://github.com/Sexigt/fuva.git
cd fuva
pip install -r requirements.txt
```

### Running the Application

**Web UI:**
```bash
python3 web/main.py
```

**CLI:**
```bash
python3 -m cli.main run https://example.com/upload
```

**Demo Server:**
```bash
python3 -c "from cli.demo_server import start_demo_server; start_demo_server()"
```

### Running Tests

```bash
# Add tests when available
pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to new functions
- Keep functions focused and small

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run linting/type checking
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Reporting Issues

Please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
