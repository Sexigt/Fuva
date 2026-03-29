"""Response analyzer for HTTP upload responses."""

import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..generators.base import GeneratedFile
from ..utils.logging import get_logger


logger = get_logger("analyzer")


@dataclass
class UploadResult:
    """Result of a single upload test."""
    file: GeneratedFile
    success: bool
    status_code: int
    response_time: float
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    error: Optional[str] = None
    ui_error: Optional[str] = None
    validation_passed: Optional[bool] = None
    matched_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file": self.file.to_dict(),
            "success": self.success,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "headers": self.headers,
            "body": self.body[:1000] if self.body else "",
            "error": self.error,
            "ui_error": self.ui_error,
            "validation_passed": self.validation_passed,
            "matched_patterns": self.matched_patterns,
        }


class ResponseAnalyzer:
    """Analyze HTTP responses from file uploads."""
    
    DEFAULT_PATTERNS = {
        "sql_injection": [
            r"SQL syntax.*MySQL",
            r"Warning.*mysql_",
            r"MySQLSyntaxErrorException",
            r"valid MySQL result",
        ],
        "path_traversal": [
            r"\.\./",
            r"\.\.\\",
            r"Directory.*not found",
            r"No such file or directory",
        ],
        "xss": [
            r"<script>",
            r"alert\(",
            r"onerror=",
            r"onload=",
        ],
        "command_injection": [
            r"sh: .*: not found",
            r"Warning.*system\(\)",
            r"exec\(\)",
            r"passthru\(",
        ],
        "error_disclosure": [
            r"Stack trace:",
            r"at .*\(",
            r"Exception in thread",
            r"Fatal error:",
            r"Parse error:",
            r"Warning:",
        ],
    }
    
    def __init__(
        self,
        target_url: str,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        auth_cookie: Optional[Dict[str, str]] = None,
        workers: int = 1,
    ):
        self.target_url = target_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.proxy = proxy
        self.custom_headers = headers or {}
        self.auth_token = auth_token
        self.auth_cookie = auth_cookie or {}
        self.workers = max(1, workers)
        
        self.session = session or self._create_session()
        self.results: List[UploadResult] = []
        self._results_lock = threading.Lock()
        self._progress_callback: Optional[Callable] = None
        self._rate_limit_detected = False
        self._current_delay = 0.5
        self._rate_limit_count = 0
    
    def _check_rate_limit(self, response) -> bool:
        """Check if response indicates rate limiting."""
        if response.status_code == 429:
            return True
        
        retry_after = response.headers.get("Retry-After") or response.headers.get("X-RateLimit-Reset")
        if retry_after:
            try:
                self._current_delay = float(retry_after) + 1
            except ValueError:
                self._current_delay = 60
        
        ratelimit_remaining = response.headers.get("X-RateLimit-Remaining", "999")
        try:
            if int(ratelimit_remaining) < 5:
                return True
        except ValueError:
            pass
        
        return False
    
    def get_current_delay(self) -> float:
        """Get current recommended delay between requests."""
        return self._current_delay
    
    def is_rate_limited(self) -> bool:
        """Check if rate limiting has been detected."""
        return self._rate_limit_detected
    
    def _create_session(self) -> requests.Session:
        """Create a configured session with retry logic."""
        session = requests.Session()
        
        if self.max_retries > 0:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.retry_delay,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        
        if self.proxy:
            session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }
        
        for key, value in self.custom_headers.items():
            session.headers.update({key: value})
        
        return session
    
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    def analyze_response(self, response: requests.Response) -> Dict[str, Any]:
        """Analyze an HTTP response."""
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:5000],
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": response.headers.get("Content-Length", ""),
            "server": response.headers.get("Server", ""),
        }
    
    def _match_patterns(self, body: str) -> List[str]:
        """Match response body against vulnerability patterns."""
        matched = []
        for pattern_name, patterns in self.DEFAULT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    matched.append(f"{pattern_name}: {pattern}")
        return matched
    
    def upload_file(
        self,
        file: GeneratedFile,
        form_field: str = "file",
        additional_data: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """Upload a single file and analyze the response."""
        start_time = time.time()
        file_handle = None
        
        try:
            file_handle = open(file.path, "rb")
            files = {form_field: (file.name, file_handle, file.mime_type)}
            data = additional_data or {}
            
            if self.auth_token:
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            for key, value in self.auth_cookie.items():
                self.session.cookies.set(key, value)
            
            response = self.session.post(
                self.target_url,
                files=files,
                data=data,
                timeout=self.timeout,
                allow_redirects=False,
            )
            
            response_time = time.time() - start_time
            
            if self._check_rate_limit(response):
                self._rate_limit_count += 1
                if self._rate_limit_count >= 3:
                    self._rate_limit_detected = True
                    self._current_delay = min(self._current_delay * 2, 30)
                    logger.warning(f"Rate limit detected! Backing off to {self._current_delay}s delay")
            
            matched_patterns = self._match_patterns(response.text)
            
            result = UploadResult(
                file=file,
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_time=response_time,
                headers=dict(response.headers),
                body=response.text[:5000],
                matched_patterns=matched_patterns,
            )
            
            logger.info(
                f"Uploaded {file.name}: {response.status_code} "
                f"({response_time:.2f}s)"
            )
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            result = UploadResult(
                file=file,
                success=False,
                status_code=0,
                response_time=response_time,
                error="Request timeout",
            )
            logger.error(f"Timeout uploading {file.name}")
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            result = UploadResult(
                file=file,
                success=False,
                status_code=0,
                response_time=response_time,
                error=str(e),
            )
            logger.error(f"Error uploading {file.name}: {e}")
        
        except Exception as e:
            response_time = time.time() - start_time
            result = UploadResult(
                file=file,
                success=False,
                status_code=0,
                response_time=response_time,
                error=f"Unexpected error: {e}",
            )
            logger.error(f"Unexpected error uploading {file.name}: {e}")
        
        finally:
            if file_handle:
                try:
                    file_handle.close()
                except Exception:
                    pass
        
        with self._results_lock:
            self.results.append(result)
        
        return result
    
    def _upload_worker(
        self,
        file: GeneratedFile,
        form_field: str,
        additional_data: Optional[Dict[str, str]],
        thread_local: threading.local,
    ) -> UploadResult:
        """Worker function for threaded uploads."""
        if not hasattr(thread_local, 'session'):
            thread_local.session = self._create_session()
        
        start_time = time.time()
        file_handle = None
        
        try:
            file_handle = open(file.path, "rb")
            files = {form_field: (file.name, file_handle, file.mime_type)}
            data = additional_data or {}
            
            if self.auth_token:
                thread_local.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            for key, value in self.auth_cookie.items():
                thread_local.session.cookies.set(key, value)
            
            response = thread_local.session.post(
                self.target_url,
                files=files,
                data=data,
                timeout=self.timeout,
                allow_redirects=False,
            )
            
            response_time = time.time() - start_time
            matched_patterns = self._match_patterns(response.text)
            
            result = UploadResult(
                file=file,
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_time=response_time,
                headers=dict(response.headers),
                body=response.text[:5000],
                matched_patterns=matched_patterns,
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            result = UploadResult(
                file=file,
                success=False,
                status_code=0,
                response_time=response_time,
                error=str(e),
            )
        
        finally:
            if file_handle:
                try:
                    file_handle.close()
                except Exception:
                    pass
        
        return result
    
    def run_upload_tests(
        self,
        files: List[GeneratedFile],
        delay: float = 0,
    ) -> List[UploadResult]:
        """Run upload tests for multiple files."""
        logger.info(f"Starting upload tests to {self.target_url}")
        logger.info(f"Total files to test: {len(files)}, Workers: {self.workers}")
        
        if self.workers > 1:
            self.results = self._run_concurrent(files, delay)
        else:
            self.results = self._run_sequential(files, delay)
        
        self._log_summary()
        return self.results
    
    def _run_sequential(
        self,
        files: List[GeneratedFile],
        delay: float,
    ) -> List[UploadResult]:
        """Run uploads sequentially."""
        results = []
        
        for i, file in enumerate(files, 1):
            if self._progress_callback:
                self._progress_callback(i, len(files))
            
            logger.info(f"Testing {i}/{len(files)}: {file.name}")
            result = self.upload_file(file)
            results.append(result)
            
            if delay > 0 and i < len(files):
                time.sleep(delay)
        
        return results
    
    def _run_concurrent(
        self,
        files: List[GeneratedFile],
        delay: float,
    ) -> List[UploadResult]:
        """Run uploads concurrently."""
        results = []
        completed = 0
        thread_local = threading.local()
        
        def worker(file):
            nonlocal completed
            result = self._upload_worker(file, "file", {}, thread_local)
            
            with self._results_lock:
                completed += 1
                if self._progress_callback:
                    self._progress_callback(completed, len(files))
            
            return result
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(worker, f): f for f in files}
            
            for future in as_completed(futures):
                file = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Uploaded {file.name}: {result.status_code}")
                except Exception as e:
                    logger.error(f"Error uploading {file.name}: {e}")
        
        return results
    
    def _log_summary(self) -> None:
        """Log test summary."""
        if not self.results:
            return
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        avg_time = sum(r.response_time for r in self.results) / total
        
        status_codes: Dict[int, int] = {}
        for r in self.results:
            status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1
        
        patterns_found = {}
        for r in self.results:
            for p in r.matched_patterns:
                patterns_found[p] = patterns_found.get(p, 0) + 1
        
        logger.info_block("Upload Test Summary", f"""Total: {total}
Successful: {successful}
Failed: {failed}
Average Response Time: {avg_time:.3f}s
""")
        
        logger.info("Status Code Distribution:")
        for code, count in sorted(status_codes.items()):
            logger.info(f"  {code}: {count}")
        
        if patterns_found:
            logger.warning("Vulnerability Patterns Found:")
            for pattern, count in patterns_found.items():
                logger.warning(f"  {pattern}: {count}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from results."""
        if not self.results:
            return {}
        
        status_codes = [r.status_code for r in self.results]
        response_times = [r.response_time for r in self.results]
        
        return {
            "total": len(self.results),
            "successful": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "status_code_distribution": {
                str(k): v for k, v in self._count_items(status_codes).items()
            },
            "matched_patterns": self._count_items(
                p for r in self.results for p in r.matched_patterns
            ),
        }
    
    def _count_items(self, items) -> Dict[Any, int]:
        """Count occurrences in list."""
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts
