"""
History Manager Service.

Stores and retrieves request history using SQLite.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

from ..types import (
    HistoryEntry,
    HistoryListInput,
    HistoryListOutput,
    HttpMethod,
    ResponseFormat,
)


class HistoryManager:
    """
    Manages request history with SQLite persistence.
    
    Stores request/response pairs for replay and analysis.
    """

    def __init__(self, db_path: str | Path = "history.db") -> None:
        self._db_path = Path(db_path)
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        if self._initialized:
            return

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    method TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    environment TEXT,
                    request_headers TEXT,
                    request_body TEXT,
                    response_headers TEXT,
                    response_body TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp 
                ON history (timestamp DESC)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_method 
                ON history (method)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_status 
                ON history (status)
            """)
            await db.commit()

        self._initialized = True

    async def add_entry(
        self,
        method: HttpMethod,
        url: str,
        status: int,
        duration: int,
        environment: str | None = None,
        request_headers: dict[str, str] | None = None,
        request_body: Any | None = None,
        response_headers: dict[str, str] | None = None,
        response_body: Any | None = None,
    ) -> str:
        """Add a new history entry."""
        await self._ensure_initialized()

        entry_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO history (
                    id, method, url, status, duration, timestamp, environment,
                    request_headers, request_body, response_headers, response_body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    method.value,
                    url,
                    status,
                    duration,
                    timestamp,
                    environment,
                    json.dumps(request_headers) if request_headers else None,
                    json.dumps(request_body) if request_body else None,
                    json.dumps(response_headers) if response_headers else None,
                    self._truncate_body(response_body),
                ),
            )
            await db.commit()

        return entry_id

    async def list_entries(
        self,
        input_data: HistoryListInput,
    ) -> HistoryListOutput:
        """List history entries with optional filtering."""
        await self._ensure_initialized()

        conditions: list[str] = []
        params: list[Any] = []

        if input_data.method:
            conditions.append("method = ?")
            params.append(input_data.method.value)

        if input_data.url_pattern:
            conditions.append("url LIKE ?")
            params.append(f"%{input_data.url_pattern}%")

        if input_data.status_code:
            conditions.append("status = ?")
            params.append(input_data.status_code)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get total count
            cursor = await db.execute(
                f"SELECT COUNT(*) as count FROM history WHERE {where_clause}",
                params,
            )
            row = await cursor.fetchone()
            total = row["count"] if row else 0

            # Get entries
            cursor = await db.execute(
                f"""
                SELECT id, method, url, status, duration, timestamp, environment
                FROM history
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params + [input_data.limit],
            )
            rows = await cursor.fetchall()

        entries = [
            HistoryEntry(
                id=row["id"],
                method=HttpMethod(row["method"]),
                url=row["url"],
                status=row["status"],
                duration=row["duration"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                environment=row["environment"],
            )
            for row in rows
        ]

        return HistoryListOutput(entries=entries, total=total)

    async def get_entry(self, entry_id: str) -> dict[str, Any] | None:
        """Get a full history entry by ID."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM history WHERE id = ?",
                (entry_id,),
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "method": row["method"],
            "url": row["url"],
            "status": row["status"],
            "duration": row["duration"],
            "timestamp": row["timestamp"],
            "environment": row["environment"],
            "request": {
                "headers": json.loads(row["request_headers"]) if row["request_headers"] else None,
                "body": json.loads(row["request_body"]) if row["request_body"] else None,
            },
            "response": {
                "headers": json.loads(row["response_headers"]) if row["response_headers"] else None,
                "body": json.loads(row["response_body"]) if row["response_body"] else None,
            },
        }

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a history entry."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "DELETE FROM history WHERE id = ?",
                (entry_id,),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def clear_history(self, before: datetime | None = None) -> int:
        """Clear history entries, optionally before a certain date."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self._db_path) as db:
            if before:
                cursor = await db.execute(
                    "DELETE FROM history WHERE timestamp < ?",
                    (before.isoformat(),),
                )
            else:
                cursor = await db.execute("DELETE FROM history")
            await db.commit()
            return cursor.rowcount

    async def get_count(self) -> int:
        """Get total number of history entries."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) as count FROM history")
            row = await cursor.fetchone()
            return row[0] if row else 0

    def _truncate_body(self, body: Any, max_size: int = 100000) -> str | None:
        """Truncate response body for storage."""
        if body is None:
            return None
        
        body_str = json.dumps(body) if isinstance(body, (dict, list)) else str(body)
        
        if len(body_str) > max_size:
            return body_str[:max_size] + "... [truncated]"
        
        return body_str
