"""Archive file generators for testing upload validation."""

import struct
import zipfile
import io
from pathlib import Path
from typing import Optional

from .base import BaseGenerator, GeneratedFile


class CorruptZIP(BaseGenerator):
    """Generate a corrupt ZIP archive."""
    
    @property
    def name(self) -> str:
        return "corrupt_zip"
    
    @property
    def description(self) -> str:
        return "ZIP archive with corrupted CRC or structure"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate corrupted ZIP."""
        filename = "corrupt.zip"
        filepath = self.output_dir / filename
        
        zip_header = b"PK\x03\x04"
        
        local_header = struct.pack("<4sHHHHHIIIHH",
            b"PK\x03\x04",
            10,
            0,
            0,
            8,
            0,
            0,
            0,
            0,
            10,
            0
        )
        
        with open(filepath, "wb") as f:
            f.write(zip_header)
            f.write(local_header)
            f.write(b"testcontent")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"corruption_type": "truncated", "has_central_directory": False},
        )


class ZipSlipArchive(BaseGenerator):
    """Generate ZIP with directory traversal (zip slip)."""
    
    @property
    def name(self) -> str:
        return "zipslip_archive"
    
    @property
    def description(self) -> str:
        return "ZIP archive with path traversal files"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate ZIP with path traversal."""
        filename = "zipslip.zip"
        filepath = self.output_dir / filename
        
        files = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "test/../../../etc/shadow",
            "normal_file.txt",
        ]
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in files:
                content = f"Content of {file_path}".encode()
                zf.writestr(file_path, content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_path_traversal": True, "num_files": len(files)},
        )


class LargeArchive(BaseGenerator):
    """Generate a large ZIP archive."""
    
    def __init__(self, output_dir: Optional[Path] = None, num_files: int = 1000, file_size: int = 10000, cleanup: bool = False):
        super().__init__(output_dir, cleanup=cleanup)
        self.num_files = num_files
        self.file_size = file_size
    
    @property
    def name(self) -> str:
        return "large_archive"
    
    @property
    def description(self) -> str:
        return f"Large ZIP with {self.num_files} files, ~{self.file_size} bytes each"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate large ZIP archive."""
        filename = f"large_{self.num_files}_files.zip"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(self.num_files):
                content = b"X" * self.file_size
                zf.writestr(f"file_{i:04d}.txt", content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"num_files": self.num_files, "file_size": self.file_size},
        )


class EmptyArchive(BaseGenerator):
    """Generate an empty or nearly empty archive."""
    
    @property
    def name(self) -> str:
        return "empty_archive"
    
    @property
    def description(self) -> str:
        return "Empty ZIP archive"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate empty ZIP."""
        filename = "empty.zip"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w") as zf:
            pass
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"num_files": 0, "is_empty": True},
        )


class SymlinkArchive(BaseGenerator):
    """Generate ZIP with symbolic links."""
    
    @property
    def name(self) -> str:
        return "symlink_archive"
    
    @property
    def description(self) -> str:
        return "ZIP archive with symbolic link entries"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate ZIP with symlink."""
        filename = "symlink.zip"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w") as zf:
            zip_info = zipfile.ZipInfo("link_to_passwd")
            zip_info.external_attr = 0xA1ED0000
            
            zf.writestr(zip_info, "../../../etc/passwd")
            zf.writestr("normal.txt", "Just a normal file")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_symlink": True},
        )


class BombZIP(BaseGenerator):
    """Generate a ZIP bomb (highly compressed)."""
    
    @property
    def name(self) -> str:
        return "zip_bomb"
    
    @property
    def description(self) -> str:
        return "Highly compressed ZIP (ZIP bomb)"
    
    @property
    def file_type(self) -> str:
        return "zip"
    
    @property
    def mime_type(self) -> str:
        return "application/zip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate ZIP bomb."""
        filename = "zip_bomb.zip"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            data = b"X" * 1000
            
            for i in range(100):
                zf.writestr(f"data_{i:03d}.txt", data)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_zip_bomb": True, "compression_ratio": "high"},
        )
