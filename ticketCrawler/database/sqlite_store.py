# -*- coding: utf-8 -*-
"""SQLite persistence for tickets, crawl runs, and visited URLs."""
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path


class Database:
    """Small SQLite storage layer for crawler history."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path or "data/pytickets.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    site TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    price REAL,
                    seat_type TEXT,
                    event_date TEXT,
                    quantity INTEGER,
                    found_at TEXT NOT NULL,
                    notified_at TEXT,
                    notification_status TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS crawl_runs (
                    id TEXT PRIMARY KEY,
                    site TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    tickets_found INTEGER DEFAULT 0,
                    tickets_notified INTEGER DEFAULT 0,
                    errors TEXT
                );

                CREATE TABLE IF NOT EXISTS url_visited (
                    url TEXT PRIMARY KEY,
                    visited_at TEXT NOT NULL,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id TEXT PRIMARY KEY,
                    site TEXT NOT NULL,
                    url TEXT,
                    interval_hours REAL NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_run_at TEXT,
                    last_status TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tickets_site_found
                    ON tickets(site, found_at);
                CREATE INDEX IF NOT EXISTS idx_tickets_notified
                    ON tickets(notified_at);
                """
            )

    def start_crawl_run(self, site):
        run_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO crawl_runs (id, site, start_time, status)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, site, now, "running"),
            )
        return run_id

    def finish_crawl_run(
        self,
        run_id,
        status="completed",
        tickets_found=0,
        tickets_notified=0,
        errors=None,
    ):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE crawl_runs
                SET end_time = ?, status = ?, tickets_found = ?,
                    tickets_notified = ?, errors = ?
                WHERE id = ?
                """,
                (
                    datetime.now(UTC).isoformat(),
                    status,
                    tickets_found,
                    tickets_notified,
                    self._to_json(errors) if errors else None,
                    run_id,
                ),
            )

    def save_ticket(self, ticket_data):
        url = ticket_data.get("url")
        if not url:
            raise ValueError("Ticket data requires a url")

        ticket_id = ticket_data.get("id") or str(uuid.uuid4())
        found_at = ticket_data.get("found_at") or datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO tickets (
                    id, site, url, price, seat_type, event_date, quantity,
                    found_at, notified_at, notification_status, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    ticket_data.get("site", "unknown"),
                    url,
                    ticket_data.get("price"),
                    ticket_data.get("seat_type"),
                    ticket_data.get("date") or ticket_data.get("event_date"),
                    ticket_data.get("quantity"),
                    found_at,
                    ticket_data.get("notified_at"),
                    ticket_data.get("notification_status"),
                    self._to_json(ticket_data.get("metadata", {})),
                ),
            )
        return ticket_id

    def mark_ticket_notified(self, url, status="sent"):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET notified_at = ?, notification_status = ?
                WHERE url = ?
                """,
                (datetime.now(UTC).isoformat(), status, url),
            )

    def ticket_exists(self, url):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM tickets WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
        return row is not None

    def mark_url_visited(self, url, metadata=None):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO url_visited (url, visited_at, metadata)
                VALUES (?, ?, ?)
                """,
                (url, datetime.now(UTC).isoformat(), self._to_json(metadata or {})),
            )

    def is_url_visited(self, url):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM url_visited WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
        return row is not None

    def get_recent_tickets(self, site=None, limit=50):
        query = "SELECT * FROM tickets"
        params = []
        if site:
            query += " WHERE site = ?"
            params.append(site)
        query += " ORDER BY found_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def query_tickets(self, site=None, notification_status=None, limit=100):
        query = "SELECT * FROM tickets WHERE 1 = 1"
        params = []
        if site:
            query += " AND site = ?"
            params.append(site)
        if notification_status:
            query += " AND notification_status = ?"
            params.append(notification_status)
        query += " ORDER BY found_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_crawl_runs(self, site=None, limit=100):
        query = "SELECT * FROM crawl_runs"
        params = []
        if site:
            query += " WHERE site = ?"
            params.append(site)
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_summary(self):
        with self._connect() as conn:
            ticket_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            notified_count = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE notification_status = 'sent'"
            ).fetchone()[0]
            crawl_count = conn.execute("SELECT COUNT(*) FROM crawl_runs").fetchone()[0]
        return {
            "tickets": ticket_count,
            "notified": notified_count,
            "crawl_runs": crawl_count,
        }

    def upsert_scheduled_job(self, job_id, site, url=None, interval_hours=2, enabled=True):
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scheduled_jobs (
                    id, site, url, interval_hours, enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    site = excluded.site,
                    url = excluded.url,
                    interval_hours = excluded.interval_hours,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (job_id, site, url, interval_hours, int(enabled), now, now),
            )

    def list_scheduled_jobs(self, enabled=None):
        query = "SELECT * FROM scheduled_jobs"
        params = []
        if enabled is not None:
            query += " WHERE enabled = ?"
            params.append(int(enabled))
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def delete_scheduled_job(self, job_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))

    def update_scheduled_job_status(self, job_id, status):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE scheduled_jobs
                SET last_run_at = ?, last_status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    datetime.now(UTC).isoformat(),
                    status,
                    datetime.now(UTC).isoformat(),
                    job_id,
                ),
            )

    def clear_url_cache(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM url_visited")

    @staticmethod
    def _to_json(value):
        return json.dumps(value or {}, sort_keys=True)
