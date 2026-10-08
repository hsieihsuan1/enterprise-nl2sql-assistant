"""Conservative AST validation for a demonstration, not a production security boundary."""
from typing import Iterable
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

class SqlValidationError(ValueError):
    pass

ALLOWED_FUNCTIONS = {"SUM", "AVG", "MIN", "MAX", "COUNT", "COALESCE", "CAST", "EXTRACT", "TIME_TO_STR", "TO_CHAR", "ROUND", "ABS", "AND", "OR"}

def validate_and_limit_sql(sql: str, allowed_tables: Iterable[str], row_limit: int = 200, dialect: str = "duckdb") -> str:
    if not 1 <= row_limit <= 1000:
        raise SqlValidationError("Row limit must be between 1 and 1000.")
    cleaned = sql.strip()
    if cleaned.startswith("```sql") and cleaned.endswith("```"):
        cleaned = cleaned[6:-3].strip()
    try:
        statements = sqlglot.parse(cleaned, read=dialect)
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError("SQL could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SqlValidationError("Only one SELECT query is allowed.")
    tree = statements[0]
    if any(isinstance(node, (exp.DML, exp.DDL, exp.Command)) for node in tree.walk()):
        raise SqlValidationError("Write operations are not allowed anywhere in the query.")
    allowed = {name.lower() for name in allowed_tables}
    if not allowed:
        raise SqlValidationError("A non-empty table allowlist is required.")
    for select in tree.find_all(exp.Select):
        if select.args.get("into") or select.args.get("locks"):
            raise SqlValidationError("SELECT INTO and locking are not allowed.")
    for node in tree.find_all(exp.Func):
        name = node.name.upper() if isinstance(node, exp.Anonymous) else node.sql_name().upper()
        if name not in ALLOWED_FUNCTIONS:
            raise SqlValidationError(f"Function not allowed: {name}")
    physical_tables = []
    for scope in traverse_scope(tree):
        for source in scope.sources.values():
            if isinstance(source, exp.Table):
                if not isinstance(source.this, exp.Identifier) or source.db or source.catalog:
                    raise SqlValidationError("Qualified names and table functions are not allowed.")
                physical_tables.append(source.name.lower())
    if not physical_tables or not set(physical_tables).issubset(allowed):
        raise SqlValidationError("Query must use only allowlisted tables.")
    # Replace even an existing higher/dynamic limit to enforce a fixed cap.
    tree = exp.select("*").from_(tree.subquery("validated_query")).limit(row_limit)
    return tree.sql(dialect=dialect)
