from __future__ import annotations

from io import StringIO
from typing import Iterable

import duckdb
import pandas as pd

from src.config import AppSettings
from src.schema.metadata import Catalog, ColumnInfo, TableInfo

MOCK_CSV = """order_date,customer_name,product_name,product_line,revenue,volume,cost,margin,country,state
2024-01-15,Synthetic Customer 1,Analytics Suite,Software,128000,42,82000,46000,USA,California
2024-01-18,Synthetic Customer 2,Insight Pro,Software,94000,35,61000,33000,USA,Texas
2024-02-05,Synthetic Customer 1,Cloud Gateway,Services,151000,49,98000,53000,USA,California
2024-02-12,Synthetic Customer 4,Data Fabric,Software,88000,31,59000,29000,Canada,Ontario
2024-03-09,Synthetic Customer 6,Analytics Suite,Software,119000,38,76000,43000,Brazil,Sao Paulo
2024-03-25,Synthetic Customer 2,Support Plus,Services,46000,18,30000,16000,USA,Texas
2024-04-02,Synthetic Customer 5,Analytics Suite,Software,134000,41,86000,48000,USA,Florida
2024-04-10,Synthetic Customer 5,Cloud Gateway,Services,73000,25,49000,24000,USA,Florida
2024-05-04,Synthetic Customer 7,Insight Pro,Software,99000,37,67000,32000,USA,New York
2024-05-20,Synthetic Customer 7,Support Plus,Services,42000,15,29000,13000,USA,New York
2024-06-11,Synthetic Customer 3,Data Fabric,Software,141000,44,92000,49000,USA,Louisiana
2024-06-26,Synthetic Customer 3,Cloud Gateway,Services,68000,24,43000,25000,USA,Louisiana
2024-07-03,Synthetic Customer 1,Support Plus,Services,39000,14,28000,11000,USA,California
2024-07-19,Synthetic Customer 4,Analytics Suite,Software,123000,39,79000,44000,Canada,Ontario
2024-08-08,Synthetic Customer 6,Insight Pro,Software,105000,36,71000,34000,Brazil,Sao Paulo
2024-08-23,Synthetic Customer 6,Support Plus,Services,41000,16,30000,11000,Brazil,Sao Paulo
2024-09-06,Synthetic Customer 2,Data Fabric,Software,117000,40,77000,40000,USA,Texas
2024-09-17,Synthetic Customer 5,Support Plus,Services,45000,17,31000,14000,USA,Florida
2024-10-14,Synthetic Customer 7,Cloud Gateway,Services,71000,23,48000,23000,USA,New York
2024-10-29,Synthetic Customer 3,Analytics Suite,Software,147000,46,94000,53000,USA,Louisiana
2024-11-13,Synthetic Customer 1,Data Fabric,Software,132000,43,86000,46000,USA,California
2024-11-27,Synthetic Customer 4,Support Plus,Services,37000,13,26000,11000,Canada,Ontario
2024-12-05,Synthetic Customer 6,Cloud Gateway,Services,76000,26,50000,26000,Brazil,Sao Paulo
2024-12-19,Synthetic Customer 5,Insight Pro,Software,111000,34,73000,38000,USA,Florida
2025-01-16,Synthetic Customer 1,Analytics Suite,Software,136000,43,87000,49000,USA,California
2025-01-30,Synthetic Customer 2,Cloud Gateway,Services,72000,24,47000,25000,USA,Texas
2025-02-14,Synthetic Customer 3,Data Fabric,Software,152000,47,98000,54000,USA,Louisiana
2025-02-28,Synthetic Customer 7,Insight Pro,Software,103000,35,69000,34000,USA,New York
"""


class MockSalesClient:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.connection = duckdb.connect(database=":memory:")
        self.sales = pd.read_csv(StringIO(MOCK_CSV), parse_dates=["order_date"])
        self.connection.register("sales_df", self.sales)
        self.connection.execute("CREATE TABLE sales AS SELECT * FROM sales_df")
        self.connection.execute("SET enable_external_access=false")

    def test_connection(self):
        return True, "mock"

    def execute_query(self, sql: str) -> pd.DataFrame:
        from src.sql.validator import validate_and_limit_sql
        validated = validate_and_limit_sql(sql, ["sales"], self.settings.row_limit, dialect="duckdb")
        return self.connection.execute(validated).df()

    def get_catalog(self, allowed_tables: Iterable[str] | None = None, introspect: bool = False) -> Catalog:
        table = TableInfo(
            name="SALES",
            description="Tabela demo de vendas com pedidos, receita, custo, volume e geografia.",
            columns=[
                ColumnInfo("ORDER_DATE", "DATE", "Data do pedido"),
                ColumnInfo("CUSTOMER_NAME", "VARCHAR", "Nome do cliente"),
                ColumnInfo("PRODUCT_NAME", "VARCHAR", "Produto vendido"),
                ColumnInfo("PRODUCT_LINE", "VARCHAR", "Linha do produto"),
                ColumnInfo("REVENUE", "NUMBER", "Receita do pedido"),
                ColumnInfo("VOLUME", "NUMBER", "Quantidade ou volume"),
                ColumnInfo("COST", "NUMBER", "Custo do pedido"),
                ColumnInfo("MARGIN", "NUMBER", "Margem em valor"),
                ColumnInfo("COUNTRY", "VARCHAR", "Pais"),
                ColumnInfo("STATE", "VARCHAR", "Estado ou provincia"),
            ],
        )
        catalog = Catalog(schema_name="DEMO", tables=[table])
        if allowed_tables:
            catalog.tables = [t for t in catalog.tables if t.name in {name.upper() for name in allowed_tables}]
        return catalog
