"""Configuration management for CLI with cross-platform support."""

import yaml
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import sys

# Add parent to path for platform utils
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from cli.utils.platform import get_config_dir, get_data_dir, get_temp_dir, get_log_dir
except ImportError:
    # Fallback if platform utils not available
    def get_config_dir():
        base = Path.home() / ".config" if os.name != "nt" else Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "fuva"
    
    def get_data_dir():
        base = Path.home() / ".local" / "share" if os.name != "nt" else Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "fuva"
    
    def get_temp_dir():
        import tempfile
        return Path(tempfile.gettempdir()) / "fuva"
    
    def get_log_dir():
        return get_data_dir() / "logs"


@dataclass
class CLIConfig:
    """Main CLI configuration class."""
    
    target_url: str = ""
    output_dir: Path = field(default_factory=lambda: Path("reports"))
    log_dir: Path = field(default_factory=get_log_dir)
    temp_dir: Path = field(default_factory=get_temp_dir)
    
    timeout: int = 30
    delay: float = 0
    max_retries: int = 0
    retry_delay: float = 1.0
    
    workers: int = 1
    
    proxy: Optional[str] = None
    proxy_chain: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    auth_token: Optional[str] = None
    auth_cookie: Dict[str, str] = field(default_factory=dict)
    
    generate_images: bool = True
    generate_documents: bool = True
    generate_archives: bool = True
    generate_mixed: bool = True
    generate_executables: bool = True
    
    form_field: str = "file"
    additional_data: dict = field(default_factory=dict)
    
    log_level: str = "INFO"
    use_colors: bool = True
    
    export_har: bool = False
    export_dir: Path = field(default_factory=lambda: Path("exports"))
    
    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.log_dir = Path(self.log_dir)
        self.temp_dir = Path(self.temp_dir)
        self.export_dir = Path(self.export_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)


class FileConfig:
    """File-based configuration with YAML/JSON support."""
    
    DEFAULT_CONFIG = {
        "web": {
            "host": "0.0.0.0",
            "port": 8000,
            "auth_enabled": False,
            "password": None,
        },
        "cli": {
            "default_timeout": 30,
            "default_workers": 1,
            "default_delay": 0,
            "default_retries": 0,
        },
        "storage": {
            "data_dir": None,
            "backup_enabled": True,
            "max_backups": 10,
        },
        "logging": {
            "level": "INFO",
            "file_enabled": True,
            "console_enabled": True,
        },
        "proxy": {
            "enabled": False,
            "http": None,
            "https": None,
        },
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (get_config_dir() / "config.yaml")
        self._config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix == '.json':
                        user_config = json.load(f)
                    else:
                        user_config = yaml.safe_load(f) or {}
                
                config = self.DEFAULT_CONFIG.copy()
                self._deep_merge(config, user_config)
                return config
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge update dict into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a config value using dot notation."""
        keys = key.split('.')
        target = self._config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value


# Global config instance
_config_instance: Optional[FileConfig] = None


def get_config() -> FileConfig:
    """Get the global file config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = FileConfig()
    return _config_instance
