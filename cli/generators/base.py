"""Base generator class for test files."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import shutil


@dataclass
class GeneratedFile:
    """Represents a generated test file."""
    name: str
    path: Path
    file_type: str
    mime_type: str
    size: int
    description: str
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def cleanup(self) -> None:
        """Remove the generated file."""
        if self.path.exists():
            self.path.unlink()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": str(self.path),
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "size": self.size,
            "description": self.description,
            "category": self.category,
            "metadata": self.metadata,
        }


class BaseGenerator(ABC):
    """Abstract base class for file generators."""
    
    def __init__(self, output_dir: Optional[Path] = None, cleanup: bool = False):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to save generated files. If None, uses temp dir.
            cleanup: If True, clean up generated files after context exit.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = Path(tempfile.mkdtemp(prefix="fuva_gen_"))
        
        self._temp_files = []
        self._cleanup = cleanup
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Generator name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Generator description."""
        pass
    
    @property
    @abstractmethod
    def file_type(self) -> str:
        """Expected file type (e.g., 'png', 'pdf', 'zip')."""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """Expected MIME type."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Category (e.g., 'image', 'document', 'archive', 'mixed')."""
        pass
    
    @abstractmethod
    def generate(self) -> GeneratedFile:
        """Generate the test file."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get generator metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "category": self.category,
        }
    
    def cleanup_all(self) -> None:
        """Clean up only temporary files that were tracked."""
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cleanup:
            self.cleanup_all()
        return False
