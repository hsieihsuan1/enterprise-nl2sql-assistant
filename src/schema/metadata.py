from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    description: str


@dataclass
class TableInfo:
    name: str
    description: str
    columns: List[ColumnInfo] = field(default_factory=list)


@dataclass
class Catalog:
    schema_name: str
    tables: List[TableInfo] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        lines = [f"Schema: {self.schema_name}"]
        for table in self.tables:
            lines.append(f"Tabela {table.name}: {table.description}")
            for column in table.columns:
                lines.append(f"- {column.name} ({column.data_type}): {column.description}")
        return "\n".join(lines)


def default_mock_catalog() -> Catalog:
    return Catalog(
        schema_name="DEMO",
        tables=[
            TableInfo(
                name="SALES",
                description="Pedidos de vendas com receita, volume, custo, margem e geografia.",
                columns=[
                    ColumnInfo("ORDER_DATE", "DATE", "Data do pedido"),
                    ColumnInfo("CUSTOMER_NAME", "VARCHAR2", "Cliente"),
                    ColumnInfo("PRODUCT_NAME", "VARCHAR2", "Produto"),
                    ColumnInfo("PRODUCT_LINE", "VARCHAR2", "Linha de produto"),
                    ColumnInfo("REVENUE", "NUMBER", "Receita"),
                    ColumnInfo("VOLUME", "NUMBER", "Volume"),
                    ColumnInfo("COST", "NUMBER", "Custo"),
                    ColumnInfo("MARGIN", "NUMBER", "Margem"),
                    ColumnInfo("COUNTRY", "VARCHAR2", "Pais"),
                    ColumnInfo("STATE", "VARCHAR2", "Estado"),
                ],
            )
        ],
    )


def build_catalog_from_text(schema_notes: str, default_catalog: Catalog, allowed_tables: Iterable[str] | None = None) -> Catalog:
    allowed = {name.upper() for name in allowed_tables or []}
    catalog = default_catalog
    if allowed:
        catalog.tables = [table for table in catalog.tables if table.name.upper() in allowed]
    if schema_notes.strip() and catalog.tables:
        catalog.tables[0].description = f"{catalog.tables[0].description} {schema_notes.strip()}"
    return catalog
