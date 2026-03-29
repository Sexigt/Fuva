"""Executable and binary file generators for testing."""

import struct
import io
from pathlib import Path
from typing import Optional
import zipfile
import shutil

from .base import BaseGenerator, GeneratedFile


class FakeEXE(BaseGenerator):
    """Generate a fake PE executable (for double extension testing)."""
    
    @property
    def name(self) -> str:
        return "fake_exe"
    
    @property
    def description(self) -> str:
        return "File that looks like an executable"
    
    @property
    def file_type(self) -> str:
        return "exe"
    
    @property
    def mime_type(self) -> str:
        return "application/x-msdownload"
    
    @property
    def category(self) -> str:
        return "executable"
    
    def generate(self) -> GeneratedFile:
        """Generate fake EXE."""
        filename = "document.exe"
        filepath = self.output_dir / filename
        
        pe_header = b"MZ" + b"\x90" * 58
        pe_header += struct.pack("<I", 64)
        pe_header += b"\x00" * 16
        pe_header += b"This is not a real executable, it's a text file with .exe extension!"
        
        with open(filepath, "wb") as f:
            f.write(pe_header)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_fake_exe": True},
        )


class FakeELF(BaseGenerator):
    """Generate a fake ELF executable (for Linux testing)."""
    
    @property
    def name(self) -> str:
        return "fake_elf"
    
    @property
    def description(self) -> str:
        return "File that looks like an ELF binary"
    
    @property
    def file_type(self) -> str:
        return "elf"
    
    @property
    def mime_type(self) -> str:
        return "application/x-executable"
    
    @property
    def category(self) -> str:
        return "executable"
    
    def generate(self) -> GeneratedFile:
        """Generate fake ELF."""
        filename = "backup.elf"
        filepath = self.output_dir / filename
        
        elf_header = b"\x7fELF"
        elf_header += b"\x02\x01\x01\x00"
        elf_header += b"\x00" * 12
        elf_header += b"This is not a real ELF binary!"
        
        with open(filepath, "wb") as f:
            f.write(elf_header)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_fake_elf": True},
        )


class MacroEnabledDOCX(BaseGenerator):
    """Generate a DOCX file (Office Open XML)."""
    
    @property
    def name(self) -> str:
        return "docx_file"
    
    @property
    def description(self) -> str:
        return "Microsoft Word document"
    
    @property
    def file_type(self) -> str:
        return "docx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate DOCX file."""
        filename = "report.docx"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
            
            zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")
            
            zf.writestr("word/document.xml", """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Test Document</w:t></w:r></w:p>
</w:body>
</w:document>""")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"office_format": "docx"},
        )


class MacroEnabledXLSX(BaseGenerator):
    """Generate an XLSX file (Office Open XML)."""
    
    @property
    def name(self) -> str:
        return "xlsx_file"
    
    @property
    def description(self) -> str:
        return "Microsoft Excel spreadsheet"
    
    @property
    def file_type(self) -> str:
        return "xlsx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate XLSX file."""
        filename = "data.xlsx"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
</Types>""")
            
            zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheets><sheet name="Sheet1" sheetId="1"/></sheets>
</workbook>""")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"office_format": "xlsx"},
        )


class ODTFile(BaseGenerator):
    """Generate an ODT file (OpenDocument Text)."""
    
    @property
    def name(self) -> str:
        return "odt_file"
    
    @property
    def description(self) -> str:
        return "OpenDocument Text document"
    
    @property
    def file_type(self) -> str:
        return "odt"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.oasis.opendocument.text"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate ODT file."""
        filename = "document.odt"
        filepath = self.output_dir / filename
        
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
            zf.writestr("content.xml", """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">
<office:body><office:text><text:p>Test Document</text:p></office:text></office:body>
</office:document>""")
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"office_format": "odt"},
        )


class GzipBomb(BaseGenerator):
    """Generate a gzip bomb (highly compressed)."""
    
    @property
    def name(self) -> str:
        return "gzip_bomb"
    
    @property
    def description(self) -> str:
        return "Highly compressed gzip archive"
    
    @property
    def file_type(self) -> str:
        return "gz"
    
    @property
    def mime_type(self) -> str:
        return "application/gzip"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate gzip bomb."""
        import gzip
        
        filename = "data.gz"
        filepath = self.output_dir / filename
        
        with gzip.open(filepath, "wb", compresslevel=9) as gz:
            data = b"X" * 10000
            for _ in range(100):
                gz.write(data)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_compression_bomb": True},
        )


class SevenZipArchive(BaseGenerator):
    """Generate a 7z format archive (simplified)."""
    
    @property
    def name(self) -> str:
        return "seven_zip"
    
    @property
    def description(self) -> str:
        return "7z archive header"
    
    @property
    def file_type(self) -> str:
        return "7z"
    
    @property
    def mime_type(self) -> str:
        return "application/x-7z-compressed"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate 7z header."""
        filename = "archive.7z"
        filepath = self.output_dir / filename
        
        seven_zip_header = b"7z\xbc\xaf'\x1e"
        seven_zip_header += b"\x00" * 100
        
        with open(filepath, "wb") as f:
            f.write(seven_zip_header)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_7z_header": True},
        )


class RARArchive(BaseGenerator):
    """Generate a RAR format archive (simplified)."""
    
    @property
    def name(self) -> str:
        return "rar_archive"
    
    @property
    def description(self) -> str:
        return "RAR archive header"
    
    @property
    def file_type(self) -> str:
        return "rar"
    
    @property
    def mime_type(self) -> str:
        return "application/x-rar-compressed"
    
    @property
    def category(self) -> str:
        return "archive"
    
    def generate(self) -> GeneratedFile:
        """Generate RAR header."""
        filename = "archive.rar"
        filepath = self.output_dir / filename
        
        rar_header = b"Rar!\x1a\x07\x01\x00"
        rar_header += b"\x00" * 100
        
        with open(filepath, "wb") as f:
            f.write(rar_header)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"is_rar_header": True},
        )
