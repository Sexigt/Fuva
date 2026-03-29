"""Cross-platform utilities for Windows and Linux support."""

import os
import sys
import platform
import shutil
import atexit
import signal
import tempfile
from pathlib import Path
from typing import Optional, Callable


def get_os() -> str:
    """Get the operating system name."""
    return platform.system().lower()


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_os() == "windows"


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_os() == "linux"


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_os() == "darwin"


def get_config_dir() -> Path:
    """Get the config directory (cross-platform)."""
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif is_macos():
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    
    config_dir = base / "fuva"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get the data directory (cross-platform)."""
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    
    data_dir = base / "fuva"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_temp_dir() -> Path:
    """Get a temp directory for the app (cross-platform)."""
    temp_base = Path(tempfile.gettempdir())
    temp_dir = temp_base / "fuva"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def cleanup_temp_files():
    """Clean up temporary files on exit."""
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temp files: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean temp files: {e}")


def get_log_dir() -> Path:
    """Get the log directory (cross-platform)."""
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    
    log_dir = base / "fuva" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


class GracefulShutdown:
    """Handle graceful shutdown on various signals."""
    
    def __init__(self):
        self.cleanup_callbacks: list[Callable] = []
        self._shutdown = False
        self._register_handlers()
        atexit.register(self._do_cleanup)
    
    def register_cleanup(self, callback: Callable):
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)
    
    def _register_handlers(self):
        """Register signal handlers (cross-platform)."""
        if is_windows():
            # Windows: only supports SIGINT (Ctrl+C)
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
            except (ValueError, OSError):
                pass
        else:
            # Unix-like: supports SIGINT and SIGTERM
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    signal.signal(sig, self._signal_handler)
                except (ValueError, OSError):
                    pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signal."""
        print("\n" + "="*50)
        print("Shutting down gracefully...")
        print("="*50)
        self._do_cleanup()
        sys.exit(0)
    
    def _do_cleanup(self):
        """Run all cleanup callbacks."""
        if self._shutdown:
            return
        self._shutdown = True
        
        # Run cleanup callbacks in reverse order
        for callback in reversed(self.cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                print(f"Cleanup error: {e}")
        
        # Clean up temp files
        try:
            cleanup_temp_files()
        except Exception:
            pass


# Global graceful shutdown handler
shutdown_handler = GracefulShutdown()


def get_default_config_path() -> Path:
    """Get the default config file path."""
    return get_config_dir() / "config.yaml"


def get_cache_dir() -> Path:
    """Get the cache directory."""
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".cache"
    
    cache_dir = base / "fuva"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
