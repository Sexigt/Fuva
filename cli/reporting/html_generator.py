"""HTML report generator."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..analyzers.response_analyzer import UploadResult
from ..analyzers.validation_comparator import ValidationGap
from ..analyzers.anomaly_detector import Anomaly
from ..utils.logging import get_logger


logger = get_logger("reporting")


class HTMLReportGenerator:
    """Generate HTML reports with tables and charts."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(
        self,
        results: List[UploadResult],
        gaps: Optional[List[ValidationGap]] = None,
        anomalies: Optional[List[Anomaly]] = None,
        target_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate complete HTML report."""
        gaps = gaps or []
        anomalies = anomalies or []
        metadata = metadata or {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"report_{timestamp}.html"
        
        html_content = self._build_html(
            results=results,
            gaps=gaps,
            anomalies=anomalies,
            target_url=target_url,
            metadata=metadata,
            timestamp=timestamp,
        )
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.success(f"HTML report generated: {report_file}")
        return report_file
    
    def _build_html(
        self,
        results: List[UploadResult],
        gaps: List[ValidationGap],
        anomalies: List[Anomaly],
        target_url: str,
        metadata: Dict[str, Any],
        timestamp: str,
    ) -> str:
        """Build complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload Validation Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 0.9em; }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        
        .status-success {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-error {{ color: #dc3545; }}
        .status-info {{ color: #17a2b8; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        
        .row-success {{ background: #d4edda; }}
        .row-error {{ background: #f8d7da; }}
        .row-warning {{ background: #fff3cd; }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .badge-critical {{ background: #dc3545; color: white; }}
        .badge-high {{ background: #fd7e14; color: white; }}
        .badge-medium {{ background: #ffc107; color: #333; }}
        .badge-low {{ background: #17a2b8; color: white; }}
        .badge-info {{ background: #6c757d; color: white; }}
        
        .chart-container {{ position: relative; height: 300px; margin: 20px 0; }}
        
        .summary-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        
        pre {{ 
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.85em;
        }}
        
        .collapsible {{ cursor: pointer; }}
        .collapsible:after {{ content: " ▼"; }}
        .collapsible.collapsed:after {{ content: " ▶"; }}
        
        .tabs {{ display: flex; border-bottom: 2px solid #ddd; margin-bottom: 20px; }}
        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            color: #666;
        }}
        .tab.active {{ 
            color: #667eea;
            border-bottom: 2px solid #667eea;
            font-weight: 600;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>File Upload Validation Analyzer</h1>
            <div class="meta">
                <div>Target: <strong>{target_url}</strong></div>
                <div>Generated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></div>
                <div>Report ID: <strong>{timestamp}</strong></div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value status-success">{sum(1 for r in results if r.success)}</div>
                <div class="stat-label">Accepted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value status-error">{sum(1 for r in results if not r.success)}</div>
                <div class="stat-label">Rejected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value status-warning">{len(anomalies)}</div>
                <div class="stat-label">Anomalies</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(gaps)}</div>
                <div class="stat-label">Validation Gaps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self._get_avg_response_time(results):.3f}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Status Code Distribution</h2>
            <div class="chart-container">
                <canvas id="statusChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h2>Response Time Analysis</h2>
            <div class="chart-container">
                <canvas id="responseTimeChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h2>Validation Gaps ({len(gaps)})</h2>
            {self._build_gaps_table(gaps) if gaps else '<p>No validation gaps detected.</p>'}
        </div>
        
        <div class="card">
            <h2>Security Anomalies ({len(anomalies)})</h2>
            {self._build_anomalies_table(anomalies) if anomalies else '<p>No anomalies detected.</p>'}
        </div>
        
        <div class="card">
            <h2>Upload Test Results</h2>
            {self._build_results_table(results)}
        </div>
    </div>
    
    <script>
        // Status Code Chart
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(self._get_status_labels(results))},
                datasets: [{{
                    label: 'Status Codes',
                    data: {json.dumps(self._get_status_values(results))},
                    backgroundColor: {json.dumps(self._get_status_colors(results))}
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        // Response Time Chart
        const responseCtx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(responseCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([r.file.name[:15] for r in results[:20]])},
                datasets: [{{
                    label: 'Response Time (s)',
                    data: {json.dumps([round(r.response_time, 3) for r in results[:20]])},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});
    </script>
</body>
</html>"""
    
    def _build_gaps_table(self, gaps: List[ValidationGap]) -> str:
        """Build validation gaps table."""
        rows = []
        for gap in gaps:
            badge_class = f"badge-{gap.severity}"
            rows.append(f"""
            <tr>
                <td>{gap.file_name}</td>
                <td>{gap.category}</td>
                <td>{gap.description}</td>
                <td>{gap.api_status_code}</td>
                <td>{'Yes' if gap.ui_rejected else 'No'}</td>
                <td><span class="badge {badge_class}">{gap.severity.upper()}</span></td>
            </tr>
            """)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>API Status</th>
                    <th>UI Rejected</th>
                    <th>Severity</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _build_anomalies_table(self, anomalies: List[Anomaly]) -> str:
        """Build anomalies table."""
        rows = []
        for anomaly in anomalies:
            badge_class = f"badge-{anomaly.severity.value}"
            rows.append(f"""
            <tr>
                <td><span class="badge {badge_class}">{anomaly.anomaly_type.value.upper()}</span></td>
                <td>{anomaly.title}</td>
                <td>{anomaly.description}</td>
                <td><span class="badge {badge_class}">{anomaly.severity.value.upper()}</span></td>
                <td>{anomaly.recommendation}</td>
            </tr>
            """)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Title</th>
                    <th>Description</th>
                    <th>Severity</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _build_results_table(self, results: List[UploadResult]) -> str:
        """Build upload results table."""
        rows = []
        for r in results:
            row_class = "row-success" if r.success else "row-error"
            status_text = f"{r.status_code}" if r.status_code else "Error"
            rows.append(f"""
            <tr class="{row_class}">
                <td>{r.file.name}</td>
                <td>{r.file.category}</td>
                <td>{r.file.mime_type}</td>
                <td>{r.file.size} bytes</td>
                <td>{status_text}</td>
                <td>{r.response_time:.3f}s</td>
                <td>{r.error or '-'}</td>
            </tr>
            """)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Category</th>
                    <th>MIME Type</th>
                    <th>Size</th>
                    <th>Status</th>
                    <th>Time</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _get_status_labels(self, results: List[UploadResult]) -> List[str]:
        """Get unique status codes as labels."""
        codes = set(r.status_code for r in results)
        return [str(c) for c in sorted(codes)]
    
    def _get_status_values(self, results: List[UploadResult]) -> List[int]:
        """Get count per status code."""
        codes = {}
        for r in results:
            codes[r.status_code] = codes.get(r.status_code, 0) + 1
        
        sorted_codes = sorted(codes.keys())
        return [codes[c] for c in sorted_codes]
    
    def _get_status_colors(self, results: List[UploadResult]) -> List[str]:
        """Get colors for status codes."""
        codes = sorted(set(r.status_code for r in results))
        colors = []
        for code in codes:
            if 200 <= code < 300:
                colors.append("#28a745")
            elif 300 <= code < 400:
                colors.append("#17a2b8")
            elif 400 <= code < 500:
                colors.append("#ffc107")
            elif 500 <= code:
                colors.append("#dc3545")
            else:
                colors.append("#6c757d")
        return colors
    
    def _get_avg_response_time(self, results: List[UploadResult]) -> float:
        """Calculate average response time."""
        if not results:
            return 0.0
        return sum(r.response_time for r in results) / len(results)
