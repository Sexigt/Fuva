"""SQLite database for persistent storage."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class Database:
    """SQLite database handler with in-memory storage."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._conn = None
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                target_url TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                total_tests INTEGER DEFAULT 0,
                accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0,
                anomalies INTEGER DEFAULT 0,
                gaps INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                config TEXT,
                html_report TEXT,
                json_report TEXT
            );
            
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_category TEXT,
                mime_type TEXT,
                status_code INTEGER,
                success INTEGER,
                response_time REAL,
                error_message TEXT,
                response_body TEXT,
                headers TEXT,
                accepted INTEGER,
                rejected INTEGER,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
            
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_name TEXT,
                evidence TEXT,
                recommendation TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
            
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                target_url TEXT,
                timeout INTEGER DEFAULT 30,
                delay REAL DEFAULT 0,
                workers INTEGER DEFAULT 1,
                max_retries INTEGER DEFAULT 0,
                form_field TEXT DEFAULT 'file',
                generator_types TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_results_run ON results(run_id);
            CREATE INDEX IF NOT EXISTS idx_anomalies_run ON anomalies(run_id);
        """)
    
    def create_run(self, run_id: str, target_url: str, config: Dict[str, Any]) -> str:
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO runs (id, target_url, status, config, created_at) 
               VALUES (?, ?, 'pending', ?, ?)""",
            (run_id, target_url, json.dumps(config), datetime.now().isoformat())
        )
        return run_id
    
    def update_run(self, run_id: str, **kwargs):
        fields = []
        values = []
        for key, value in kwargs.items():
            if key == "config":
                fields.append("config = ?")
                values.append(json.dumps(value))
            elif key in ("html_report", "json_report"):
                fields.append(f"{key} = ?")
                values.append(value)
            else:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            values.append(run_id)
            conn = self._get_connection()
            conn.execute(f"UPDATE runs SET {', '.join(fields)} WHERE id = ?", values)
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row:
            result = dict(row)
            result["run_id"] = result["id"]
            return result
        return None
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        results = [dict(row) for row in rows]
        for r in results:
            r["run_id"] = r["id"]
        return results
    
    def delete_run(self, run_id: str):
        conn = self._get_connection()
        conn.execute("DELETE FROM anomalies WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM results WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    
    def save_result(self, run_id: str, result: Dict[str, Any]):
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO results 
               (run_id, file_name, file_category, mime_type, status_code, success, 
                response_time, error_message, response_body, headers, accepted, rejected)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, result.get("file_name"), result.get("file_category"),
                result.get("mime_type"), result.get("status_code"), result.get("success"),
                result.get("response_time"), result.get("error_message"),
                result.get("response_body"), json.dumps(result.get("headers", {})),
                result.get("accepted"), result.get("rejected")
            )
        )
    
    def get_results(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM results WHERE run_id = ?", (run_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def save_anomaly(self, run_id: str, anomaly: Dict[str, Any]):
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO anomalies 
               (run_id, anomaly_type, severity, title, description, file_name, evidence, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, anomaly.get("anomaly_type"), anomaly.get("severity"),
                anomaly.get("title"), anomaly.get("description"), anomaly.get("file_name"),
                json.dumps(anomaly.get("evidence", {})), anomaly.get("recommendation")
            )
        )
    
    def get_anomalies(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM anomalies WHERE run_id = ?", (run_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def save_profile(self, name: str, config: Dict[str, Any]):
        now = datetime.now().isoformat()
        conn = self._get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO profiles 
               (name, target_url, timeout, delay, workers, max_retries, form_field, generator_types, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, config.get("target_url"), config.get("timeout", 30),
                config.get("delay", 0), config.get("workers", 1), config.get("max_retries", 0),
                config.get("form_field", "file"), json.dumps(config.get("generators", [])), now
            )
        )
    
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM profiles WHERE name = ?", (name,)).fetchone()
        if row:
            return dict(row)
        return None
    
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM profiles ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    
    def delete_profile(self, name: str):
        conn = self._get_connection()
        conn.execute("DELETE FROM profiles WHERE name = ?", (name,))


_db_instance = None

def get_db():
    """Get database instance (lazy initialization)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


db = get_db()
