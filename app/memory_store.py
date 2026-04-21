from __future__ import annotations

import os
from datetime import datetime
import psycopg2
from psycopg2.extensions import connection as PgConnection


def _get_conn() -> PgConnection:
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "123456"),
        dbname=os.getenv("PG_DB", "lang-agent"),
    )


def _fmt_updated_at(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


def _ensure_table() -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, memory_key)
                )
                """
            )
        conn.commit()


def save_user_memory(user_id: str, key: str, value: str) -> None:
    _ensure_table()
    now = datetime.now()
    clean_key = key.strip()
    clean_value = value.strip()
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_memory
                SET memory_value = %s, updated_at = %s
                WHERE user_id = %s AND memory_key = %s
                """,
                (clean_value, now, user_id, clean_key),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO user_memory(user_id, memory_key, memory_value, updated_at)
                    VALUES(%s, %s, %s, %s)
                    """,
                    (user_id, clean_key, clean_value, now),
                )
        conn.commit()


def search_user_memory(user_id: str, query: str, limit: int = 5) -> list[dict[str, str]]:
    _ensure_table()
    q = f"%{query.strip()}%"
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT memory_key, memory_value, updated_at
                FROM user_memory
                WHERE user_id = %s
                  AND (memory_key ILIKE %s OR memory_value ILIKE %s)
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (user_id, q, q, limit),
            )
            rows = cur.fetchall()
    return [
        {"key": key, "value": value, "updated_at": _fmt_updated_at(updated_at)}
        for key, value, updated_at in rows
    ]


def list_user_memory(user_id: str, limit: int = 10) -> list[dict[str, str]]:
    _ensure_table()
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT memory_key, memory_value, updated_at
                FROM user_memory
                WHERE user_id = %s
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()
    return [
        {"key": key, "value": value, "updated_at": _fmt_updated_at(updated_at)}
        for key, value, updated_at in rows
    ]

