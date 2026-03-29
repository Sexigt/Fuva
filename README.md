# File Upload Validation Analyzer

A comprehensive security testing tool for analyzing file upload validation in web applications. Automatically generates various test files and analyzes how servers handle them, identifying security vulnerabilities and validation gaps.

## Features

### CLI Tool
- **44 File Generators** - Corrupted images, malicious documents, archive bombs, executables, and more
- **Concurrent Testing** - Multi-threaded uploads for faster testing
- **Authentication Support** - Bearer tokens, cookies, custom headers
- **Proxy Support** - Route through Burp, ZAP, or other proxies
- **Proxy Chain** - Chain multiple proxies
- **Retry Logic** - Automatic retries with configurable delays
- **Rate Limiting** - Auto-backoff when rate limited
- **Pattern Matching** - Detects SQL injection, XSS, RCE, XXE, path traversal
- **Server Fingerprinting** - Identifies Apache, nginx, PHP, WordPress, etc.
- **HAR Export** - Export all HTTP traffic for analysis
- **Detailed Reporting** - HTML, JSON, and CSV reports

### Web Interface
- **Dashboard** - View statistics and recent test runs
- **Real-time Progress** - Live progress tracking during tests (SSE)
- **Theme Toggle** - Dark/light mode
- **Profile Comparison** - Compare results between test runs
- **Profile Management** - Save and load test configurations

### Security Detection
- **WAF Detection** - Identifies Cloudflare, AWS WAF, Akamai, Imperva, and more
- **Anomaly Detection** - Flags dangerous files that were accepted
- **API vs UI Validation** - Compares server-side vs client-side validation

### Cross-Platform
- **Windows** - Full support with proper config paths
- **Linux** - Full support with XDG Base Directory
- **macOS** - Full support with Application Support
- **Docker** - Ready-to-use container

## Installation

```bash
# Navigate to project
cd file-upload-validation-analyzer

# Install dependencies
pip install -r requirements.txt

# Or just install requests (minimum requirement)
pip install requests pyyaml
```

## Quick Start

### Web UI (Recommended)

```bash
# Start the web interface
python3 web/main.py

# Open http://localhost:8000 in your browser
```

### CLI

```bash
# Generate test files only
python3 -m cli.main generate -o test_files

# Run upload tests
python3 -m cli.main run https://example.com/upload

# With authentication
python3 -m cli.main run https://example.com/upload --token YOUR_TOKEN

# Through proxy
python3 -m cli.main run https://example.com/upload --proxy http://localhost:8080

# Concurrent testing
python3 -m cli.main run https://example.com/upload --workers 10
```

### Demo Server

```bash
# Start a mock server for testing
python3 -c "from cli.demo_server import start_demo_server; start_demo_server()"

# Vulnerable mode (accepts all files)
python3 -c "from cli.demo_server import start_demo_server; start_demo_server(vulnerable=True)"
```

## Docker

```bash
# Build and run
docker-compose up

# Run just the main app
docker run -p 8000:8000 fuva
```

## Configuration

Configuration file location:
- **Windows**: `%APPDATA%/fuva/config.yaml`
- **Linux**: `~/.config/fuva/config.yaml`
- **macOS**: `~/Library/Application Support/fuva/config.yaml`

Example config.yaml:
```yaml
web:
  host: "0.0.0.0"
  port: 8000
  auth_enabled: false

cli:
  default_timeout: 30
  default_workers: 1
  default_delay: 0

proxy:
  enabled: false
  http: null
  https: null

logging:
  level: INFO
  file_enabled: true
```

## File Generators

The tool includes 44 test file generators in these categories:

### Images
- CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage, EmptyImage, GiantImage

### Documents
- EdgeCasePDF, MalformedSVG, LargePDF, PDFWithJavaScript, RTFWithEmbedded
- PPTMacro, XLSMBom, OfficeOXMLExternalEntity, WordWithEmbeddedHTML

### Archives
- CorruptZIP, ZipSlipArchive, LargeArchive, EmptyArchive, SymlinkArchive, BombZIP
- XZBomb, NestedArchiveBomb, DEFLATEBomb, SevenZipSolidArchive, BZ2Bomb, LZ4Bomb
- WebShellArchive

### Executables
- FakeEXE, FakeELF, MacroEnabledDOCX, MacroEnabledXLSX, ODTFile, GzipBomb, SevenZipArchive, RARArchive

### Mixed/Other
- TextInBinary, DoubleExtensionFile, NullByteInjection, PolyglotFile, HTMLinImage, LongFilename, UnicodeFilenames
- LargeJSONFile, XMLBomb

## Security Notice

⚠️ **Only test servers you own or have explicit written permission to test.** Unauthorized access is illegal.

## License

MIT License - See LICENSE file for details.
