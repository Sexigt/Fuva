"""Extended generators for Office files and additional test cases."""

import zipfile
import io
import os
from pathlib import Path

from .base import BaseGenerator, GeneratedFile


class PPTMacro(BaseGenerator):
    """PowerPoint file with embedded macro."""
    
    def _generate(self) -> GeneratedFile:
        content = b"PK\x03\x04" + b"\x00" * 100
        content += b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vbaProject" Target="vbaProject.bin"/>'
        
        file_path = self.output_dir / "macro.pptm"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type="pptm",
            size=len(content),
            description="PowerPoint with embedded macro",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            category="document",
            metadata={"has_macro": True, "extension": ".pptm"},
        )


class XLSMBom(BaseGenerator):
    """Excel file with BOM and macro."""
    
    def _generate(self) -> GeneratedFile:
        content = b'\xef\xbb\xbfPK\x03\x04'
        content += b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        content += b'<vbaProject><zipIgnore/><zipFrom>xl/vbaProject.bin</zipFrom></vbaProject>'
        
        file_path = self.output_dir / "bom_macro.xlsb"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/vnd.ms-excel.sheet.binary.macroEnabled.12",
            category="document",
            metadata={"has_macro": True, "has_bom": True},
        )


class OfficeOXMLExternalEntity(BaseGenerator):
    """Office Open XML file with external entity."""
    
    def _generate(self) -> GeneratedFile:
        content = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE document [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>'''
        
        file_path = self.output_dir / "xxe_test.docx"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            category="document",
            metadata={"has_xxe": True},
        )


class WordWithEmbeddedHTML(BaseGenerator):
    """Word document with embedded HTML."""
    
    def _generate(self) -> GeneratedFile:
        content = b'''RTF
{\\htmltbl
{\\field{\\*\\fldinst{HYPERLINK "javascript:alert(1)"}}{\\fldrslt{Link}}}}
{\\colortbl
\\red0\\green0\\blue0;
\\red255\\green0\\blue0;}
'''
        
        file_path = self.output_dir / "embedded_html.doc"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/msword",
            category="document",
            metadata={"has_html_content": True, "has_script": True},
        )


class XZBomb(BaseGenerator):
    """XZ compression bomb."""
    
    def _generate(self) -> GeneratedFile:
        compressed = b'\xfd7zXZ\x00\x00\x04\xff\xff'
        compressed += b'\x00' * 100000
        
        file_path = self.output_dir / "xz_bomb.tar.xz"
        file_path.write_bytes(compressed)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(compressed),
            description="XZ compression bomb",
            mime_type="application/x-xz",
            category="archive",
            metadata={"is_xz_bomb": True},
        )


class NestedArchiveBomb(BaseGenerator):
    """Nested archive bomb."""
    
    def _generate(self) -> GeneratedFile:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(10):
                inner_buffer = io.BytesIO()
                with zipfile.ZipFile(inner_buffer, 'w', zipfile.ZIP_DEFLATED) as inner_zf:
                    inner_zf.writestr(f"level{i}.txt", "A" * 100000)
                zf.writestr(f"nested_{i}.zip", inner_buffer.getvalue())
        
        file_path = self.output_dir / "nested_bomb.zip"
        nested_content = buffer.getvalue()
        file_path.write_bytes(nested_content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(nested_content),
            description="Nested archive bomb",
            mime_type="application/zip",
            category="archive",
            metadata={"is_nested_bomb": True, "depth": 10},
        )


class DEFLATEBomb(BaseGenerator):
    """DEFLATE compression bomb."""
    
    def _generate(self) -> GeneratedFile:
        data = b'X' * 1000000
        compressed = b''
        
        import zlib
        compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
        compressed = compressor.compress(data)
        compressed += compressor.flush()
        
        file_path = self.output_dir / "deflate_bomb.zlib"
        deflate_content = compressed
        file_path.write_bytes(deflate_content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(deflate_content),
            description="DEFLATE compression bomb",
            mime_type="application/x-deflate",
            category="archive",
            metadata={"is_deflate_bomb": True},
        )


class SevenZipSolidArchive(BaseGenerator):
    """7z solid archive bomb."""
    
    def _generate(self) -> GeneratedFile:
        content = b'7z\xbc\xaf\x27\x1c'
        content += b'\x00' * 100000
        
        file_path = self.output_dir / "7z_bomb.7z"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/x-7z-compressed",
            category="archive",
            metadata={"is_7z_bomb": True},
        )


class BZ2Bomb(BaseGenerator):
    """BZ2 compression bomb."""
    
    def _generate(self) -> GeneratedFile:
        data = b'B' * 1000000
        
        import bz2
        bz2_content = bz2.compress(data, compresslevel=9)
        
        file_path = self.output_dir / "bz2_bomb.bz2"
        file_path.write_bytes(bz2_content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(bz2_content),
            description="BZ2 compression bomb",
            mime_type="application/x-bzip2",
            category="archive",
            metadata={"is_bz2_bomb": True},
        )


class LZ4Bomb(BaseGenerator):
    """LZ4 compression bomb."""
    
    def _generate(self) -> GeneratedFile:
        content = b'\x04\x22\x4d\x18'
        content += b'\x00' * 100000
        
        file_path = self.output_dir / "lz4_bomb.lz4"
        file_path.write_bytes(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/x-lz4",
            category="archive",
            metadata={"is_lz4_bomb": True},
        )


class WebShellArchive(BaseGenerator):
    """Archive containing web shell."""
    
    def _generate(self) -> GeneratedFile:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("shell.php", '<?php system($_GET["cmd"]);?>')
            zf.writestr("image.png", 'GIF89a<script>alert(1)</script>')
        
        file_path = self.output_dir / "webshell_archive.zip"
        webshell_content = buffer.getvalue()
        file_path.write_bytes(webshell_content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(webshell_content),
            description="Archive with web shell",
            mime_type="application/zip",
            category="archive",
            metadata={"has_webshell": True},
        )


class LargeJSONFile(BaseGenerator):
    """Large JSON file."""
    
    def _generate(self) -> GeneratedFile:
        content = '{"data": [' + ','.join(['{"id":%d,"value":"X"}' % i for i in range(10000)]) + ']}'
        
        file_path = self.output_dir / "large.json"
        file_path.write_text(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/json",
            category="document",
            metadata={"size": "large"},
        )


class XMLBomb(BaseGenerator):
    """XML bomb (billion laughs attack)."""
    
    def _generate(self) -> GeneratedFile:
        content = '''<?xml version="1.0"?>
<!DOCTYPE lolz [
<!ENTITY lol "lol">
<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<lolz>&lol3;</lolz>'''
        
        file_path = self.output_dir / "xml_bomb.xml"
        file_path.write_text(content)
        
        return GeneratedFile(
            name=file_path.name,
            path=file_path,
            file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
            size=len(content),
            description="Test file",
            mime_type="application/xml",
            category="document",
            metadata={"is_xml_bomb": True},
        )
