"""HAR (HTTP Archive) export for request/response capture."""

import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class HARExporter:
    """Export HTTP traffic to HAR format."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries: List[Dict] = []
        self.started_date_time = datetime.now().isoformat() + "Z"
    
    def add_entry(
        self,
        method: str,
        url: str,
        status_code: int,
        request_headers: Dict[str, str],
        response_headers: Dict[str, str],
        request_body: Optional[bytes] = None,
        response_body: Optional[str] = None,
        time: float = 0,
        mime_type: str = "",
    ):
        """Add an entry to the HAR log."""
        entry = {
            "startedDateTime": datetime.now().isoformat() + "Z",
            "time": time * 1000,  # Convert to milliseconds
            "request": {
                "method": method,
                "url": url,
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": [{"name": k, "value": v} for k, v in request_headers.items()],
                "queryString": [],
                "postData": {
                    "mimeType": mime_type,
                    "text": request_body.decode('utf-8', errors='replace') if request_body else "",
                } if request_body else {},
                "headersSize": -1,
                "bodySize": len(request_body) if request_body else 0,
            },
            "response": {
                "status": status_code,
                "statusText": "",
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": [{"name": k, "value": v} for k, v in response_headers.items()],
                "content": {
                    "size": len(response_body) if response_body else 0,
                    "mimeType": response_headers.get("Content-Type", ""),
                    "text": response_body[:100000] if response_body else "",  # Limit size
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": len(response_body) if response_body else 0,
            },
            "cache": {},
            "timings": {
                "send": 0,
                "wait": time * 1000,
                "receive": 0,
            },
        }
        self.entries.append(entry)
    
    def save(self, filename: Optional[str] = None) -> Path:
        """Save HAR to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"har_{timestamp}.har"
        
        filepath = self.output_dir / filename
        
        har = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "File Upload Validation Analyzer",
                    "version": "1.0.0",
                },
                "pages": [],
                "entries": self.entries,
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(har, f, indent=2)
        
        return filepath
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of captured traffic."""
        return {
            "total_requests": len(self.entries),
            "successful": sum(1 for e in self.entries if e["response"]["status"] < 400),
            "failed": sum(1 for e in self.entries if e["response"]["status"] >= 400),
            "total_size": sum(e["response"]["content"]["size"] for e in self.entries),
        }


class FingerprintDetector:
    """Detect server technology from HTTP responses."""
    
    FINGERPRINTS = {
        "apache": {
            "headers": {"Server": r"Apache"},
            "body": None,
        },
        "nginx": {
            "headers": {"Server": r"nginx"},
            "body": None,
        },
        "iis": {
            "headers": {"Server": r"IIS|Microsoft-IIS"},
            "body": None,
        },
        "cloudflare": {
            "headers": {"Server": r"cloudflare", "CF-RAY": None},
            "body": None,
        },
        "php": {
            "headers": {"X-Powered-By": r"PHP"},
            "body": None,
        },
        "asp.net": {
            "headers": {"X-Powered-By": r"ASP\\.NET"},
            "body": None,
        },
        "express": {
            "headers": {"Server": r"Express"},
            "body": None,
        },
        "django": {
            "headers": {"Server": r"gunicorn", "X-Generator": r"Django"},
            "body": None,
        },
        "flask": {
            "headers": {"Server": r"Werkzeug"},
            "body": None,
        },
        "nodejs": {
            "headers": {"Server": r"Node\\.js"},
            "body": None,
        },
        "java_tomcat": {
            "headers": {"Server": r"Apache.*Tomcat"},
            "body": None,
        },
        "jetty": {
            "headers": {"Server": r"Jetty"},
            "body": None,
        },
        "fastly": {
            "headers": {"Server": r"Fastly"},
            "body": None,
        },
        "aws_s3": {
            "headers": {"Server": r"AmazonS3"},
            "body": None,
        },
        "wordpress": {
            "headers": None,
            "body": r"wp-content|wp-includes",
        },
        "drupal": {
            "headers": None,
            "body": r"Drupal|X-Generator.*Drupal",
        },
        "joomla": {
            "headers": None,
            "body": r"option=com_",
        },
    }
    
    def detect(self, headers: Dict[str, str], body: str = "") -> Dict[str, Any]:
        """Detect server technology from response."""
        results = {
            "frameworks": [],
            "servers": [],
            "cms": [],
            "technologies": [],
            "confidence": 0,
        }
        
        for name, fingerprint in self.FINGERPRINTS.items():
            matches = 0
            
            # Check headers
            if fingerprint.get("headers"):
                for header, pattern in fingerprint["headers"].items():
                    header_value = headers.get(header, "")
                    if pattern is None:
                        if header_value:
                            matches += 1
                    elif pattern in header_value or hasattr(pattern, 'search') and pattern.search(header_value):
                        matches += 1
            
            # Check body
            if fingerprint.get("body"):
                if body:
                    import re
                    if re.search(fingerprint["body"], body, re.IGNORECASE):
                        matches += 1
            
            if matches > 0:
                if name in ("apache", "nginx", "iis", "cloudflare", "fastly", "aws_s3"):
                    results["servers"].append(name)
                elif name in ("wordpress", "drupal", "joomla"):
                    results["cms"].append(name)
                else:
                    results["frameworks"].append(name)
                
                results["technologies"].append(name)
                results["confidence"] = min(results["confidence"] + (matches * 0.2), 1.0)
        
        return results
