"""JSON report generator."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from ..analyzers.response_analyzer import UploadResult
from ..analyzers.validation_comparator import ValidationGap
from ..analyzers.anomaly_detector import Anomaly
from ..utils.logging import get_logger


logger = get_logger("reporting")


class JSONReportGenerator:
    """Generate JSON reports for machine analysis."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(
        self,
        results: List[UploadResult],
        gaps: Optional[List[ValidationGap]] = None,
        anomalies: Optional[List[Anomaly]] = None,
        target_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate JSON report."""
        gaps = gaps or []
        anomalies = anomalies or []
        metadata = metadata or {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"report_{timestamp}.json"
        
        report_data = self._build_report_data(
            results=results,
            gaps=gaps,
            anomalies=anomalies,
            target_url=target_url,
            metadata=metadata,
            timestamp=timestamp,
        )
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.success(f"JSON report generated: {report_file}")
        return report_file
    
    def _build_report_data(
        self,
        results: List[UploadResult],
        gaps: List[ValidationGap],
        anomalies: List[Anomaly],
        target_url: str,
        metadata: Dict[str, Any],
        timestamp: str,
    ) -> Dict[str, Any]:
        """Build complete report data structure."""
        
        status_distribution = self._get_status_distribution(results)
        category_distribution = self._get_category_distribution(results)
        severity_counts = self._get_severity_counts(anomalies)
        
        return {
            "report_metadata": {
                "report_id": timestamp,
                "generated_at": datetime.now().isoformat(),
                "target_url": target_url,
                "tool_version": "0.1.0",
                "metadata": metadata,
            },
            "summary": {
                "total_tests": len(results),
                "accepted": sum(1 for r in results if r.success),
                "rejected": sum(1 for r in results if not r.success),
                "acceptance_rate": self._calculate_rate(
                    sum(1 for r in results if r.success),
                    len(results)
                ),
                "total_gaps": len(gaps),
                "total_anomalies": len(anomalies),
                "avg_response_time": self._get_avg_response_time(results),
                "min_response_time": self._get_min_response_time(results),
                "max_response_time": self._get_max_response_time(results),
            },
            "status_distribution": status_distribution,
            "category_distribution": category_distribution,
            "severity_counts": severity_counts,
            "validation_gaps": [gap.to_dict() for gap in gaps],
            "anomalies": [anomaly.to_dict() for anomaly in anomalies],
            "test_results": [self._result_to_dict(r) for r in results],
        }
    
    def _result_to_dict(self, result: UploadResult) -> Dict[str, Any]:
        """Convert UploadResult to dictionary."""
        return {
            "file": {
                "name": result.file.name,
                "path": str(result.file.path),
                "type": result.file.file_type,
                "mime_type": result.file.mime_type,
                "size": result.file.size,
                "category": result.file.category,
                "description": result.file.description,
                "metadata": result.file.metadata,
            },
            "success": result.success,
            "status_code": result.status_code,
            "response_time": result.response_time,
            "headers": result.headers,
            "error": result.error,
            "ui_error": result.ui_error,
            "validation_passed": result.validation_passed,
        }
    
    def _get_status_distribution(self, results: List[UploadResult]) -> Dict[str, int]:
        """Get status code distribution."""
        distribution = {}
        for r in results:
            code = str(r.status_code)
            distribution[code] = distribution.get(code, 0) + 1
        return distribution
    
    def _get_category_distribution(self, results: List[UploadResult]) -> Dict[str, int]:
        """Get file category distribution."""
        distribution = {}
        for r in results:
            category = r.file.category
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def _get_severity_counts(self, anomalies: List[Anomaly]) -> Dict[str, int]:
        """Get anomaly counts by severity."""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for anomaly in anomalies:
            severity = anomaly.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _calculate_rate(self, part: int, total: int) -> float:
        """Calculate rate percentage."""
        if total == 0:
            return 0.0
        return round((part / total) * 100, 2)
    
    def _get_avg_response_time(self, results: List[UploadResult]) -> float:
        """Get average response time."""
        if not results:
            return 0.0
        return round(sum(r.response_time for r in results) / len(results), 3)
    
    def _get_min_response_time(self, results: List[UploadResult]) -> float:
        """Get minimum response time."""
        if not results:
            return 0.0
        return round(min(r.response_time for r in results), 3)
    
    def _get_max_response_time(self, results: List[UploadResult]) -> float:
        """Get maximum response time."""
        if not results:
            return 0.0
        return round(max(r.response_time for r in results), 3)
    
    def export_minimal(self, results: List[UploadResult]) -> Dict[str, Any]:
        """Export minimal JSON for quick analysis."""
        return {
            "total": len(results),
            "accepted": sum(1 for r in results if r.success),
            "rejected": sum(1 for r in results if not r.success),
            "status_codes": self._get_status_distribution(results),
        }
