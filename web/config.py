"""Web application configuration."""

from pathlib import Path
import os


class Settings:
    """Application settings."""
    
    def __init__(self):
        self.app_name = "File Upload Validation Analyzer"
        self.app_description = "Web interface for file upload security testing"
        
        self.host = os.getenv("FUVA_WEB_HOST", "0.0.0.0")
        self.port = int(os.getenv("FUVA_WEB_PORT", "8000"))
        self.debug = os.getenv("FUVA_WEB_DEBUG", "false").lower() == "true"
        
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        self.temp_dir = Path("/tmp/fuva")
        
        self.max_file_size = 100 * 1024 * 1024
        
        self.cors_origins = ["*"]
        
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
