# File Upload Validation Analyzer - Complete Guide

## Introduction

This tool helps you test how a server handles file uploads. It automatically generates test files with various issues (corrupted files, security problems, etc.) and analyzes how the server responds.

## Quick Start

### Web Interface (Recommended)

```bash
python3 web/main.py
```

Then open http://localhost:8000 in your browser.

### CLI

```bash
# Basic test
python3 -m cli.main run https://example.com/upload

# With authentication
python3 -m cli.main run https://example.com/upload --token "your-token"

# Through proxy
python3 -m cli.main run https://example.com/upload --proxy http://localhost:8080

# Concurrent testing
python3 -m cli.main run https://example.com/upload --workers 10
```

## Demo Server

For testing without a real server:

```bash
# Basic demo server (rejects all uploads)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server()"

# Accept all uploads
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(accept_all=True)"

# Vulnerable mode (accepts malicious files)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(vulnerable=True)"

# With delay simulation
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(delay=1)"
```

## Configuration

### Config File

Create `~/.config/fuva/config.yaml` (Linux) or `%APPDATA%/fuva/config.yaml` (Windows):

```yaml
web:
  host: "0.0.0.0"
  port: 8000
  auth_enabled: false
  # password: "your-password"

cli:
  default_timeout: 30
  default_workers: 1
  default_delay: 0

proxy:
  enabled: false
  http: "http://localhost:8080"
```

## CLI Commands

### Run Tests

```bash
python3 -m cli.main run https://example.com/upload [options]

Options:
  --timeout SECONDS      Request timeout (default: 30)
  --workers NUM          Concurrent workers (default: 1)
  --delay SECONDS        Delay between requests (default: 0)
  --retries NUM          Max retries (default: 0)
  --token TOKEN          Bearer token authentication
  --proxy URL            Proxy URL (e.g., http://localhost:8080)
  --form-field NAME      Form field name (default: file)
  --html                 Generate HTML report
  --json                 Generate JSON report
```

### Generate Files

```bash
python3 -m cli.main generate -o output_dir
```

### Compare Results

```bash
python3 -m cli.main compare run_id1 run_id2
```

## Understanding Results

### Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | File accepted - check if it should be |
| 201 | Created | File accepted and stored |
| 400 | Bad Request | Usually means validation failed |
| 403 | Forbidden | Access denied or blocked |
| 404 | Not Found | Upload endpoint doesn't exist |
| 413 | Too Large | File size rejected |
| 415 | Unsupported | File type rejected |
| 429 | Rate Limited | Too many requests |

### Anomaly Types

- **Security** - Dangerous file accepted (e.g., executable)
- **Performance** - Slow response times
- **Validation** - Missing or weak validation
- **Configuration** - Server misconfiguration

### Severity Levels

- **Critical** - Immediate security risk
- **High** - Significant security issue
- **Medium** - Moderate risk
- **Low** - Minor issue
- **Info** - Informational

## Interpreting Reports

### HTML Report

Open the generated HTML report in a browser to see:
- Summary statistics
- Charts and visualizations
- List of all test files
- Anomalies detected
- Recommendations

### JSON Report

```bash
# View JSON report
cat report_*.json | jq
```

### CSV Report

Export and open in Excel for analysis:
- `/api/report/{id}?format=csv`

## Advanced Features

### Server Fingerprinting

The tool automatically detects:
- Web servers (Apache, nginx, IIS, Cloudflare)
- Frameworks (PHP, ASP.NET, Express, Django, Flask)
- CMS (WordPress, Drupal, Joomla)

### WAF Detection

Identifies:
- Cloudflare
- AWS WAF
- Akamai
- Imperva Incapsula
- F5 BIG-IP
- Sucuri
- ModSecurity

### Rate Limiting

If rate limiting is detected, the tool will:
- Automatically backoff
- Increase delay between requests
- Log warnings

## Docker

```bash
# Build
docker build -t fuva .

# Run
docker run -p 8000:8000 fuva

# Docker Compose
docker-compose up
```

## Troubleshooting

### "Database is locked" on Windows/WSL

The tool now uses in-memory storage by default. If you see lock errors:
1. Delete old database files: `rm -f data/fuva.db*`
2. Restart the server

### Proxy not working

Ensure your proxy is running and you have the correct URL:
```bash
# For Burp
--proxy http://localhost:8080

# For ZAP
--proxy http://localhost:8090
```

### SSL errors

If testing HTTPS sites with certificate issues:
```bash
# Not recommended for production - use only with sites you trust
# The tool uses requests library which verifies SSL by default
```

## Security Warning

⚠️ **Only test servers you own or have written permission to test.**

Unauthorized access to computer systems is illegal.

## Getting Help

- Report issues: https://github.com/Sexigt/fuva/issues
- Documentation: See README.md
