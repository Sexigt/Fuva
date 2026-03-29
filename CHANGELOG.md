# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cross-platform support (Windows, Linux, macOS)
- Graceful shutdown handling
- In-memory database with optional JSON persistence
- Configuration file support (YAML/JSON)
- HAR export for HTTP traffic capture
- Server fingerprint detection
- Demo/Mock server for testing
- Docker and docker-compose support
- Systemd service configuration

### Changed
- 44 total test file generators
- Enhanced WAF detection (8 WAF types)
- Rate limiting with auto-backoff
- Dark/Light theme toggle
- Profile comparison view

### Fixed
- Database locking issues on Windows/WSL
- Import errors in generators

## [1.0.0] - 2024-03-29

### Added
- Initial MVP release
- CLI with 31 test file generators
- Web UI with dashboard
- HTML and JSON report generation
- Anomaly detection
- API vs UI validation comparison

[Unreleased]: https://github.com/Sexigt/fuva/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Sexigt/fuva/releases/tag/v1.0.0
