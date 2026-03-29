#!/usr/bin/env python3
"""
File Upload Validation Analyzer - CLI Tool

A comprehensive tool for testing and analyzing file upload validation
on web servers. Generates various test files, uploads them, and analyzes
the responses to identify security issues and validation gaps.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .config import Config
from .generators import (
    CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage, EmptyImage,
    GiantImage, EdgeCasePDF, MalformedSVG, LargePDF, PDFWithJavaScript,
    RTFWithEmbedded, CorruptZIP, ZipSlipArchive, LargeArchive, EmptyArchive,
    SymlinkArchive, BombZIP, TextInBinary, DoubleExtensionFile, NullByteInjection,
    PolyglotFile, HTMLinImage, LongFilename, UnicodeFilenames, FakeEXE, FakeELF,
    MacroEnabledDOCX, MacroEnabledXLSX, ODTFile, GzipBomb, SevenZipArchive, RARArchive,
    GeneratedFile,
)
from .analyzers import (
    ResponseAnalyzer,
    ValidationComparator,
    AnomalyDetector,
    UploadResult,
)
from .reporting import HTMLReportGenerator, JSONReportGenerator
from .utils.logging import setup_logging, get_logger


logger: Optional[object] = None


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="fuva",
        description="File Upload Validation Analyzer - Test file upload security",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test files
  fuva generate -o test_files
  
  # Basic upload test
  fuva run https://example.com/upload
  
  # Concurrent uploads (10 workers)
  fuva run https://example.com/upload --workers 10
  
  # With authentication
  fuva run https://example.com/upload --token YOUR_TOKEN
  
  # Through proxy
  fuva run https://example.com/upload --proxy http://localhost:8080
  
  # With retries
  fuva run https://example.com/upload --retries 3 --retry-delay 2
        """
    )
    
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Generate test files")
    gen_parser.add_argument("-o", "--output", default="test_files", help="Output directory")
    gen_parser.add_argument(
        "--categories",
        nargs="+",
        choices=["image", "document", "archive", "mixed", "executable", "all"],
        default=["all"],
        help="File categories to generate"
    )
    
    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run upload tests")
    run_parser.add_argument("target_url", nargs="?", default="", help="Target upload URL")
    run_parser.add_argument("-o", "--output", default="reports", help="Output directory")
    run_parser.add_argument("--html", action="store_true", help="Generate HTML report")
    run_parser.add_argument("--json", action="store_true", help="Generate JSON report")
    run_parser.add_argument("--timeout", type=int, default=30, help="Request timeout")
    run_parser.add_argument("--delay", type=float, default=0, help="Delay between requests")
    run_parser.add_argument("--workers", type=int, default=1, help="Concurrent workers")
    run_parser.add_argument("--retries", type=int, default=0, help="Max retries on failure")
    run_parser.add_argument("--retry-delay", type=float, default=1.0, help="Delay between retries")
    run_parser.add_argument("--form-field", default="file", help="Form field name")
    run_parser.add_argument("--proxy", help="Proxy URL (e.g., http://localhost:8080)")
    run_parser.add_argument("--header", action="append", help="Custom headers (key:value)")
    run_parser.add_argument("--token", help="Bearer token for authentication")
    run_parser.add_argument("--cookie", action="append", help="Cookies (key=value)")
    
    # Compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare API vs UI validation")
    compare_parser.add_argument("api_url", help="API endpoint URL")
    compare_parser.add_argument("ui_url", help="UI upload form URL")
    
    return parser


def generate_test_files(output_dir: str, categories: List[str]) -> List[GeneratedFile]:
    """Generate test files for upload testing."""
    global logger
    if logger is None:
        logger = setup_logging()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating test files in {output_path}")
    
    files: List[GeneratedFile] = []
    generator_classes = []
    
    if "all" in categories or "image" in categories:
        generator_classes.extend([
            CorruptPNG, CorruptJPEG, LargeMetadataImage, WrongMIMEImage,
            EmptyImage, GiantImage,
        ])
    
    if "all" in categories or "document" in categories:
        generator_classes.extend([
            EdgeCasePDF, MalformedSVG, LargePDF, PDFWithJavaScript,
            RTFWithEmbedded, MacroEnabledDOCX, MacroEnabledXLSX, ODTFile,
        ])
    
    if "all" in categories or "archive" in categories:
        generator_classes.extend([
            CorruptZIP, ZipSlipArchive, LargeArchive, EmptyArchive,
            SymlinkArchive, BombZIP, GzipBomb, SevenZipArchive, RARArchive,
        ])
    
    if "all" in categories or "mixed" in categories:
        generator_classes.extend([
            TextInBinary, DoubleExtensionFile, NullByteInjection,
            PolyglotFile, HTMLinImage, UnicodeFilenames,
        ])
    
    if "all" in categories or "executable" in categories:
        generator_classes.extend([
            FakeEXE, FakeELF,
        ])
    
    for generator_class in generator_classes:
        try:
            with generator_class(output_dir=output_path, cleanup=False) as generator:
                generated_file = generator.generate()
                files.append(generated_file)
                logger.success(f"Generated: {generated_file.name}")
        except Exception as e:
            logger.error(f"Error generating file with {generator_class.__name__}: {e}")
    
    logger.info(f"Generated {len(files)} test files")
    return files


