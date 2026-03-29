"""Mixed file generators for testing upload validation."""

import io
from pathlib import Path
from typing import Optional
import struct
import zipfile

from .base import BaseGenerator, GeneratedFile


class TextInBinary(BaseGenerator):
    """Generate file with text embedded in binary data."""
    
    @property
    def name(self) -> str:
        return "text_in_binary"
    
    @property
    def description(self) -> str:
        return "PNG file with embedded text content"
    
    @property
    def file_type(self) -> str:
        return "png"
    
    @property
    def mime_type(self) -> str:
        return "image/png"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate file with text in binary."""
        filename = "text_in_png.png"
        filepath = self.output_dir / filename
        
        png_header = b"\x89PNG\r\n\x1a\n"
        
        with open(filepath, "wb") as f:
            f.write(png_header)
            f.write(b"This is not a real PNG file. It's text embedded in binary!")
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
            metadata={"has_embedded_text": True},
        )


class DoubleExtensionFile(BaseGenerator):
    """Generate file with double extension (bypass)."""
    
    @property
    def name(self) -> str:
        return "double_extension"
    
    @property
    def description(self) -> str:
        return "File with double extension (e.g., file.txt.exe)"
    
    @property
    def file_type(self) -> str:
        return "txt"
    
    @property
    def mime_type(self) -> str:
        return "text/plain"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate file with double extension."""
        filename = "malicious.txt.exe"
        filepath = self.output_dir / filename
        
        content = b"MZ" + b"\x00" * 100 + b"This looks like an EXE but is a text file"
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_double_extension": True, "fake_extension": "txt", "real_content": "exe"},
        )


class NullByteInjection(BaseGenerator):
    """Generate file with null byte injection."""
    
    @property
    def name(self) -> str:
        return "null_byte_injection"
    
    @property
    def description(self) -> str:
        return "File with null byte in filename"
    
    @property
    def file_type(self) -> str:
        return "php"
    
    @property
    def mime_type(self) -> str:
        return "application/x-php"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate file with null byte."""
        filename = "shell.php\x00.jpg"
        filepath = self.output_dir / "shell_php.jpg"
        
        php_content = b"""<?php
system($_GET['cmd']);
?>"""
        
        with open(filepath, "wb") as f:
            f.write(php_content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_null_byte": True, "content_type": "php"},
        )


class PolyglotFile(BaseGenerator):
    """Generate polyglot file (valid in multiple formats)."""
    
    @property
    def name(self) -> str:
        return "polyglot_file"
    
    @property
    def description(self) -> str:
        return "File that is valid as both image and archive"
    
    @property
    def file_type(self) -> str:
        return "jpg"
    
    @property
    def mime_type(self) -> str:
        return "image/jpeg"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate polyglot file."""
        filename = "polyglot.jpg"
        filepath = self.output_dir / filename
        
        jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        zip_start = b"PK\x03\x04"
        
        with open(filepath, "wb") as f:
            f.write(jpeg_header)
            f.write(b"\xff" * 100)
            f.write(zip_start)
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
            metadata={"polyglot_type": "jpeg_zip", "has_multiple_signatures": True},
        )


class HTMLinImage(BaseGenerator):
    """Generate image file with embedded HTML/JS."""
    
    @property
    def name(self) -> str:
        return "html_in_image"
    
    @property
    def description(self) -> str:
        return "GIF with embedded HTML/JavaScript"
    
    @property
    def file_type(self) -> str:
        return "gif"
    
    @property
    def mime_type(self) -> str:
        return "image/gif"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate GIF with embedded HTML."""
        filename = "html_gif.gif"
        filepath = self.output_dir / filename
        
        gif_header = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff"
        html_content = b'<script>alert("XSS")</script>'
        
        with open(filepath, "wb") as f:
            f.write(gif_header)
            f.write(b"\x00" * 100)
            f.write(html_content)
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
            metadata={"has_html_content": True, "has_script": True},
        )


class LongFilename(BaseGenerator):
    """Generate file with extremely long filename."""
    
    def __init__(self, output_dir: Optional[Path] = None, name_length: int = 1000, cleanup: bool = False):
        super().__init__(output_dir, cleanup=cleanup)
        self.name_length = name_length
    
    @property
    def name(self) -> str:
        return "long_filename"
    
    @property
    def description(self) -> str:
        return f"File with very long filename ({self.name_length} chars)"
    
    @property
    def file_type(self) -> str:
        return "txt"
    
    @property
    def mime_type(self) -> str:
        return "text/plain"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate file with long filename."""
        long_name = "a" * self.name_length + ".txt"
        filepath = self.output_dir / long_name
        
        with open(filepath, "wb") as f:
            f.write(b"Test content")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=long_name,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"filename_length": self.name_length},
        )


class UnicodeFilenames(BaseGenerator):
    """Generate file with Unicode characters in filename."""
    
    @property
    def name(self) -> str:
        return "unicode_filename"
    
    @property
    def description(self) -> str:
        return "File with Unicode characters in filename"
    
    @property
    def file_type(self) -> str:
        return "txt"
    
    @property
    def mime_type(self) -> str:
        return "text/plain"
    
    @property
    def category(self) -> str:
        return "mixed"
    
    def generate(self) -> GeneratedFile:
        """Generate file with Unicode filename."""
        import unicodedata
        filename = "malicious_\u202e_exe.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(b"MZ fake executable content")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_unicode": True, "has_rtl_override": "\u202e" in filename},
        )
