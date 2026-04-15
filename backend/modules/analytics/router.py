"""
EREBUS · User Analytics Router
================================
Full CRUD for the user_analytics table stored in AWS RDS PostgreSQL.

Endpoints
---------
GET    /analytics              → list all sessions (newest first)
DELETE /analytics/{session_id} → delete a session entry
DELETE /analytics              → clear ALL sessions

Sessions are AUTO-INSERTED by the chat and analyze routers — never by the user.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ── DB availability flag (set on first successful connection) ─────────────────
_DB_READY = False


def _try_ensure_table() -> bool:
    """
    Try to create the user_analytics table.
    Returns True if successful, False if DB is unreachable.
    Never raises.
    """
    global _DB_READY
    try:
        from core.database import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_analytics (
                    id           SERIAL PRIMARY KEY,
                    session_type VARCHAR(20)  NOT NULL DEFAULT 'chat',
                    title        TEXT         NOT NULL,
                    sub          TEXT,
                    ticker       VARCHAR(50),
                    ui_state     JSONB,
                    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            try:
                cur.execute("ALTER TABLE user_analytics ADD COLUMN IF NOT EXISTS ui_state JSONB")
            except Exception:
                pass
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_analytics_created
                ON user_analytics(created_at DESC)
            """)
            cur.execute("DROP TRIGGER IF EXISTS update_user_analytics_updated_at ON user_analytics")
            cur.execute("""
                CREATE TRIGGER update_user_analytics_updated_at
                    BEFORE UPDATE ON user_analytics
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """)
        _DB_READY = True
        logger.info("user_analytics table ready")
        return True
    except Exception as e:
        logger.warning("DB not reachable for analytics (will retry per-request): %s", e)
        _DB_READY = False
        return False


# Attempt once on startup — OK if it fails (port not whitelisted yet)
_try_ensure_table()


def _require_db():
    """
    Called at the start of every endpoint.
    Retries table setup if DB wasn't ready on startup.
    Raises 503 with a clear message if still unreachable.
    """
    global _DB_READY
    if not _DB_READY:
        _DB_READY = _try_ensure_table()
    if not _DB_READY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database unreachable. "
                "Please whitelist your IP (103.208.226.238/32) on port 5432 "
                "in the RDS security group, then retry."
            ),
        )


# ── Utility ───────────────────────────────────────────────────────────────────

def _row_to_out(row: dict) -> dict:
    return {
        "id":           row["id"],
        "session_type": row["session_type"],
        "title":        row["title"],
        "sub":          row["sub"],
        "ticker":       row["ticker"],
        "ui_state":     row.get("ui_state"),
        "created_at":   row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at":   row["updated_at"].isoformat() if row["updated_at"] else None,
    }


# ── Public helper: auto-insert a session (used by chat/analyze routers) ───────

def record_session(session_type: str, title: str, sub: Optional[str] = None, ticker: Optional[str] = None) -> None:
    """
    Best-effort insert into user_analytics.
    Called by other routers (chat, analyze) after a successful action.
    Never raises — silently drops if DB is unreachable.
    """
    try:
        from core.database import execute_write
        if not _DB_READY:
            _try_ensure_table()
        execute_write(
            "INSERT INTO user_analytics (session_type, title, sub, ticker) VALUES (%s, %s, %s, %s)",
            (session_type, title[:300], sub, ticker),
            returning="id",
        )
    except Exception as e:
        logger.debug("[analytics] record_session skipped: %s", e)


# ── Models ────────────────────────────────────────────────────────────────────

from typing import Any
import json

class CreateSessionReq(BaseModel):
    session_type: str = "chat"
    title: str = Field(..., max_length=500)
    sub: Optional[str] = None
    ticker: Optional[str] = None
    ui_state: Optional[Any] = None

class UpdateSessionReq(BaseModel):
    title: Optional[str] = None
    sub: Optional[str] = None
    ticker: Optional[str] = None
    ui_state: Optional[Any] = None

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="List all analytics sessions")
def list_sessions():
    """Return all auto-tracked sessions, newest first."""
    _require_db()
    from core.database import execute_query
    rows = execute_query("""
        SELECT id, session_type, title, sub, ticker, created_at, updated_at
        FROM user_analytics
        ORDER BY created_at DESC
    """)
    return {"sessions": [_row_to_out(r) for r in rows], "total": len(rows)}

@router.get("/{session_id}", summary="Get a specific analytics session")
def get_session(session_id: int):
    """Fetch a session, including full ui_state payload."""
    _require_db()
    from core.database import execute_single
    row = execute_single("SELECT * FROM user_analytics WHERE id = %s", (session_id,))
    if not row:
        raise HTTPException(404, detail="Session not found")
    return {"session": _row_to_out(dict(row))}

@router.post("", summary="Create a new analytics session")
def create_session(req: CreateSessionReq):
    _require_db()
    from core.database import execute_write
    state_json = json.dumps(req.ui_state) if req.ui_state is not None else None
    
    session_id = execute_write(
        """
        INSERT INTO user_analytics (session_type, title, sub, ticker, ui_state)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (req.session_type, req.title[:500], req.sub, req.ticker, state_json),
        returning="id"
    )
    return {"session": {"id": session_id}}

@router.put("/{session_id}", summary="Update an existing analytics session")
def update_session(session_id: int, req: UpdateSessionReq):
    _require_db()
    from core.database import get_cursor
    updates = []
    vals = []
    
    if req.title is not None:
        updates.append("title = %s")
        vals.append(req.title[:500])
    if req.sub is not None:
        updates.append("sub = %s")
        vals.append(req.sub)
    if req.ticker is not None:
        updates.append("ticker = %s")
        vals.append(req.ticker)
    if req.ui_state is not None:
        updates.append("ui_state = %s")
        vals.append(json.dumps(req.ui_state))
        
    if not updates:
        return {"updated": True, "id": session_id}
        
    vals.append(session_id)
    with get_cursor() as cur:
        cur.execute(f"UPDATE user_analytics SET {', '.join(updates)} WHERE id = %s", tuple(vals))
        if cur.rowcount == 0:
            raise HTTPException(404, detail=f"Session {session_id} not found")
    return {"updated": True, "id": session_id}


@router.delete("/{session_id}", summary="Delete a single analytics session")
def delete_session(session_id: int):
    """Permanently delete a session by ID."""
    _require_db()
    from core.database import get_cursor
    with get_cursor() as cur:
        cur.execute("DELETE FROM user_analytics WHERE id = %s", (session_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, detail=f"Session {session_id} not found")
    return {"deleted": True, "id": session_id}


@router.delete("", summary="Clear all analytics sessions")
def clear_all_sessions():
    """Delete every row in user_analytics."""
    _require_db()
    from core.database import get_cursor
    with get_cursor() as cur:
        cur.execute("DELETE FROM user_analytics")
        deleted = cur.rowcount
    return {"deleted": True, "count": deleted}
