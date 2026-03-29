# FUVA - File Upload Validation Analyzer

Security testing tool for file upload endpoints. Finds vulnerabilities like:

- Extension bypass (file.php.jpg, file.jpg.php)
- Content-Type spoofing
- Polyglot files (valid image + malicious payload)
- Archive bombs (compressed files that expand huge)
- Path traversal (../ etc in filenames)
- Files with double extensions
- Executables disguised as images
- Documents with embedded scripts/macros
- XXE and deserialization attacks

Works with CLI or Web UI.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Start Web UI
python3 web/main.py

# Or use CLI
python3 -m cli.main run https://yoursite.com/upload
```

Open http://localhost:8000 for the web interface.

## What Gets Tested

| Category | Examples |
|----------|----------|
| Images | corrupt headers, wrong MIME, large metadata, empty files |
| Documents | malformed PDF, SVG with XSS, macros in Office |
| Archives | zip slip, symlinks, nested bombs, web shells |
| Executables | fake extensions, double extensions, ELF/PE |
| Mixed | polyglots, null bytes, path traversal |

## CLI Examples

```bash
# Basic test
python3 -m cli.main run https://example.com/upload

# With authentication
python3 -m cli.main run https://example.com/upload --token "your-token"

# Through proxy (Burp, ZAP, etc)
python3 -m cli.main run https://example.com/upload --proxy http://localhost:8080

# Faster with multiple workers
python3 -m cli.main run https://example.com/upload --workers 10
```

## Demo Server

Want to test without a real server?

```bash
# Accepts everything (vulnerable mode)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(vulnerable=True)"
```

## Web UI Features

- Dashboard with test history
- Real-time progress
- Dark/light theme
- Compare test results
- Export to HTML, JSON, CSV

## Docker

```bash
docker-compose up
```

## Config

Config file location:
- Linux: `~/.config/fuva/config.yaml`
- Windows: `%APPDATA%/fuva/config.yaml`
- Mac: `~/Library/Application Support/fuva/config.yaml`

Example:

```yaml
web:
  port: 8000
cli:
  default_timeout: 30
proxy:
  http: "http://localhost:8080"
```

## Requirements

- Python 3.12+
- requests
- pyyaml

## Warning

Only test servers you own or have permission to test. Unauthorized access is illegal.

## License

MIT
