from __future__ import annotations

import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


TIME_NAME_HINTS = {"month", "date", "day", "week", "year", "period"}


def _find_time_col(df: pd.DataFrame) -> str | None:
    datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    if datetime_cols:
        return str(datetime_cols[0])

    for col in df.columns:
        lower = str(col).lower()
        if not any(hint in lower for hint in TIME_NAME_HINTS):
            continue
        series = df[col].dropna().astype(str)
        if series.empty:
            continue
        sample = series.head(20)
        if sample.map(lambda value: bool(re.match(r"^\d{4}-\d{2}(-\d{2})?$", value.strip()))).all():
            return str(col)
    return None


def _sort_time_like(df: pd.DataFrame, col: str) -> pd.DataFrame:
    series = df[col].astype(str)
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.notna().any():
        return df.assign(__sort_key=parsed).sort_values("__sort_key").drop(columns="__sort_key")
    return df.sort_values(col)


def _aggregate_for_axis(df: pd.DataFrame, axis_col: str, numeric_cols: list[str]) -> pd.DataFrame:
    base = df[[axis_col, *numeric_cols]].copy()
    if base[axis_col].duplicated().any():
        base = base.groupby(axis_col, as_index=False)[numeric_cols].sum()
    return base


def infer_chart_hint(df: pd.DataFrame) -> str:
    time_col = _find_time_col(df)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols]

    if time_col and len(numeric_cols) >= 2:
        return "combo"
    if time_col and numeric_cols:
        return "line"
    if len(numeric_cols) >= 2 and non_numeric_cols:
        return "combo"
    if len(numeric_cols) >= 2:
        return "scatter"
    if len(numeric_cols) == 1 and non_numeric_cols:
        return "bar"
    return "none"


def build_chart(df: pd.DataFrame, hint: str | None = None):
    if df.empty:
        return None

    chart_type = (hint or infer_chart_hint(df)).lower()
    numeric_cols = [str(col) for col in df.select_dtypes(include="number").columns.tolist()]
    time_col = _find_time_col(df)
    dimension_cols = [str(col) for col in df.columns if col not in numeric_cols]

    if chart_type == "line" and numeric_cols:
        x = time_col or (dimension_cols[0] if dimension_cols else None)
        if not x:
            return None
        line_df = _aggregate_for_axis(df, x, [numeric_cols[0]])
        if x == time_col:
            line_df = _sort_time_like(line_df, x)
        return px.line(line_df, x=x, y=numeric_cols[0], markers=True)

    if chart_type == "bar" and numeric_cols and dimension_cols:
        x = time_col or dimension_cols[0]
        bar_df = _aggregate_for_axis(df, x, [numeric_cols[0]])
        if x == time_col:
            bar_df = _sort_time_like(bar_df, x)
        return px.bar(bar_df, x=x, y=numeric_cols[0])

    if chart_type == "combo" and len(numeric_cols) >= 2 and dimension_cols:
        x = time_col or dimension_cols[0]
        combo_df = _aggregate_for_axis(df, x, [numeric_cols[0], numeric_cols[1]])
        if x == time_col:
            combo_df = _sort_time_like(combo_df, x)
        fig = go.Figure()
        fig.add_bar(x=combo_df[x], y=combo_df[numeric_cols[0]], name=numeric_cols[0])
        fig.add_scatter(
            x=combo_df[x],
            y=combo_df[numeric_cols[1]],
            name=numeric_cols[1],
            yaxis="y2",
            mode="lines+markers",
        )
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right"),
            legend=dict(orientation="h"),
            margin=dict(l=20, r=20, t=30, b=20),
        )
        return fig

    if chart_type == "scatter" and len(numeric_cols) >= 2:
        color = dimension_cols[0] if dimension_cols and dimension_cols[0] != time_col else None
        return px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], color=color, size=numeric_cols[1])

    return None
