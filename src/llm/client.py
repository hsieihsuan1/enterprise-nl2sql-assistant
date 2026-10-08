"""Opt-in remote provider. Offline demonstrations do not instantiate this client."""
import os
from openai import OpenAI

def generate_sql(question: str, schema: str) -> str:
    key = os.getenv("OPENAI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("An API key is required for LLM mode.")
    kwargs = {"api_key": key, "timeout": 30, "max_retries": 0}
    if os.getenv("LLM_BASE_URL"):
        kwargs["base_url"] = os.environ["LLM_BASE_URL"]
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"), temperature=0,
        messages=[
            {"role": "system", "content": "Return only one read-only SELECT query for the SALES table. No comments, DDL, DML, table functions, or qualified tables. Schema: " + schema},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content or ""
