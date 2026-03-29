"""Anomaly detector for identifying security issues."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import statistics

from .response_analyzer import UploadResult
from ..utils.logging import get_logger


logger = get_logger("anomaly")


class AnomalyType(str, Enum):
    """Type of anomaly detected."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"


class Severity(str, Enum):
    """Severity level of anomaly."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_type: AnomalyType
    severity: Severity
    title: str
    description: str
    file_name: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_name": self.file_name,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


class AnomalyDetector:
    """Detect anomalies in upload responses."""
    
    def __init__(self):
        self.anomalies: List[Anomaly] = []
    
    def detect_anomalies(
        self,
        results: List[UploadResult],
    ) -> List[Anomaly]:
        """Detect all types of anomalies in results."""
        self.anomalies = []
        
        self._detect_security_anomalies(results)
        self._detect_performance_anomalies(results)
        self._detect_validation_anomalies(results)
        self._detect_configuration_anomalies(results)
        
        self._log_summary()
        return self.anomalies
    
    def _detect_security_anomalies(self, results: List[UploadResult]) -> None:
        """Detect security-related anomalies."""
        for result in results:
            file = result.file
            
            if result.success and self._is_dangerous_file(file):
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.SECURITY,
                    severity=Severity.CRITICAL,
                    title=f"Dangerous file accepted: {file.name}",
                    description=f"File type {file.mime_type} with {file.category} "
                               f"characteristics was accepted by the server",
                    file_name=file.name,
                    evidence={
                        "mime_type": file.mime_type,
                        "category": file.category,
                        "metadata": file.metadata,
                        "status_code": result.status_code,
                    },
                    recommendation="Implement proper file type validation and content inspection",
                )
                self.anomalies.append(anomaly)
                logger.error(f"Security anomaly: {file.name} accepted")
            
            if result.status_code == 200 and "error" not in result.body.lower():
                if self._contains_exploit_patterns(result.body):
                    anomaly = Anomaly(
                        anomaly_type=AnomalyType.SECURITY,
                        severity=Severity.HIGH,
                        title=f"Potential exploit pattern in response for {file.name}",
                        description="Server response contains patterns that may indicate "
                                   "vulnerability exposure",
                        file_name=file.name,
                        evidence={"status_code": result.status_code},
                        recommendation="Review server error handling",
                    )
                    self.anomalies.append(anomaly)
    
    def _is_dangerous_file(self, file) -> bool:
        """Check if file is potentially dangerous."""
        metadata = file.metadata or {}
        
        dangerous_types = [
            metadata.get("has_script"),
            metadata.get("has_embedded_script"),
            metadata.get("has_path_traversal"),
            metadata.get("has_symlink"),
            metadata.get("has_null_byte"),
            metadata.get("has_html_content"),
            metadata.get("has_rtl_override"),
            metadata.get("is_zip_bomb"),
            metadata.get("has_double_extension"),
            metadata.get("has_multiple_signatures"),
        ]
        
        return any(dangerous_types)
    
    def _contains_exploit_patterns(self, body: str) -> bool:
        """Check for common exploit patterns in response."""
        patterns = [
            "stack trace",
            "fatal error",
            "undefined index",
            "sql syntax",
            "mysql_fetch",
            "ORA-",
            "exception",
            "warning:",
            "syntax error",
            "Parse error",
            "system(",
            "exec(",
            "passthru",
            "shell_exec",
            "${",
            "cmd.exe",
            "/bin/sh",
            "<!ENTITY",
            "DOCTYPE",
            "xmlns:xi",
            "xinclude",
            "unserialize",
            "pickle.loads",
            "yaml.load",
            "ObjectInputStream",
            "Deserialization",
            "../",
            "..\\",
            "%2e%2e",
            "/etc/passwd",
            "boot.ini",
            "C:\\Windows",
            "phar://",
            "gopher://",
            "jar:",
        ]
        
        body_lower = body.lower()
        return any(pattern.lower() in body_lower for pattern in patterns)
    
    def _detect_performance_anomalies(self, results: List[UploadResult]) -> None:
        """Detect performance-related anomalies."""
        if not results:
            return
        
        response_times = [r.response_time for r in results]
        
        if len(response_times) < 2:
            return
        
        mean_time = statistics.mean(response_times)
        stdev_time = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        threshold = mean_time + (3 * stdev_time) if stdev_time > 0 else mean_time * 3
        
        for result in results:
            if result.response_time > threshold:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.PERFORMANCE,
                    severity=Severity.MEDIUM,
                    title=f"Slow response for {result.file.name}",
                    description=f"Response time {result.response_time:.2f}s exceeds "
                               f"threshold {threshold:.2f}s",
                    file_name=result.file.name,
                    evidence={
                        "response_time": result.response_time,
                        "mean_time": mean_time,
                        "threshold": threshold,
                    },
                    recommendation="Investigate server-side processing for this file type",
                )
                self.anomalies.append(anomaly)
                logger.warning(f"Performance anomaly: {result.file.name} slow")
        
        timeout_count = sum(1 for r in results if r.error and "timeout" in r.error.lower())
        if timeout_count > 0:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.PERFORMANCE,
                severity=Severity.HIGH,
                title=f"Multiple timeouts detected",
                description=f"{timeout_count} requests timed out",
                evidence={"timeout_count": timeout_count},
                recommendation="Check server timeout settings and file processing logic",
            )
            self.anomalies.append(anomaly)
    
    def _detect_validation_anomalies(self, results: List[UploadResult]) -> None:
        """Detect validation-related anomalies."""
        accepted = [r for r in results if r.success]
        rejected = [r for r in results if not r.success]
        
        acceptance_rate = len(accepted) / len(results) if results else 0
        
        if acceptance_rate > 0.8:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.VALIDATION,
                severity=Severity.HIGH,
                title="High acceptance rate",
                description=f"Server accepted {acceptance_rate*100:.1f}% of test files",
                evidence={
                    "accepted_count": len(accepted),
                    "total_count": len(results),
                    "acceptance_rate": acceptance_rate,
                },
                recommendation="Review file type validation - too many files accepted",
            )
            self.anomalies.append(anomaly)
            logger.warning(f"High acceptance rate: {acceptance_rate*100:.1f}%")
        
        for result in accepted:
            if result.file.size == 0:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.VALIDATION,
                    severity=Severity.MEDIUM,
                    title="Empty file accepted",
                    description=f"Zero-byte file {result.file.name} was accepted",
                    file_name=result.file.name,
                    evidence={"file_size": 0},
                    recommendation="Add minimum file size validation",
                )
                self.anomalies.append(anomaly)
    
    def _detect_configuration_anomalies(self, results: List[UploadResult]) -> None:
        """Detect configuration-related anomalies."""
        status_codes = {}
        for result in results:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        
        if 0 in status_codes:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.CONFIGURATION,
                severity=Severity.MEDIUM,
                title="Connection failures detected",
                description=f"{status_codes[0]} requests failed to connect",
                evidence={"failed_count": status_codes[0]},
                recommendation="Check network connectivity and server availability",
            )
            self.anomalies.append(anomaly)
        
        for result in results:
            server_header = result.headers.get("Server", "")
            if "Apache" in server_header or "nginx" in server_header:
                self._check_server_version(result, server_header)
    
    def _check_server_version(self, result: UploadResult, server: str) -> None:
        """Check for outdated server versions."""
        old_versions = ["Apache/2.2", "Apache/2.0", "nginx/1.0", "nginx/0.9"]
        
        for old_ver in old_versions:
            if old_ver in server:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.CONFIGURATION,
                    severity=Severity.HIGH,
                    title="Outdated server version",
                    description=f"Server uses outdated version: {server}",
                    evidence={"server": server},
                    recommendation="Update server to latest version for security patches",
                )
                self.anomalies.append(anomaly)
                logger.warning(f"Outdated server: {server}")
    
    def _log_summary(self) -> None:
        """Log anomaly summary."""
        if not self.anomalies:
            logger.success("No anomalies detected!")
            return
        
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        
        for anomaly in self.anomalies:
            severity_counts[anomaly.severity.value] = (
                severity_counts.get(anomaly.severity.value, 0) + 1
            )
        
        logger.info_block("Anomaly Detection Summary", f"""Critical: {severity_counts.get('critical', 0)}
High: {severity_counts.get('high', 0)}
Medium: {severity_counts.get('medium', 0)}
Low: {severity_counts.get('low', 0)}
Info: {severity_counts.get('info', 0)}
Total Anomalies: {len(self.anomalies)}
""")
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Get anomalies filtered by type."""
        return [a for a in self.anomalies if a.anomaly_type == anomaly_type]
    
    def get_anomalies_by_severity(self, severity: Severity) -> List[Anomaly]:
        """Get anomalies filtered by severity."""
        return [a for a in self.anomalies if a.severity == severity]
