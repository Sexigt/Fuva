"""Mock server for testing and demo mode."""

import http.server
import socketserver
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class MockUploadHandler(http.server.BaseHTTPRequestHandler):
    """Handler that simulates various file upload scenarios."""
    
    # Configuration for the mock server behavior
    config = {
        "accept_all": False,
        "reject_patterns": [],
        "vulnerable": False,
        "delay": 0,
        "status_code": 200,
        "error_message": "",
        "store_uploads": True,
        "upload_dir": "/tmp/fuva_uploads",
    }
    
    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[MockServer] {args[0]}")
    
    def do_POST(self):
        """Handle file upload POST requests."""
        import time
        time.sleep(self.config.get("delay", 0))
        
        content_type = self.headers.get("Content-Type", "")
        
        if "multipart/form-data" not in content_type:
            self.send_error(400, "Expected multipart/form-data")
            return
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        # Store uploaded file if enabled
        if self.config.get("store_uploads", True):
            upload_dir = Path(self.config.get("upload_dir", "/tmp/fuva_uploads"))
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract filename from multipart
            filename = "uploaded_file"
            if b"filename=" in body:
                start = body.find(b"filename=") + 10
                end = body.find(b'"', start)
                if end > start:
                    filename = body[start:end].decode('utf-8', errors='ignore')
            
            filepath = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath.write_bytes(body)
        
        # Check rejection patterns
        for pattern in self.config.get("reject_patterns", []):
            if pattern.lower() in body.decode('utf-8', errors='ignore').lower():
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File rejected", "pattern": pattern}).encode())
                return
        
        # Determine response based on config
        if self.config.get("accept_all", False):
            status = 200
            response = {"success": True, "message": "File uploaded successfully", "size": content_length}
        elif self.config.get("vulnerable", False):
            status = 200
            response = {"success": True, "message": "File uploaded (VULNERABLE MODE)", "size": content_length}
            # Simulate vulnerability by including file content in response
            response["file_content_preview"] = body[:200].decode('utf-8', errors='ignore')
        else:
            status = self.config.get("status_code", 400)
            response = {"success": False, "message": self.config.get("error_message", "Upload rejected")}
        
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Mock-Server", "fuva-demo")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_GET(self):
        """Handle GET requests."""
        path = self.path
        
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Demo Upload Server</title></head>
<body><h1>Demo File Upload Server</h1>
<p>This is a mock server for testing.</p>
<form method="POST" enctype="multipart/form-data" action="/upload">
<input type="file" name="file"><button>Upload</button>
</form></body></html>""")
        
        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "running",
                "config": self.config,
                "server": "fuva-mock-v1.0"
            }).encode())
        
        else:
            self.send_error(404)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for handling multiple requests."""
    allow_reuse_address = True
    daemon_threads = True


def start_demo_server(
    port: int = 8001,
    accept_all: bool = False,
    vulnerable: bool = False,
    delay: float = 0,
    store_uploads: bool = True,
):
    """Start the demo/mock server."""
    MockUploadHandler.config = {
        "accept_all": accept_all,
        "vulnerable": vulnerable,
        "delay": delay,
        "store_uploads": store_uploads,
    }
    
    server = ThreadedHTTPServer(("0.0.0.0", port), MockUploadHandler)
    
    print("=" * 60)
    print("FUVA Demo Server Started")
    print("=" * 60)
    print(f"Server running at: http://localhost:{port}")
    print(f"Accept all uploads: {accept_all}")
    print(f"Vulnerable mode: {vulnerable}")
    print(f"Upload delay: {delay}s")
    print(f"Store uploads: {store_uploads}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FUVA Demo Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--accept-all", action="store_true", help="Accept all file uploads")
    parser.add_argument("--vulnerable", action="store_true", help="Enable vulnerable mode (accepts malicious files)")
    parser.add_argument("--delay", type=float, default=0, help="Delay in seconds before responding")
    parser.add_argument("--no-store", action="store_true", help="Don't store uploaded files")
    
    args = parser.parse_args()
    
    start_demo_server(
        port=args.port,
        accept_all=args.accept_all,
        vulnerable=args.vulnerable,
        delay=args.delay,
        store_uploads=not args.no_store,
    )
