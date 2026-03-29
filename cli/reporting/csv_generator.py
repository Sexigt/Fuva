"""CSV report generator."""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class CSVReportGenerator:
    """Generate CSV reports."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_csv_report(
        self,
        results: List,
        anomalies: List[Dict[str, Any]],
        target_url: str,
        metadata: Dict[str, Any] = None,
    ) -> Path:
        """Generate CSV report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "File Name", "Category", "MIME Type", "Status Code",
                "Success", "Response Time (s)", "Error", "Matched Patterns"
            ])
            
            for result in results:
                writer.writerow([
                    result.file.name,
                    result.file.category,
                    result.file.mime_type,
                    result.status_code,
                    result.success,
                    f"{result.response_time:.3f}" if result.response_time else "",
                    result.error or "",
                    ", ".join(result.matched_patterns) if result.matched_patterns else "",
                ])
            
            if anomalies:
                writer.writerow([])
                writer.writerow(["Anomalies"])
                writer.writerow([
                    "Type", "Severity", "Title", "Description",
                    "File Name", "Recommendation"
                ])
                
                for anomaly in anomalies:
                    if hasattr(anomaly, 'to_dict'):
                        a = anomaly.to_dict()
                    else:
                        a = anomaly
                    writer.writerow([
                        a.get("anomaly_type", ""),
                        a.get("severity", ""),
                        a.get("title", ""),
                        a.get("description", ""),
                        a.get("file_name", ""),
                        a.get("recommendation", ""),
                    ])
        
        return filepath
    
    def generate_summary_csv(
        self,
        runs: List[Dict[str, Any]],
    ) -> Path:
        """Generate summary CSV for multiple runs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "Run ID", "Target URL", "Status", "Total Tests",
                "Accepted", "Rejected", "Anomalies", "Created At", "Completed At"
            ])
            
            for run in runs:
                writer.writerow([
                    run.get("id", ""),
                    run.get("target_url", ""),
                    run.get("status", ""),
                    run.get("total_tests", 0),
                    run.get("accepted", 0),
                    run.get("rejected", 0),
                    run.get("anomalies", 0),
                    run.get("created_at", ""),
                    run.get("completed_at", ""),
                ])
        
        return filepath
