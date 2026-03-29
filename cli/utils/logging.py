"""Colored logging utility with file and console output."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with ANSI color codes."""
    
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[34m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "SUCCESS": "\033[32m",
    }
    
    RESET = "\033[0m"
    
    def __init__(self, fmt: Optional[str] = None, use_colors: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors and sys.stdout.isatty():
            levelname = record.levelname
            if levelname == "SUCCESS":
                levelname = "INFO"
                record.levelname = "INFO"
            
            color = self.COLORS.get(levelname, "")
            record.levelname = f"{color}{levelname}{self.RESET}"
        
        return super().format(record)


class SimpleLogger:
    """Simple logger wrapper with colored console output and file logging."""
    
    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        use_colors: bool = True,
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.use_colors = use_colors and sys.stdout.isatty()
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        console_format = "%(asctime)s │ %(levelname)-8s │ %(message)s"
        console_formatter = ColoredFormatter(
            console_format,
            use_colors=self.use_colors
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setLevel(logging.DEBUG)
        
        file_format = "%(asctime)s │ %(name)s │ %(levelname)-8s │ %(message)s"
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str) -> None:
        self.logger.debug(msg)
    
    def info(self, msg: str) -> None:
        self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        self.logger.warning(msg)
    
    def error(self, msg: str) -> None:
        self.logger.error(msg)
    
    def critical(self, msg: str) -> None:
        self.logger.critical(msg)
    
    def success(self, msg: str) -> None:
        custom_level = logging.INFO + 1
        logging.addLevelName(custom_level, "SUCCESS")
        self.logger.log(custom_level, msg)
    
    def info_block(self, title: str, content: str = "") -> None:
        separator = "=" * 50
        self.logger.info(separator)
        self.logger.info(f"  {title}")
        if content:
            for line in content.split("\n"):
                self.logger.info(f"  {line}")
        self.logger.info(separator)
    
    def table(self, headers: list, rows: list) -> None:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        header_line = " | ".join(
            h.ljust(w) for h, w in zip(headers, col_widths)
        )
        separator = "-" * len(header_line)
        
        self.logger.info(separator)
        self.logger.info(header_line)
        self.logger.info(separator)
        
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(w) for cell, w in zip(row, col_widths)
            )
            self.logger.info(row_line)
        self.logger.info(separator)


_loggers = {}


def setup_logging(
    name: str = "fuva",
    log_dir: str = "logs",
    level: int = logging.INFO,
    use_colors: bool = True,
) -> SimpleLogger:
    """Setup and configure logging."""
    if name not in _loggers:
        _loggers[name] = SimpleLogger(
            name=name,
            log_dir=log_dir,
            log_level=level,
            use_colors=use_colors,
        )
    return _loggers[name]


def get_logger(name: str = "fuva") -> SimpleLogger:
    """Get a logger instance."""
    if name not in _loggers:
        return setup_logging(name)
    return _loggers[name]
