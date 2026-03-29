"""Validation comparator for API vs UI validation comparison."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from .response_analyzer import UploadResult
from ..utils.logging import get_logger


logger = get_logger("comparator")


class ValidationType(str, Enum):
    """Type of validation."""
    API = "api"
    UI = "ui"
    BOTH = "both"
    NONE = "none"


@dataclass
class ValidationGap:
    """Represents a gap between API and UI validation."""
    file_name: str
    category: str
    description: str
    api_status_code: int
    ui_rejected: bool
    severity: str
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_name": self.file_name,
            "category": self.category,
            "description": self.description,
            "api_status_code": self.api_status_code,
            "ui_rejected": self.ui_rejected,
            "severity": self.severity,
            "recommendation": self.recommendation,
        }


class ValidationComparator:
    """Compare API validation vs UI validation."""
    
    def __init__(self):
        self.gaps: List[ValidationGap] = []
    
    def compare_api_ui(
        self,
        results: List[UploadResult],
        ui_errors: Optional[Dict[str, str]] = None,
    ) -> List[ValidationGap]:
        """
        Compare API and UI validation.
        
        Args:
            results: List of upload results
            ui_errors: Optional dict mapping filename to UI error message
        
        Returns:
            List of validation gaps found
        """
        ui_errors = ui_errors or {}
        gaps = []
        
        for result in results:
            file = result.file
            ui_error = ui_errors.get(file.name)
            
            api_accepted = 200 <= result.status_code < 300
            ui_rejected = ui_error is not None
            
            if api_accepted and ui_rejected:
                gap = ValidationGap(
                    file_name=file.name,
                    category=file.category,
                    description=(
                        f"API accepted {file.name} ({file.mime_type}) "
                        f"but UI rejected it: {ui_error}"
                    ),
                    api_status_code=result.status_code,
                    ui_rejected=True,
                    severity="medium",
                    recommendation="Check UI validation logic for false positives",
                )
                gaps.append(gap)
                logger.warning(f"UI false positive: {file.name}")
                
            elif not api_accepted and not ui_rejected:
                gap = ValidationGap(
                    file_name=file.name,
                    category=file.category,
                    description=(
                        f"API rejected {file.name} (status {result.status_code}) "
                        f"but UI accepted it"
                    ),
                    api_status_code=result.status_code,
                    ui_rejected=False,
                    severity="high",
                    recommendation="Add UI validation to match API validation",
                )
                gaps.append(gap)
                logger.error(f"API rejected but UI accepted: {file.name}")
                
            elif api_accepted and not ui_rejected:
                gap = ValidationGap(
                    file_name=file.name,
                    category=file.category,
                    description=f"Both API and UI accepted {file.name}",
                    api_status_code=result.status_code,
                    ui_rejected=False,
                    severity="low",
                    recommendation="Review if file should be blocked",
                )
                gaps.append(gap)
                logger.info(f"Both accepted: {file.name}")
        
        self.gaps = gaps
        self._log_summary()
        return gaps
    
    def detect_missing_validations(
        self,
        results: List[UploadResult],
    ) -> List[ValidationGap]:
        """Detect missing validation types."""
        gaps = []
        
        for result in results:
            file = result.file
            
            if self._is_malicious_file(file) and result.success:
                gap = ValidationGap(
                    file_name=file.name,
                    category=file.category,
                    description=f"Potentially malicious file was accepted: {file.description}",
                    api_status_code=result.status_code,
                    ui_rejected=False,
                    severity="critical",
                    recommendation="Implement proper file type validation",
                )
                gaps.append(gap)
                logger.error(f"Malicious file accepted: {file.name}")
        
        self.gaps.extend(gaps)
        return gaps
    
    def _is_malicious_file(self, file) -> bool:
        """Check if file is potentially malicious based on metadata."""
        metadata = file.metadata or {}
        
        malicious_indicators = [
            metadata.get("has_script"),
            metadata.get("has_embedded_script"),
            metadata.get("has_path_traversal"),
            metadata.get("has_symlink"),
            metadata.get("has_null_byte"),
            metadata.get("has_double_extension"),
            metadata.get("has_rtl_override"),
            metadata.get("is_zip_bomb"),
        ]
        
        return any(malicious_indicators)
    
    def _log_summary(self) -> None:
        """Log comparison summary."""
        if not self.gaps:
            logger.success("No validation gaps found!")
            return
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for gap in self.gaps:
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1
        
        logger.info_block("Validation Comparison Summary", f"""Critical: {severity_counts.get('critical', 0)}
High: {severity_counts.get('high', 0)}
Medium: {severity_counts.get('medium', 0)}
Low: {severity_counts.get('low', 0)}
Total Gaps: {len(self.gaps)}
""")
    
    def get_gaps_by_severity(self, severity: str) -> List[ValidationGap]:
        """Get validation gaps filtered by severity."""
        return [g for g in self.gaps if g.severity == severity]
    
    def get_gaps_by_category(self, category: str) -> List[ValidationGap]:
        """Get validation gaps filtered by category."""
        return [g for g in self.gaps if g.category == category]
