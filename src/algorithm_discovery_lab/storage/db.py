"""SQLite-based storage for experiments, candidates, and discoveries."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any

from algorithm_discovery_lab.core.candidate import Candidate, CandidateState, VerificationResult, BenchmarkResult
from algorithm_discovery_lab.core.discovery import Discovery


class Storage:
    """Lightweight SQLite storage backend."""

    def __init__(self, db_path: str = "adl.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                problem_type TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                seed INTEGER,
                created_at REAL,
                completed_at REAL,
                best_candidate_id TEXT
            );
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                experiment_id TEXT,
                problem_type TEXT,
                representation TEXT,
                state TEXT,
                cost_metrics TEXT,
                verification TEXT,
                benchmark TEXT,
                parent_ids TEXT,
                generation INTEGER,
                seed INTEGER,
                created_at REAL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
            CREATE TABLE IF NOT EXISTS discoveries (
                id TEXT PRIMARY KEY,
                problem TEXT,
                domain TEXT,
                candidate TEXT,
                baseline TEXT,
                verification_method TEXT,
                verification_result TEXT,
                cost_metrics TEXT,
                benchmark_result TEXT,
                hardware TEXT,
                software_env TEXT,
                search_config TEXT,
                search_seed INTEGER,
                generation_discovered INTEGER,
                timestamp REAL,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS search_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                event_type TEXT,
                generation INTEGER,
                candidate_id TEXT,
                data TEXT,
                timestamp REAL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)
        self.conn.commit()

    def save_experiment(
        self, exp_id: str, problem_type: str, config: dict[str, Any], seed: int
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO experiments (id, problem_type, config, seed, status, created_at) VALUES (?, ?, ?, ?, 'running', ?)",
            (exp_id, problem_type, json.dumps(config), seed, time.time()),
        )
        self.conn.commit()

    def complete_experiment(self, exp_id: str, best_candidate_id: str | None = None) -> None:
        self.conn.execute(
            "UPDATE experiments SET status='completed', completed_at=?, best_candidate_id=? WHERE id=?",
            (time.time(), best_candidate_id, exp_id),
        )
        self.conn.commit()

    def save_candidate(self, candidate: Candidate, experiment_id: str = "") -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO candidates
            (id, experiment_id, problem_type, representation, state, cost_metrics, verification, benchmark, parent_ids, generation, seed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                candidate.id,
                experiment_id,
                candidate.problem_type,
                json.dumps(candidate.representation),
                candidate.state.value,
                json.dumps(candidate.cost_metrics),
                json.dumps(candidate.verification.to_dict()) if candidate.verification else None,
                json.dumps(candidate.benchmark.to_dict()) if candidate.benchmark else None,
                json.dumps(candidate.parent_ids),
                candidate.generation,
                candidate.seed,
                candidate.created_at,
            ),
        )
        self.conn.commit()

    def save_discovery(self, discovery: Discovery) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO discoveries
            (id, problem, domain, candidate, baseline, verification_method, verification_result,
             cost_metrics, benchmark_result, hardware, software_env, search_config, search_seed,
             generation_discovered, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                discovery.id,
                discovery.problem,
                discovery.domain,
                json.dumps(discovery.candidate_dict),
                json.dumps(discovery.baseline_dict),
                discovery.verification_method,
                json.dumps(discovery.verification_result),
                json.dumps(discovery.cost_metrics),
                json.dumps(discovery.benchmark_result),
                json.dumps(discovery.hardware),
                json.dumps(discovery.software_env),
                json.dumps(discovery.search_config),
                discovery.search_seed,
                discovery.generation_discovered,
                discovery.timestamp,
                discovery.notes,
            ),
        )
        self.conn.commit()

    def save_event(self, experiment_id: str, event_type: str, generation: int, data: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO search_events (experiment_id, event_type, generation, data, timestamp) VALUES (?, ?, ?, ?, ?)",
            (experiment_id, event_type, generation, json.dumps(data), time.time()),
        )
        self.conn.commit()

    def get_experiment(self, exp_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM experiments WHERE id=?", (exp_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_experiments(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_discovery(self, disc_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM discoveries WHERE id=?", (disc_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_discoveries(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM discoveries ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_candidates(self, experiment_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM candidates WHERE experiment_id=? ORDER BY created_at DESC LIMIT ?",
            (experiment_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
