# Verification - 2026-10-08

- Visual browser check confirmed the synthetic results table, chart and SQL output are readable.
- Tested offline execution with Python 3.10 in a clean virtual environment.
- 22 tests passed: SQL validator, four demo questions, result charts, output caps and negative cases tested by pytest.
- Streamlit AppTest exercised startup and a query click without exceptions.
- No LLM provider calls or real Oracle connections were used during verification.
- All demo data is synthetic; explicit synthetic customer labels replace company-like labels from the private demo.
- Only files needed for the curated demo were retained. Messaging, telemetry, authentication/UI branding, sector-specific scenarios, wallet/runtime directories and private deployment configurations were excluded.
- No notebook files included, so no notebook output is distributed.
- No source Git history was copied.
- Pattern and file-inventory scanning is not a guarantee that all secrets or intellectual-property restrictions have been detected.
