"""Background test runner service."""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import threading
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.generators import (
    CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage, EmptyImage,
    EdgeCasePDF, MalformedSVG, LargePDF, CorruptZIP, ZipSlipArchive,
    LargeArchive, EmptyArchive, TextInBinary, DoubleExtensionFile,
    NullByteInjection, PolyglotFile,
)
from cli.analyzers import ResponseAnalyzer, ValidationComparator, AnomalyDetector
from cli.reporting import HTMLReportGenerator, JSONReportGenerator
from cli.config import Config


class RunStatus(str, Enum):
    """Status of a test run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestRunner:
    """Background service for running upload tests."""
    
    def __init__(self):
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def run_tests(
        self,
        run_id: str,
        target_url: str,
        timeout: int = 30,
        delay: float = 0,
        form_field: str = "file",
        generate_html: bool = True,
        generate_json: bool = True,
    ) -> None:
        """Run upload tests in background."""
        with self._lock:
            self._runs[run_id] = {
                "run_id": run_id,
                "target_url": target_url,
                "status": RunStatus.RUNNING.value,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "total_tests": 0,
                "accepted": 0,
                "rejected": 0,
                "anomalies": 0,
                "gaps": 0,
                "html_report": None,
                "json_report": None,
                "error": None,
            }
        
        try:
            config = Config(
                target_url=target_url,
                output_dir="reports",
                timeout=timeout,
                delay=delay,
            )
            
            generator_classes = [
                CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage,
                EmptyImage, EdgeCasePDF, MalformedSVG, CorruptZIP,
                ZipSlipArchive, TextInBinary, DoubleExtensionFile,
                NullByteInjection, PolyglotFile,
            ]
            
            temp_dir = Path(config.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            test_files = []
            for gen_class in generator_classes:
                with gen_class(output_dir=temp_dir) as gen:
                    test_files.append(gen.generate())
            
            analyzer = ResponseAnalyzer(target_url=target_url, timeout=timeout)
            results = analyzer.run_upload_tests(test_files, delay=delay)
            
            anomaly_detector = AnomalyDetector()
            anomalies = anomaly_detector.detect_anomalies(results)
            
            comparator = ValidationComparator()
            gaps = comparator.compare_api_ui(results)
            
            html_path = None
            json_path = None
            
            html_gen = HTMLReportGenerator(str(config.output_dir))
            json_gen = JSONReportGenerator(str(config.output_dir))
            
            if generate_html:
                html_path = str(html_gen.generate_html_report(
                    results=results,
                    gaps=gaps,
                    anomalies=anomalies,
                    target_url=target_url,
                    metadata={"timeout": timeout, "delay": delay},
                ))
            
            if generate_json:
                json_path = str(json_gen.generate_json_report(
                    results=results,
                    gaps=gaps,
                    anomalies=anomalies,
                    target_url=target_url,
                    metadata={"timeout": timeout, "delay": delay},
                ))
            
            with self._lock:
                self._runs[run_id].update({
                    "status": RunStatus.COMPLETED.value,
                    "completed_at": datetime.now().isoformat(),
                    "total_tests": len(results),
                    "accepted": sum(1 for r in results if r.success),
                    "rejected": sum(1 for r in results if not r.success),
                    "anomalies": len(anomalies),
                    "gaps": len(gaps),
                    "html_report": html_path,
                    "json_report": json_path,
                })
        
        except Exception as e:
            with self._lock:
                self._runs[run_id].update({
                    "status": RunStatus.FAILED.value,
                    "completed_at": datetime.now().isoformat(),
                    "error": str(e),
                })
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run."""
        with self._lock:
            return self._runs.get(run_id)
    
    def get_all_runs(self) -> Dict[str, Dict[str, Any]]:
        """Get all runs."""
        with self._lock:
            return dict(self._runs)
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a run."""
        with self._lock:
            if run_id in self._runs:
                del self._runs[run_id]
                return True
            return False
