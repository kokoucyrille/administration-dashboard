"""Tableaux HTML aux couleurs des maquettes (en-tête vert pâle, lignes séparées, évolution en vert)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from data.data import fmt_dec, fmt_int


def create_table(df: pd.DataFrame, formats: dict | None = None, up_cols: tuple = ()) -> str:
    """
    Convertit un DataFrame en table HTML.
    `formats` : colonne -> fonction de mise en forme ; `up_cols` : colonnes de variation (flèche verte).
    """
    formats = formats or {}
    head = "".join(f"<th>{c}</th>" for c in df.columns)
    body = []
    for _, row in df.iterrows():
        cells = []
        for c in df.columns:
            v = row[c]
            txt = formats[c](v) if c in formats else (fmt_dec(v) if isinstance(v, float) else str(v))
            if c in up_cols:
                cells.append(f'<td class="up"><i class="fa-solid fa-arrow-up" style="font-size:11px"></i> {txt}</td>')
            else:
                cells.append(f"<td>{txt}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def render_table(df: pd.DataFrame, **kw) -> None:
    if df.empty:
        st.markdown('<div style="color:#7b8794;padding:20px 0">Aucune donnée pour cette sélection.</div>', unsafe_allow_html=True)
        return
    st.markdown(create_table(df, **kw), unsafe_allow_html=True)


# mises en forme usuelles
FMT_PERF = {"CA (Md)": lambda v: fmt_dec(v, 1), "Ventes": fmt_int, "Marge (%)": lambda v: fmt_dec(v, 1),
            "Évolution": lambda v: f"+{fmt_dec(v, 1)}%"}
