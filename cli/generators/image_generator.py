"""Image file generators for testing upload validation."""

import struct
import io
from pathlib import Path
from typing import Optional
import random

from .base import BaseGenerator, GeneratedFile


class CorruptPNG(BaseGenerator):
    """Generate a PNG with corrupted header/magic bytes."""
    
    @property
    def name(self) -> str:
        return "corrupt_png"
    
    @property
    def description(self) -> str:
        return "PNG file with corrupted magic bytes"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate corrupted PNG."""
        filename = "corrupt_header.png"
        filepath = self.output_dir / filename
        
        png_header = b"\x89PNG\r\n\x1a\n"
        corrupted_header = b"\x89PNG\r\n\x00\x00"
        
        with open(filepath, "wb") as f:
            f.write(corrupted_header)
            f.write(b"\x00" * 100)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"corruption_type": "header", "original_header": "corrupted"},
        )


class CorruptJPEG(BaseGenerator):
    """Generate a JPEG with corrupted data."""
    
    @property
    def name(self) -> str:
        return "corrupt_jpeg"
    
    @property
    def description(self) -> str:
        return "JPEG file with truncated/corrupted data"
    
    @property
    def file_type(self) -> str:
        return "jpg"
    
    @property
    def mime_type(self) -> str:
        return "image/jpeg"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate corrupted JPEG."""
        filename = "corrupt_jpeg.jpg"
        filepath = self.output_dir / filename
        
        jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        truncated = jpeg_header + b"\xff\xd9"
        
        with open(filepath, "wb") as f:
            f.write(truncated)
            f.write(b"\xff" * 50)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"corruption_type": "truncated", "has_eoi": True},
        )


class LargeMetadataImage(BaseGenerator):
    """Generate an image with excessively large metadata."""
    
    def __init__(self, output_dir: Optional[Path] = None, metadata_size: int = 100000, cleanup: bool = False):
        super().__init__(output_dir, cleanup=cleanup)
        self.metadata_size = metadata_size
    
    @property
    def name(self) -> str:
        return "large_metadata_image"
    
    @property
    def description(self) -> str:
        return f"PNG with large metadata chunk ({self.metadata_size} bytes)"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate PNG with large metadata."""
        filename = "large_metadata.png"
        filepath = self.output_dir / filename
        
        png_magic = b"\x89PNG\r\n\x1a\n"
        
        ihdr_chunk = struct.pack(">I", 13)
        ihdr_chunk += b"IHDR"
        ihdr_chunk += struct.pack(">IIBBBBB", 100, 100, 8, 2, 0, 0, 0)
        ihdr_crc = self._calculate_crc(b"IHDR" + struct.pack(">IIBBBBB", 100, 100, 8, 2, 0, 0, 0))
        ihdr_chunk += struct.pack(">I", ihdr_crc)
        
        large_data = b"\x00" * self.metadata_size
        tEXt_chunk = struct.pack(">I", self.metadata_size)
        tEXt_chunk += b"tEXt"
        tEXt_chunk += large_data
        tEXt_crc = self._calculate_crc(b"tEXt" + large_data)
        tEXt_chunk += struct.pack(">I", tEXt_crc)
        
        with open(filepath, "wb") as f:
            f.write(png_magic)
            f.write(ihdr_chunk)
            f.write(tEXt_chunk)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"metadata_size": self.metadata_size, "chunk_type": "tEXt"},
        )
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC32 for PNG chunks."""
        import zlib
        return zlib.crc32(data) & 0xFFFFFFFF


class WrongMIMEImage(BaseGenerator):
    """Generate a file with wrong MIME type in content."""
    
    @property
    def name(self) -> str:
        return "wrong_mime_image"
    
    @property
    def description(self) -> str:
        return "Image with intentionally wrong content but valid extension"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate file with wrong MIME content."""
        filename = "fake_image.png"
        filepath = self.output_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(b"This is not a PNG file, it's plain text!")
            f.write(b"\x00" * 100)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"content_type": "text", "extension": "png"},
        )


class EmptyImage(BaseGenerator):
    """Generate an empty (0 byte) file."""
    
    @property
    def name(self) -> str:
        return "empty_image"
    
    @property
    def description(self) -> str:
        return "Empty file with image extension"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate empty file."""
        filename = "empty.png"
        filepath = self.output_dir / filename
        
        filepath.touch()
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=0,
            description=self.description,
            category=self.category,
            metadata={"size": 0, "is_empty": True},
        )


class GiantImage(BaseGenerator):
    """Generate an image with extremely large dimensions."""
    
    def __init__(self, output_dir: Optional[Path] = None, width: int = 100000, height: int = 100000, cleanup: bool = False):
        super().__init__(output_dir, cleanup=cleanup)
        self.width = width
        self.height = height
    
    @property
    def name(self) -> str:
        return "giant_image"
    
    @property
    def description(self) -> str:
        return f"PNG with extreme dimensions {self.width}x{self.height}"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "image"
    
    def generate(self) -> GeneratedFile:
        """Generate PNG with giant dimensions."""
        filename = f"giant_{self.width}x{self.height}.png"
        filepath = self.output_dir / filename
        
        png_magic = b"\x89PNG\r\n\x1a\n"
        
        ihdr_chunk = struct.pack(">I", 13)
        ihdr_chunk += b"IHDR"
        ihdr_chunk += struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        ihdr_crc = self._calculate_crc(b"IHDR" + struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0))
        ihdr_chunk += struct.pack(">I", ihdr_crc)
        
        idat_data = b"\x00" * 1000
        idat_chunk = struct.pack(">I", len(idat_data))
        idat_chunk += b"IDAT"
        idat_chunk += idat_data
        idat_crc = self._calculate_crc(b"IDAT" + idat_data)
        idat_chunk += struct.pack(">I", idat_crc)
        
        iend_chunk = struct.pack(">I", 0)
        iend_chunk += b"IEND"
        iend_chunk += struct.pack(">I", 0xAE426082)
        
        with open(filepath, "wb") as f:
            f.write(png_magic)
            f.write(ihdr_chunk)
            f.write(idat_chunk)
            f.write(iend_chunk)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"width": self.width, "height": self.height},
        )
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC32 for PNG chunks."""
        import zlib
        return zlib.crc32(data) & 0xFFFFFFFF
