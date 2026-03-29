#!/usr/bin/env python3
"""
File Upload Validation Analyzer - Web Application

A simple HTTP server with a clean, modern UI.
"""

import sys
import json
import os
import uuid
import threading
import signal
import atexit
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.generators import (
    CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage, EmptyImage,
    EdgeCasePDF, MalformedSVG, CorruptZIP, ZipSlipArchive, TextInBinary,
    DoubleExtensionFile, NullByteInjection, PolyglotFile, FakeEXE, FakeELF,
    MacroEnabledDOCX, MacroEnabledXLSX, ODTFile, GzipBomb,
)
from cli.analyzers import ResponseAnalyzer, ValidationComparator, AnomalyDetector
from cli.reporting import HTMLReportGenerator, JSONReportGenerator
from cli.reporting.csv_generator import CSVReportGenerator
from cli.db import db

# Graceful shutdown handler
_shutdown_requested = False

def _cleanup():
    """Cleanup on shutdown."""
    global _shutdown_requested
    if _shutdown_requested:
        return
    _shutdown_requested = True
    print("\n" + "="*50)
    print("Shutting down gracefully...")
    print("="*50)

def _signal_handler(signum, frame):
    """Handle shutdown signals."""
    _cleanup()
    sys.exit(0)

# Register signal handlers (cross-platform)
if hasattr(signal, 'SIGINT'):
    signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, _signal_handler)
atexit.register(_cleanup)


