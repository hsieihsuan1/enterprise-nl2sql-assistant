from __future__ import annotations

import os
from typing import Iterable, Tuple

import oracledb
import pandas as pd

from src.config import AppSettings
from src.schema.metadata import Catalog, ColumnInfo, TableInfo


class OracleClient:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def _connect(self):
        os.environ["TNS_ADMIN"] = self.settings.oracle_wallet_dir
        return oracledb.connect(
            user=self.settings.oracle_user,
            password=self.settings.oracle_password,
            dsn=self.settings.oracle_dsn,
            config_dir=self.settings.oracle_wallet_dir,
            wallet_location=self.settings.oracle_wallet_dir,
            wallet_password=self.settings.wallet_password or None,
        )

    def test_connection(self) -> Tuple[bool, str]:
        if not self.settings.oracle_user or not self.settings.oracle_password:
            return False, "credenciais Oracle ausentes"
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("select user from dual")
                    return True, str(cursor.fetchone()[0])
        except Exception as exc:  # pragma: no cover - depends on environment
            return False, str(exc)

    def execute_query(self, sql: str) -> pd.DataFrame:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                # Always validate before executing model-produced SQL.
                from src.sql.validator import validate_and_limit_sql
                sql = validate_and_limit_sql(sql, ["sales"], self.settings.row_limit, dialect="oracle")
                cursor.execute(sql)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)

    def generate_sql_with_select_ai(self, prompt: str, profile_name: str | None = None) -> str:
        profile = (profile_name or self.settings.oracle_ai_profile).strip().upper()
        query = """
            SELECT DBMS_CLOUD_AI.GENERATE(
                prompt       => :prompt,
                profile_name => :profile_name,
                action       => 'showsql'
            )
            FROM dual
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, prompt=prompt, profile_name=profile)
                row = cursor.fetchone()
                if not row or row[0] is None:
                    return ""
                value = row[0].read() if hasattr(row[0], "read") else row[0]
                return str(value).strip()

    def get_catalog(self, allowed_tables: Iterable[str] | None = None, introspect: bool = True) -> Catalog:
        schema_name = self.settings.oracle_schema or self.settings.oracle_user.upper()
        if not introspect:
            return Catalog(schema_name=schema_name, tables=[])

        allowed = {name.upper() for name in allowed_tables or []}
        query = """
            SELECT
                c.table_name,
                tc.comments AS table_comment,
                c.column_name,
                c.data_type,
                cc.comments AS column_comment
            FROM all_tab_columns c
            LEFT JOIN all_tab_comments tc
              ON tc.owner = c.owner
             AND tc.table_name = c.table_name
            LEFT JOIN all_col_comments cc
              ON cc.owner = c.owner
             AND cc.table_name = c.table_name
             AND cc.column_name = c.column_name
            WHERE c.owner = :owner
            ORDER BY c.table_name, c.column_id
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, owner=schema_name)
                rows = cursor.fetchall()

        tables: dict[str, TableInfo] = {}
        for table_name, table_comment, column_name, data_type, column_comment in rows:
            if allowed and table_name.upper() not in allowed:
                continue
            tables.setdefault(
                table_name,
                TableInfo(
                    name=table_name,
                    description=(table_comment or f"Tabela Oracle {table_name}"),
                    columns=[],
                ),
            )
            tables[table_name].columns.append(
                ColumnInfo(
                    name=column_name,
                    data_type=data_type,
                    description=(column_comment or f"Coluna {column_name}"),
                )
            )

        return Catalog(schema_name=schema_name, tables=list(tables.values()))
