# FUVA - How to Use

## Running Tests

### Web UI (easiest)

```bash
python3 web/main.py
```

Then open http://localhost:8000

### CLI

```bash
# Basic test
python3 -m cli.main run https://example.com/upload

# With auth token
python3 -m cli.main run https://example.com/upload --token "your-token"

# Through proxy
python3 -m cli.main run https://example.com/upload --proxy http://localhost:8080

# Faster (concurrent uploads)
python3 -m cli.main run https://example.com/upload --workers 10
```

### Demo Server

For testing the tool itself:

```bash
# Normal (rejects uploads)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server()"

# Vulnerable mode (accepts everything)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(vulnerable=True)"

# Custom port
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(port=8001)"
```

## Understanding Results

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | File accepted |
| 400 | Validation caught it |
| 403 | Blocked |
| 413 | File too big |
| 415 | Wrong file type |

### What to Look For

**Good results:**
- Dangerous files rejected (400, 403, 415)
- Proper error messages

**Bad results (vulnerabilities):**
- 200 OK for `.exe`, `.php`, `.svg` files
- Files saved with original name (path traversal possible)
- Server errors revealing code/info
- Very slow responses (DoS possible)

### Reports

Generated in `reports/` folder:
- HTML - visual report with charts
- JSON - machine readable
- CSV - for spreadsheets

## Troubleshooting

### Proxy not working

Make sure your proxy is running first. For Burp use port 8080, for ZAP use 8090.

### SSL errors

The tool verifies SSL certificates. For testing with self-signed certs, that's a security risk so not supported.

### Nothing happens after starting test

Check the server URL is correct. Make sure the upload endpoint accepts POST requests.

## Config File

Location:
- Linux: `~/.config/fuva/config.yaml`
- Windows: `%APPDATA%/fuva/config.yaml`

```yaml
web:
  port: 8000

cli:
  default_timeout: 30
  default_workers: 1

proxy:
  http: "http://localhost:8080"
```

## Security

Only test servers you own. Unauthorized access is illegal.