class TestRunner:
    """Background service for running upload tests."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def run_tests(
        self,
        run_id: str,
        target_url: str,
        timeout: int = 30,
        delay: float = 0,
        workers: int = 1,
        max_retries: int = 0,
        form_field: str = "file",
    ):
        config = {
            "timeout": timeout, "delay": delay, "workers": workers,
            "max_retries": max_retries, "form_field": form_field
        }
        db.create_run(run_id, target_url, config)
        db.update_run(run_id, status="running", progress=0, total_tests=0)
        
        try:
            temp_dir = Path("/tmp/fuva")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            generator_classes = [
                CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage,
                EmptyImage, EdgeCasePDF, MalformedSVG, CorruptZIP,
                ZipSlipArchive, TextInBinary, DoubleExtensionFile,
                NullByteInjection, PolyglotFile, FakeEXE, FakeELF,
                MacroEnabledDOCX, MacroEnabledXLSX, ODTFile, GzipBomb,
            ]
            
            test_files = []
            for gen_class in generator_classes:
                with gen_class(output_dir=temp_dir, cleanup=False) as gen:
                    test_files.append(gen.generate())
            
            db.update_run(run_id, total_tests=len(test_files))
            
            def progress_callback(current, total):
                db.update_run(run_id, progress=current)
            
            analyzer = ResponseAnalyzer(
                target_url=target_url,
                timeout=timeout,
                max_retries=max_retries,
                workers=workers,
            )
            analyzer.set_progress_callback(progress_callback)
            
            results = analyzer.run_upload_tests(test_files, delay=delay)
            
            for r in results:
                db.save_result(run_id, {
                    "file_name": r.file.name, "file_category": r.file.category,
                    "mime_type": r.file.mime_type, "status_code": r.status_code,
                    "success": r.success, "response_time": r.response_time,
                    "error_message": r.error, "response_body": r.body,
                    "headers": dict(r.headers) if r.headers else {},
                })
            
            anomaly_detector = AnomalyDetector()
            anomalies = anomaly_detector.detect_anomalies(results)
            
            for a in anomalies:
                db.save_anomaly(run_id, a.to_dict())
            
            comparator = ValidationComparator()
            gaps = comparator.compare_api_ui(results)
            
            html_gen = HTMLReportGenerator("reports")
            html_path = str(html_gen.generate_html_report(
                results=results, gaps=gaps, anomalies=anomalies,
                target_url=target_url, metadata={"timeout": timeout, "workers": workers},
            ))
            
            json_gen = JSONReportGenerator("reports")
            json_path = str(json_gen.generate_json_report(
                results=results, gaps=gaps, anomalies=anomalies,
                target_url=target_url, metadata={"timeout": timeout, "workers": workers},
            ))
            
            db.update_run(
                run_id, status="completed", progress=len(test_files),
                completed_at=datetime.now().isoformat(), total_tests=len(results),
                accepted=sum(1 for r in results if r.success),
                rejected=sum(1 for r in results if not r.success),
                anomalies=len(anomalies), gaps=len(gaps),
                html_report=html_path, json_report=json_path,
            )
        except Exception as e:
            db.update_run(run_id, status="failed", error=str(e))
    
    def get_run(self, run_id):
        return db.get_run(run_id)
    
    def get_all_runs(self):
        return {r["id"]: r for r in db.get_all_runs()}


test_runner = TestRunner()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload Validation Analyzer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --text: #1f2937;
            --text-light: #6b7280;
            --bg: #f9fafb;
            --card-bg: #ffffff;
            --border: #e5e7eb;
        }
        
        [data-theme="dark"] {
            --primary: #818cf8;
            --primary-hover: #6366f1;
            --success: #34d399;
            --warning: #fbbf24;
            --error: #f87171;
            --text: #f3f4f6;
            --text-light: #9ca3af;
            --bg: #111827;
            --card-bg: #1f2937;
            --border: #374151;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        
        .header {
            position: relative;
        }
        
        .theme-toggle {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.1rem;
            transition: background 0.2s;
        }
        
        .theme-toggle:hover {
            background: rgba(255,255,255,0.3);
        }
        
        [data-theme="dark"] .theme-toggle {
            background: rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            opacity: 0.9;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }
        
        .card h2 {
            color: var(--text);
            margin-bottom: 1.25rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--primary);
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .card h2 i { color: var(--primary); }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
        }
        
        .form-group { margin-bottom: 0.75rem; }
        
        .form-group label {
            display: block;
            margin-bottom: 0.375rem;
            color: var(--text-light);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.625rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.9rem;
            transition: border-color 0.2s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.625rem 1.25rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .btn:hover { 
            background: var(--primary-hover); 
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(99,102,241,0.3);
        }
        
        .btn:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
        }
        
        .stat-card {
            background: var(--bg);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .stat-value { 
            font-size: 1.75rem; 
            font-weight: 700; 
            color: var(--primary); 
        }
        
        .stat-label { 
            color: var(--text-light); 
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 1rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--success));
            transition: width 0.3s ease;
        }
        
        table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        
        th, td { 
            padding: 0.875rem; 
            text-align: left; 
            border-bottom: 1px solid var(--border); 
        }
        
        th { 
            color: var(--text-light); 
            font-weight: 500; 
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        tr:hover { background: var(--bg); }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.625rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-error { background: #fee2e2; color: #991b1b; }
        .badge-info { background: #e0e7ff; color: #3730a3; }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-light);
        }
        
        .empty-state i { 
            font-size: 2.5rem; 
            margin-bottom: 0.75rem; 
            opacity: 0.4; 
            color: var(--primary);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .running { animation: pulse 1.5s infinite; }
        
        .help-text {
            font-size: 0.8rem;
            color: var(--text-light);
            margin-top: 1rem;
            padding: 0.75rem;
            background: #eff6ff;
            border-radius: 6px;
            border-left: 3px solid var(--primary);
        }
        
        .nav {
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 0.75rem 2rem;
            display: flex;
            gap: 1.5rem;
        }
        
        .nav a {
            color: var(--text-light);
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 0;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }
        
        .nav a:hover, .nav a.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .section {
            display: none;
        }
        .section.active {
            display: block;
        }
        
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.85rem;
            margin: 0.5rem 0;
        }
        
        .code-block .comment { color: #64748b; }
        .code-block .keyword { color: #c084fc; }
        .code-block .string { color: #86efac; }
        
        .status-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.5rem 0;
        }
        
        .status-table th, .status-table td {
            padding: 0.5rem;
            border: 1px solid var(--border);
            font-size: 0.85rem;
        }
        
        .status-table th { background: var(--bg); }
        
        .status-2xx { background: #d1fae5; color: #065f46; }
        .status-3xx { background: #dbeafe; color: #1e40af; }
        .status-4xx { background: #fef3c7; color: #92400e; }
        .status-5xx { background: #fee2e2; color: #991b1b; }
        
        .checklist {
            list-style: none;
            padding: 0;
        }
        
        .checklist li {
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .checklist input[type="checkbox"] {
            width: auto;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .alert-warning {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }
        
        .alert-danger {
            background: #fee2e2;
            border-left: 4px solid #ef4444;
        }
        
        .alert-success {
            background: #d1fae5;
            border-left: 4px solid #10b981;
        }
        
        .alert-info {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/" class="active" id="nav-dashboard">Dashboard</a>
        <a href="/guide.html" id="nav-guide">How to Use</a>
        <a href="/interpret.html" id="nav-interpret">Interpretation</a>
    </div>
    
    <div class="section active" id="section-dashboard">
    <div class="header">
        <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme"><i class="fas fa-moon"></i></button>
        <h1><i class="fas fa-shield-alt"></i> File Upload Validation Analyzer</h1>
        <p>Test and analyze file upload security on any web server</p>
    </div>
    
    <div class="container">
        <div class="card">
            <h2><i class="fas fa-rocket"></i> Run New Test</h2>
            <form id="runForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Target Upload URL *</label>
                        <input type="url" id="target_url" placeholder="https://example.com/upload" required>
                    </div>
                    <div class="form-group">
                        <label>Timeout (seconds)</label>
                        <input type="number" id="timeout" value="30" min="1" max="300">
                    </div>
                    <div class="form-group">
                        <label>Workers</label>
                        <input type="number" id="workers" value="1" min="1" max="20">
                    </div>
                    <div class="form-group">
                        <label>Max Retries</label>
                        <input type="number" id="max_retries" value="0" min="0" max="10">
                    </div>
                    <div class="form-group">
                        <label>Form Field</label>
                        <input type="text" id="form_field" value="file">
                    </div>
                </div>
                <button type="submit" class="btn" id="submitBtn">
                    <i class="fas fa-play"></i> Start Test
                </button>
                <div class="progress-bar" id="progressBar" style="display:none;">
                    <div class="progress-fill" id="progressFill" style="width:0%"></div>
                </div>
            </form>
            <div class="help-text">
                <i class="fas fa-info-circle"></i> 
                The tool will generate 31 test files including corrupted images, malicious documents, 
                archive bombs, and more to test how the server handles different types of uploads.
                <br><br>
                <a href="#guide" onclick="showSection('guide'); return false;" style="color: var(--primary);">
                    <i class="fas fa-book"></i> View How to Use Guide
                </a>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-chart-bar"></i> Statistics</h2>
            <div class="stats-grid" id="stats">
                <div class="stat-card"><div class="stat-value">0</div><div class="stat-label">Total Runs</div></div>
                <div class="stat-card"><div class="stat-value">0</div><div class="stat-label">Completed</div></div>
                <div class="stat-card"><div class="stat-value">0</div><div class="stat-label">Tests Run</div></div>
                <div class="stat-card"><div class="stat-value">0</div><div class="stat-label">Anomalies</div></div>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-history"></i> Recent Runs</h2>
            <div style="margin-bottom: 1rem;">
                <button class="btn btn-secondary" onclick="compareSelectedRuns()" id="compareBtn" style="display:none;">
                    <i class="fas fa-balance-scale"></i> Compare Selected
                </button>
            </div>
            <div id="runsList">
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>No tests yet. Start a test above!</p>
                </div>
            </div>
            <div id="comparisonResult" style="margin-top: 1rem; display: none;">
                <div class="card" style="background: var(--bg);">
                    <h3><i class="fas fa-balance-scale"></i> Comparison Result</h3>
                    <pre id="comparisonContent" style="white-space: pre-wrap; font-size: 0.9rem;"></pre>
                </div>
            </div>
        </div>
    </div>
    
    <!-- GUIDE SECTION -->
    <div class="section" id="section-guide">
        <div class="header">
            <h1><i class="fas fa-book"></i> How to Use & Interpret Results</h1>
            <p>A complete guide to testing file upload security</p>
        </div>
        
        <div class="container">
            <div class="card">
                <h2><i class="fas fa-play-circle"></i> Getting Started</h2>
                <p>This tool helps you identify security vulnerabilities in file upload functionality. It generates 31 different test files including:</p>
                <ul style="margin: 1rem 0 1rem 1.5rem; line-height: 1.8;">
                    <li><strong>Corrupted images</strong> - Files with broken headers or wrong MIME types</li>
                    <li><strong>Malicious documents</strong> - PDFs with embedded scripts, SVG with XSS</li>
                    <li><strong>Archive bombs</strong> - Highly compressed files designed to exhaust resources</li>
                    <li><strong>Path traversal</strong> - Files designed to escape upload directories</li>
                    <li><strong>Double extensions</strong> - files.txt.exe that bypass simple filters</li>
                </ul>
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i> <strong>Legal Notice:</strong> Only test servers you own or have explicit written permission to test. Unauthorized access is illegal.
                </div>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-code"></i> Using the CLI</h2>
                <p>For more advanced testing, use the command line interface:</p>
                <div class="code-block">
# Basic test
python3 -m cli.main run https://example.com/upload

# With authentication
python3 -m cli.main run https://example.com/upload --token "your-token"

# Through proxy (Burp/ZAP)
python3 -m cli.main run https://example.com/upload --proxy http://localhost:8080

# Concurrent testing (faster)
python3 -m cli.main run https://example.com/upload --workers 10
                </div>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-check-circle"></i> Understanding Status Codes</h2>
                <p>When you upload a file, the server responds with an HTTP status code. Here's what they mean:</p>
                
                <h3 style="margin: 1rem 0 0.5rem;">Success (2xx) - Usually Good</h3>
                <table class="status-table">
                    <tr><th>Code</th><th>Meaning</th><th>Security Note</th></tr>
                    <tr><td class="status-2xx">200 OK</td><td>File accepted</td><td>Check if it's safe to accept this file type</td></tr>
                    <tr><td class="status-2xx">201 Created</td><td>File saved</td><td>Verify the file type is allowed</td></tr>
                    <tr><td class="status-2xx">415 Unsupported</td><td>Wrong file type</td><td><strong>Good!</strong> Server validates MIME type</td></tr>
                </table>
                
                <h3 style="margin: 1rem 0 0.5rem;">Client Errors (4xx) - Often Good</h3>
                <table class="status-table">
                    <tr><th>Code</th><th>Meaning</th><th>Security Note</th></tr>
                    <tr><td class="status-4xx">400 Bad Request</td><td>Server didn't understand</td><td>May indicate missing validation</td></tr>
                    <tr><td class="status-4xx">403 Forbidden</td><td>Access denied</td><td><strong>Good!</strong> Server blocked the file</td></tr>
                    <tr><td class="status-4xx">413 Payload Too Large</td><td>File too big</td><td><strong>Good!</strong> Server validates size</td></tr>
                </table>
                
                <h3 style="margin: 1rem 0 0.5rem;">Server Errors (5xx) - Usually Bad</h3>
                <table class="status-table">
                    <tr><th>Code</th><th>Meaning</th><th>Security Note</th></tr>
                    <tr><td class="status-5xx">500 Internal Error</td><td>Server crashed</td><td><strong>Danger!</strong> File causes crash - potential exploit</td></tr>
                    <tr><td class="status-5xx">502 Bad Gateway</td><td>Server error</td><td>May indicate processing issues</td></tr>
                </table>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-exclamation-triangle"></i> What to Look For</h2>
                
                <h3 style="margin: 1rem 0 0.5rem;">High Acceptance Rate</h3>
                <div class="alert alert-warning">
                    If the server accepts more than 50% of test files, it likely lacks proper validation.
                </div>
                
                <h3 style="margin: 1rem 0 0.5rem;">Server Crashes (5xx)</h3>
                <div class="alert alert-danger">
                    <strong>Critical!</strong> If any file causes a 500 error, the server may be vulnerable to denial of service or code execution attacks.
                </div>
                
                <h3 style="margin: 1rem 0 0.5rem;">Error Messages in Response</h3>
                <div class="alert alert-warning">
                    If the response contains "SQL syntax", "Stack trace", or internal paths, the server may be leaking sensitive information.
                </div>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-clipboard-check"></i> Security Checklist</h2>
                <p>Use this checklist when reviewing file upload functionality:</p>
                <ul class="checklist">
                    <li><input type="checkbox"> Server only accepts documented/expected file types</li>
                    <li><input type="checkbox"> MIME type is validated on server-side (not just client-side)</li>
                    <li><input type="checkbox"> File content is inspected, not just extension</li>
                    <li><input type="checkbox"> Maximum file size is enforced</li>
                    <li><input type="checkbox"> Corrupted/malformed files are rejected</li>
                    <li><input type="checkbox"> Path traversal (../) in filenames is blocked</li>
                    <li><input type="checkbox"> Double extensions (file.txt.exe) are blocked</li>
                    <li><input type="checkbox"> Null byte injection is handled</li>
                    <li><input type="checkbox"> ZIP archives are validated for path traversal</li>
                    <li><input type="checkbox"> Files with scripts (SVG, PDF with JS) are blocked</li>
                    <li><input type="checkbox"> Upload attempts are logged for security monitoring</li>
                    <li><input type="checkbox"> Internal error messages are not exposed to users</li>
                </ul>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-lightbulb"></i> Interpreting Results</h2>
                
                <h3 style="margin: 1rem 0 0.5rem;">Good Results</h3>
                <div class="alert alert-success">
                    <ul style="margin: 0.5rem 0 0 1rem;">
                        <li>Most files get 403, 415, or 413 responses</li>
                        <li>No 500 errors (server doesn't crash)</li>
                        <li>Clean error messages without internal details</li>
                        <li>Only expected file types are accepted</li>
                    </ul>
                </div>
                
                <h3 style="margin: 1rem 0 0.5rem;">Bad Results</h3>
                <div class="alert alert-danger">
                    <ul style="margin: 0.5rem 0 0 1rem;">
                        <li>Server accepts 200+ for most test files</li>
                        <li>Any 500 errors on test files</li>
                        <li>SQL injection or stack traces in responses</li>
                        <li>Files saved with original names (path traversal possible)</li>
                        <li>No file type validation visible</li>
                    </ul>
                </div>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-file-alt"></i> Understanding Reports</h2>
                <p>After a test completes, you can view detailed reports:</p>
                <ul style="margin: 1rem 0 0 1.5rem; line-height: 1.8;">
                    <li><strong>HTML Report</strong> - Visual charts and tables showing all test results</li>
                    <li><strong>JSON Report</strong> - Machine-readable format for automation</li>
                    <li><strong>Anomalies</strong> - Security issues detected during testing</li>
                    <li><strong>Validation Gaps</strong> - Differences between expected and actual behavior</li>
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        function showSection(name) {
            document.querySelectorAll('.section').forEach(function(s) { s.classList.remove('active'); });
            document.querySelectorAll('.nav a').forEach(function(a) { a.classList.remove('active'); });
            document.getElementById('section-' + name).classList.add('active');
            document.getElementById('nav-' + name).classList.add('active');
        }
        
        function toggleTheme() {
            var html = document.documentElement;
            var current = html.getAttribute('data-theme');
            var btn = document.querySelector('.theme-toggle i');
            if (current === 'dark') {
                html.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                btn.className = 'fas fa-moon';
            } else {
                html.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                btn.className = 'fas fa-sun';
            }
        }
        
        function initTheme() {
            var saved = localStorage.getItem('theme');
            if (saved === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.querySelector('.theme-toggle i').className = 'fas fa-sun';
            }
        }
        
        // Check URL hash on load
        window.onload = function() {
            initTheme();
            var hash = window.location.hash;
            if (hash === '#guide') {
                showSection('guide');
            }
        };
        
        var currentRunId = null;
        
        function updateCompareButton() {
            var checkboxes = document.querySelectorAll('.run-checkbox:checked');
            var btn = document.getElementById('compareBtn');
            btn.style.display = checkboxes.length >= 2 ? 'inline-block' : 'none';
        }
        
        async function compareSelectedRuns() {
            var checkboxes = document.querySelectorAll('.run-checkbox:checked');
            if (checkboxes.length < 2) return;
            
            var runId1 = checkboxes[0].value;
            var runId2 = checkboxes[1].value;
            
            try {
                var resp = await fetch('/api/compare/' + runId1 + '/' + runId2);
                if (resp.ok) {
                    var data = await resp.json();
                    var div = document.getElementById('comparisonResult');
                    var content = document.getElementById('comparisonContent');
                    var diff = data.differences;
                    content.textContent = JSON.stringify(diff, null, 2);
                    div.style.display = 'block';
                } else {
                    alert('Could not compare runs');
                }
            } catch (e) {
                alert('Error comparing runs: ' + e.message);
            }
        }
        
        async function refreshData() {
            try {
                var resp = await fetch('/api/stats');
                var stats = await resp.json();
                document.getElementById('stats').innerHTML = 
                    '<div class="stat-card"><div class="stat-value">' + (stats.total_runs || 0) + '</div><div class="stat-label">Total Runs</div></div>' +
                    '<div class="stat-card"><div class="stat-value">' + (stats.completed_runs || 0) + '</div><div class="stat-label">Completed</div></div>' +
                    '<div class="stat-card"><div class="stat-value">' + (stats.total_tests || 0) + '</div><div class="stat-label">Tests Run</div></div>' +
                    '<div class="stat-card"><div class="stat-value">' + (stats.total_anomalies || 0) + '</div><div class="stat-label">Anomalies</div></div>';
                
                var runsResp = await fetch('/api/runs');
                var runs = await runsResp.json();
                var container = document.getElementById('runsList');
                
                if (runs.length === 0) {
                    container.innerHTML = '<div class="empty-state"><i class="fas fa-folder-open"></i><p>No tests yet. Start a test above!</p></div>';
                    return;
                }
                
                var html = '<table><thead><tr><th></th><th>ID</th><th>Target</th><th>Status</th><th>Progress</th><th>Tests</th><th>Accepted</th><th>Anomalies</th><th>Report</th></tr></thead><tbody>';
                
                for (var i = 0; i < runs.length; i++) {
                    var run = runs[i];
                    var statusClass = run.status === 'completed' ? 'badge-success' : run.status === 'running' ? 'badge-warning running' : 'badge-error';
                    var progress = run.total > 0 ? Math.round((run.progress / run.total) * 100) : 0;
                    var progressHtml = run.status === 'running' ? 
                        '<div class="progress-bar" style="width:80px;height:4px;"><div class="progress-fill" style="width:' + progress + '%"></div></div>' :
                        progress + '%';
                    
                    html += '<tr>' +
                        '<td><input type="checkbox" class="run-checkbox" value="' + run.id + '" onchange="updateCompareButton()"></td>' +
                        '<td>' + run.id + '</td>' +
                        '<td>' + (run.target_url ? run.target_url.substring(0, 25) + '...' : '-') + '</td>' +
                        '<td><span class="badge ' + statusClass + '">' + run.status + '</span></td>' +
                        '<td>' + progressHtml + '</td>' +
                        '<td>' + (run.total_tests || 0) + '</td>' +
                        '<td style="color:var(--success)">' + (run.accepted || 0) + '</td>' +
                        '<td style="color:var(--warning)">' + (run.anomalies || 0) + '</td>' +
                        '<td>' + (run.status === 'completed' && run.html_report ? '<a href="/api/report/' + run.id + '" target="_blank" class="badge badge-info" style="text-decoration:none;">View</a>' : '-') + '</td>' +
                        '</tr>';
                }
                
                html += '</tbody></table>';
                container.innerHTML = html;
                
                if (currentRunId) {
                    var currentRun = null;
                    for (var j = 0; j < runs.length; j++) {
                        if (runs[j].id === currentRunId) {
                            currentRun = runs[j];
                            break;
                        }
                    }
                    if (currentRun && currentRun.status === 'running') {
                        var progress = currentRun.total > 0 ? Math.round((currentRun.progress / currentRun.total) * 100) : 0;
                        document.getElementById('progressFill').style.width = progress + '%';
                        document.getElementById('progressBar').style.display = 'block';
                        document.getElementById('submitBtn').disabled = true;
                    } else if (currentRun && currentRun.status === 'completed') {
                        document.getElementById('progressBar').style.display = 'none';
                        document.getElementById('submitBtn').disabled = false;
                        currentRunId = null;
                    }
                }
            } catch(e) {
                console.error(e);
            }
        }
        
        document.getElementById('runForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            var target_url = document.getElementById('target_url').value;
            var timeout = parseInt(document.getElementById('timeout').value);
            var workers = parseInt(document.getElementById('workers').value);
            var max_retries = parseInt(document.getElementById('max_retries').value);
            var form_field = document.getElementById('form_field').value;
            
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('progressBar').style.display = 'block';
            document.getElementById('progressFill').style.width = '0%';
            
            try {
                var resp = await fetch('/api/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({target_url: target_url, timeout: timeout, workers: workers, max_retries: max_retries, form_field: form_field})
                });
                var data = await resp.json();
                currentRunId = data.run_id;
            } catch(e) {
                console.error(e);
                document.getElementById('submitBtn').disabled = false;
            }
        });
        
        setInterval(refreshData, 3000);
        refreshData();
    </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        
        elif parsed.path == '/api/stats':
            runs = test_runner.get_all_runs()
            total = len(runs)
            completed = sum(1 for r in runs.values() if r.get("status") == "completed")
            tests = sum(r.get("total_tests", 0) for r in runs.values())
            anomalies = sum(r.get("anomalies", 0) for r in runs.values())
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "total_runs": total,
                "completed_runs": completed,
                "total_tests": tests,
                "total_anomalies": anomalies,
            }).encode())
        
        elif parsed.path == '/api/runs':
            runs = test_runner.get_all_runs()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(list(runs.values())).encode())
        
        elif parsed.path.startswith('/api/compare/'):
            parts = parsed.path.split('/')
            if len(parts) >= 4:
                run_id1 = parts[2]
                run_id2 = parts[3]
                run1 = test_runner.get_run(run_id1)
                run2 = test_runner.get_run(run_id2)
                if run1 and run2:
                    comparison = {
                        "run1": run1,
                        "run2": run2,
                        "differences": {
                            "total_tests": run1.get("total_tests", 0) - run2.get("total_tests", 0),
                            "accepted": run1.get("accepted", 0) - run2.get("accepted", 0),
                            "rejected": run1.get("rejected", 0) - run2.get("rejected", 0),
                            "anomalies": run1.get("anomalies", 0) - run2.get("anomalies", 0),
                        }
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(comparison).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
        
        elif parsed.path.startswith('/api/progress/'):
            run_id = parsed.path.split('/').pop()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            last_progress = -1
            import time
            for _ in range(300):
                run = test_runner.get_run(run_id)
                if run:
                    progress = run.get("progress", 0)
                    if progress != last_progress:
                        data = json.dumps({
                            "progress": progress,
                            "total": run.get("total_tests", 0),
                            "status": run.get("status", "running"),
                        })
                        self.wfile.write(f"data: {data}\n\n".encode())
                        last_progress = progress
                    if run.get("status") in ("completed", "failed"):
                        break
                time.sleep(0.5)
        
        elif parsed.path.startswith('/api/report/'):
            run_id = parsed.path.split('/').pop()
            query = parsed.query
            fmt = 'csv' if 'format=csv' in query else 'html'
            run = test_runner.get_run(run_id)
            if run and run.get("html_report"):
                if fmt == 'csv' and run.get("json_report"):
                    json_path = run.get("json_report")
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    csv_gen = CSVReportGenerator("reports")
                    results = data.get("results", [])
                    anomalies = data.get("anomalies", [])
                    csv_path = csv_gen.generate_csv_report(results, anomalies, run.get("target_url", ""))
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/csv')
                    self.send_header('Content-Disposition', f'attachment; filename="report_{run_id}.csv"')
                    self.end_headers()
                    with open(csv_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    try:
                        with open(run["html_report"], 'rb') as f:
                            self.wfile.write(f.read())
                    except:
                        self.wfile.write(b"Report not found")
            else:
                self.send_response(404)
                self.end_headers()
        
        elif parsed.path == '/api/profiles':
            profiles = db.get_all_profiles()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(profiles).encode())
        
        elif parsed.path.startswith('/api/profile/'):
            name = parsed.path.split('/').pop()
            if self.command == 'DELETE':
                db.delete_profile(name)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"deleted": True}).encode())
            else:
                profile = db.get_profile(name)
                if profile:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(profile).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        elif parsed.path == '/guide.html':
            guide_path = Path(__file__).parent / 'guide.html'
            if guide_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(guide_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        
        elif parsed.path == '/interpret.html':
            interpret_path = Path(__file__).parent / 'interpret.html'
            if interpret_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(interpret_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/run':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            run_id = str(uuid.uuid4())[:8]
            thread = threading.Thread(target=test_runner.run_tests, args=(
                run_id,
                data.get("target_url"),
                data.get("timeout", 30),
                data.get("delay", 0),
                data.get("workers", 1),
                data.get("max_retries", 0),
                data.get("form_field", "file"),
            ))
            thread.start()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "run_id": run_id,
                "status": "pending",
                "message": "Test run " + run_id + " started"
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def main():
    port = int(os.getenv("PORT", "8000"))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print("=" * 55)
    print("  File Upload Validation Analyzer")
    print("  Web Interface v0.2.0")
    print("=" * 55)
    print("Server running on http://localhost:" + str(port))
    print("Open in your browser to start testing!")
    print("=" * 55)
    server.serve_forever()


if __name__ == "__main__":
    main()