def run_upload_tests(
    target_url: str,
    output_dir: str = "reports",
    timeout: int = 30,
    delay: float = 0,
    workers: int = 1,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    form_field: str = "file",
    generate_html: bool = True,
    generate_json: bool = True,
    proxy: Optional[str] = None,
    headers: Optional[List[str]] = None,
    token: Optional[str] = None,
    cookies: Optional[List[str]] = None,
) -> tuple:
    """Run upload tests against target URL."""
    global logger
    if logger is None:
        logger = setup_logging()
    
    logger.info(f"Starting upload tests against {target_url}")
    logger.info(f"Workers: {workers}, Timeout: {timeout}s, Retries: {max_retries}")
    
    config = Config(
        target_url=target_url,
        output_dir=output_dir,
        timeout=timeout,
    )
    
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)
    
    header_dict = {}
    if headers:
        for h in headers:
            if ":" in h:
                k, v = h.split(":", 1)
                header_dict[k.strip()] = v.strip()
    
    cookie_dict = {}
    if cookies:
        for c in cookies:
            if "=" in c:
                k, v = c.split("=", 1)
                cookie_dict[k.strip()] = v.strip()
    
    logger.info("Generating test files...")
    test_files = generate_test_files(str(config.temp_dir), ["all"])
    
    logger.info("Running upload tests...")
    analyzer = ResponseAnalyzer(
        target_url=target_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        proxy=proxy,
        headers=header_dict,
        auth_token=token,
        auth_cookie=cookie_dict,
        workers=workers,
    )
    
    results = analyzer.run_upload_tests(test_files, delay=delay)
    
    logger.info("Detecting anomalies...")
    anomaly_detector = AnomalyDetector()
    anomalies = anomaly_detector.detect_anomalies(results)
    
    logger.info("Comparing API vs UI validation...")
    comparator = ValidationComparator()
    gaps = comparator.compare_api_ui(results)
    
    html_path = None
    json_path = None
    
    html_generator = HTMLReportGenerator(output_dir)
    json_generator = JSONReportGenerator(output_dir)
    
    metadata = {
        "timeout": timeout,
        "delay": delay,
        "workers": workers,
        "max_retries": max_retries,
        "proxy": proxy,
        "form_field": form_field,
    }
    
    if generate_html or (not generate_json):
        html_path = html_generator.generate_html_report(
            results=results,
            gaps=gaps,
            anomalies=anomalies,
            target_url=target_url,
            metadata=metadata,
        )
    
    if generate_json:
        json_path = json_generator.generate_json_report(
            results=results,
            gaps=gaps,
            anomalies=anomalies,
            target_url=target_url,
            metadata=metadata,
        )
    
    return results, gaps, anomalies, html_path, json_path


def main() -> None:
    """Main entry point."""
    global logger
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    logger = setup_logging(name="fuva", log_dir="logs")
    
    if args.command == "generate":
        files = generate_test_files(args.output, args.categories)
        logger.success(f"Generated {len(files)} files in {args.output}")
    
    elif args.command == "run":
        if not args.target_url:
            logger.error("target_url is required")
            sys.exit(1)
        
        results, gaps, anomalies, html_path, json_path = run_upload_tests(
            target_url=args.target_url,
            output_dir=args.output,
            timeout=args.timeout,
            delay=args.delay,
            workers=args.workers,
            max_retries=args.retries,
            retry_delay=args.retry_delay,
            form_field=args.form_field,
            generate_html=args.html or not args.json,
            generate_json=args.json,
            proxy=args.proxy,
            headers=args.header,
            token=args.token,
            cookies=args.cookie,
        )
        
        logger.success(f"Tests complete!")
        logger.info(f"Results: {len(results)} uploads tested")
        logger.info(f"Anomalies: {len(anomalies)} found")
        logger.info(f"Validation gaps: {len(gaps)} found")
        
        if html_path:
            logger.success(f"HTML report: {html_path}")
        if json_path:
            logger.success(f"JSON report: {json_path}")
    
    elif args.command == "compare":
        logger.info(f"Comparing API ({args.api_url}) vs UI ({args.ui_url})")
        logger.warning("Compare command not fully implemented yet")


if __name__ == "__main__":
    main()
