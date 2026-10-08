import streamlit as st
from src.config import AppSettings
from src.db.mock_client import MockSalesClient
from src.schema.metadata import default_mock_catalog
from src.sql.validator import validate_and_limit_sql
from src.demo import QUESTIONS, offline_sql
from src.visualization.chart_builder import build_chart

st.set_page_config(page_title="DataTalk", page_icon="📊", layout="wide")
st.title("DataTalk")
st.caption("Natural-language analytics | Synthetic sales data | Local demonstration")
st.info("Offline mode uses predefined queries. LLM mode is opt-in and can send your question and schema to the configured provider.")
mode = st.sidebar.radio("Query generation", ["Offline demo", "LLM (requires API key)"])
st.sidebar.caption("Local DuckDB backend. Oracle adapter is included but not tested against a live database.")
question = st.selectbox("Choose a demo question", list(QUESTIONS))
if mode.startswith("LLM"):
    question = st.text_input("Ask about sales data", value=question)
if st.button("Run query", type="primary"):
    try:
        settings = AppSettings.load()
        backend = MockSalesClient(settings)
        if mode == "Offline demo":
            sql = offline_sql(question)
        else:
            from src.llm.client import generate_sql
            sql = generate_sql(question, default_mock_catalog().to_prompt_text())
        validated = validate_and_limit_sql(sql, ["sales"], settings.row_limit)
        df = backend.execute_query(validated)
        st.subheader("Results")
        st.write(f"{len(df)} rows returned from synthetic data.")
        st.dataframe(df, hide_index=True, width="stretch")
        chart = build_chart(df)
        if chart is not None:
            st.plotly_chart(chart, width="stretch")
        st.subheader("SQL executed")
        st.code(validated, language="sql")
        st.caption("Validation uses a conservative SQL AST allowlist and a row cap. It is not a production sandbox.")
        backend.connection.close()
    except Exception as exc:
        st.error(str(exc))
