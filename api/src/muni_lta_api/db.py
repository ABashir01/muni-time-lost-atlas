"""Small Postgres access helpers for the historical/static API surface."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from psycopg import Connection, connect
from psycopg.rows import dict_row


class Database:
    """Thin connection wrapper around psycopg for read-only endpoint queries."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    @contextmanager
    def connection(self) -> Iterator[Connection[Any]]:
        with connect(self._database_url, row_factory=dict_row) as connection:
            yield connection

    def fetch_all(
        self,
        query: str,
        params: Sequence[object] | None = None,
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]

    def fetch_one(
        self,
        query: str,
        params: Sequence[object] | None = None,
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(query, params)
        if not rows:
            return None
        return rows[0]

    def table_exists(self, *, schema: str, table: str) -> bool:
        row = self.fetch_one(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name = %s
            ) AS table_exists
            """,
            [schema, table],
        )
        return bool(row and row["table_exists"])
