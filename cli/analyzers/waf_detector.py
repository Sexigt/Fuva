"""WAF detection module."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class WAFType(str, Enum):
    """Type of WAF detected."""
    CLOUDFLARE = "cloudflare"
    AWS_WAF = "aws_waf"
    AKAMAI = "akamai"
    F5_BIGIP = "f5_bigip"
    SUCURI = "sucuri"
    IMPERVA = "imperva"
    FORTIWEB = "fortiweb"
    MODSECURITY = "modsecurity"
    UNKNOWN = "unknown"


@dataclass
class WAFDetection:
    """Represents a detected WAF."""
    waf_type: WAFType
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "waf_type": self.waf_type.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class WAFDetector:
    """Detect WAFs from HTTP responses."""
    
    WAF_SIGNATURES = {
        WAFType.CLOUDFLARE: {
            "headers": {"Server": r"cloudflare", "CF-RAY": None, "CF-Cache-Status": None},
            "body": ["Attention Required! | Cloudflare", "cf-error-details"],
            "status_codes": [403, 503],
        },
        WAFType.AWS_WAF: {
            "headers": {"Server": r"AWS", "X-Amzn-Requestid": None},
            "body": ["403 ERROR", "The request could not be satisfied", "AWS WAF"],
            "status_codes": [403, 405],
        },
        WAFType.AKAMAI: {
            "headers": {"Server": r"Akamai", "X-Cdn": None, "X-Akamai-Transformed": None},
            "body": ["Reference #", "Access Denied"],
            "status_codes": [403],
        },
        WAFType.F5_BIGIP: {
            "headers": {"Server": r"BIG-IP", "X-Correlation-ID": None},
            "body": ["The requested URL was rejected", "TS= "],
            "status_codes": [403],
        },
        WAFType.SUCURI: {
            "headers": {"Server": r"Sucuri", "X-Sucuri-ID": None, "X-Sucuri-Cache-Status": None},
            "body": ["Sucuri Website Firewall", "Access Denied - Sucuri"],
            "status_codes": [403],
        },
        WAFType.IMPERVA: {
            "headers": {"Server": r"Incapsula", "X-CDN": None, "X-Iinfo": None},
            "body": ["Incapsula incident ID", "_Incapsula_Resource"],
            "status_codes": [403, 405],
        },
        WAFType.FORTIWEB: {
            "headers": {"Server": r"FortiWeb", "X-FortiWeb": None},
            "body": ["FortiWeb", "attack ID"],
            "status_codes": [403],
        },
        WAFType.MODSECURITY: {
            "headers": {"Server": None},
            "body": ["ModSecurity", "mod_security", "403 Forbidden"],
            "status_codes": [403],
        },
    }
    
    def __init__(self):
        self.detections: List[WAFDetection] = []
    
    def detect(self, status_code: int, headers: Dict[str, str], body: str) -> Optional[WAFDetection]:
        """Detect WAF from response."""
        for waf_type, sigs in self.WAF_SIGNATURES.items():
            confidence = 0.0
            evidence = {}
            
            for header_name, pattern in sigs.get("headers", {}).items():
                if header_name and header_name.lower() in [h.lower() for h in headers]:
                    if pattern is None or pattern in headers.get(header_name, ""):
                        confidence += 0.4
                        evidence[f"header_{header_name}"] = headers.get(header_name)
            
            body_lower = body.lower() if body else ""
            for pattern in sigs.get("body", []):
                if pattern.lower() in body_lower:
                    confidence += 0.4
                    evidence["body_match"] = pattern
            
            if status_code in sigs.get("status_codes", []):
                confidence += 0.2
                evidence["status_code"] = status_code
            
            if confidence >= 0.4:
                detection = WAFDetection(waf_type=waf_type, confidence=min(confidence, 1.0), evidence=evidence)
                self.detections.append(detection)
                return detection
        
        return None
    
    def detect_batch(self, results: List) -> List[WAFDetection]:
        """Detect WAF across multiple results."""
        waf_detections = {}
        
        for result in results:
            status_code = result.status_code
            headers = dict(result.headers) if result.headers else {}
            body = result.body or ""
            
            detection = self.detect(status_code, headers, body)
            if detection:
                if detection.waf_type not in waf_detections:
                    waf_detections[detection.waf_type] = detection
        
        return list(waf_detections.values())
    
    def is_blocked_by_waf(self, status_code: int, headers: Dict[str, str], body: str) -> bool:
        """Check if request was blocked by WAF."""
        if status_code in (403, 405, 429, 503):
            detection = self.detect(status_code, headers, body)
            return detection is not None
        return False
    
    def get_blocked_results(self, results: List) -> List:
        """Get results that were likely blocked by WAF."""
        blocked = []
        for result in results:
            headers = dict(result.headers) if result.headers else {}
            if self.is_blocked_by_waf(result.status_code, headers, result.body or ""):
                blocked.append(result)
        return blocked
