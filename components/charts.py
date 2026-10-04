"""Graphiques Plotly aux couleurs des maquettes + blocs HTML (barres Top 5, anneaux de qualité)."""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import FONT, OP_COLORS, THEME
from data.data import fmt_dec, fmt_int

GRID = "#e3edf0"
AXIS_TXT = "#0a4a9a"
LINE_COLORS = [THEME["green"], "#ffc903", "#f20e36", "#a24df0"]


def show(fig: go.Figure, key: str) -> None:
    """Affiche une figure sans barre d'outils, à la largeur du conteneur."""
    st.plotly_chart(fig, width="stretch", key=key,
                    config={"displayModeBar": False, "responsive": True})


def _layout(fig: go.Figure, height: int, **kw) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=4, r=8, t=kw.pop("t", 8), b=kw.pop("b", 4)), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, size=13, color=AXIS_TXT), showlegend=False, **kw)
    return fig


def nice_ticks(vmax: float, n: int = 4) -> list[float]:
    """Graduations « rondes » (0, 2,5k, 5k, …) jusqu'à couvrir `vmax`."""
    if vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    top = math.ceil(vmax / step) * step
    return [round(i * step, 6) for i in range(int(round(top / step)) + 1)]


def compact(v: float) -> str:
    """2500 -> '2,5k' ; 800000 -> '800K' ; 1000000 -> '1M' (graduations d'axes)."""
    if abs(v) >= 1_000_000:
        return f"{fmt_dec(v / 1_000_000, 1).rstrip('0').rstrip(',')}M"
    if abs(v) >= 1000:
        return f"{fmt_dec(v / 1000, 1).rstrip('0').rstrip(',')}k"
    return fmt_dec(v, 1).rstrip("0").rstrip(",") if v % 1 else str(int(v))


# --------------------------------------------------------------------------------------
def create_bar_chart(df: pd.DataFrame, x: str, y: str, colors: list[str], height: int = 215,
                     fmt=compact, hover_unit: str = "") -> go.Figure:
    """Barres verticales (une couleur par barre, comme sur la maquette)."""
    ticks = nice_ticks(float(df[y].max()))
    fig = go.Figure(go.Bar(x=df[x], y=df[y], marker_color=colors[: len(df)], width=0.42,
                           hovertemplate="%{x}<br><b>%{customdata}</b>" + hover_unit + "<extra></extra>",
                           customdata=[fmt_int(v) for v in df[y]]))
    _layout(fig, height, b=2)
    fig.update_yaxes(tickvals=ticks, ticktext=[fmt(t) for t in ticks], gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=12), range=[0, ticks[-1]])
    fig.update_xaxes(showgrid=False, tickfont=dict(size=13.5))
    return fig


def create_donut_chart(labels: list[str], values: list[float], colors: list[str], center_top: str,
                       center_bottom: str, height: int = 190) -> go.Figure:
    """Donut avec valeur + libellé au centre (la légende est rendue en HTML à côté)."""
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False, direction="clockwise",
                           marker=dict(colors=colors, line=dict(color="#fff", width=2)), textinfo="none", rotation=0,
                           hovertemplate="%{label}<br>%{percent}<extra></extra>"))
    _layout(fig, height, t=2, b=2)
    fig.update_layout(margin=dict(l=2, r=2, t=2, b=2), annotations=[
        dict(text=f"<b>{center_top}</b>", x=0.5, y=0.56, showarrow=False, font=dict(size=24 if len(center_top) <= 6 else 19, color="#0a4a9a")),
        dict(text=f"<b>{center_bottom}</b>", x=0.5, y=0.40, showarrow=False, font=dict(size=13.5, color="#0a4a9a"))])
    return fig


def create_line_chart(df: pd.DataFrame, x: str, y: str, group: str, colors: dict | list, height: int = 190,
                      yfmt=compact, yrange: tuple | None = None, ypct: bool = False) -> go.Figure:
    """Courbes multi-séries avec marqueurs ronds et légende horizontale en haut."""
    fig = go.Figure()
    groups = list(dict.fromkeys(df[group]))
    palette = colors if isinstance(colors, dict) else dict(zip(groups, colors))
    for g in groups:
        d = df[df[group] == g]
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], name=g, mode="lines+markers", line=dict(color=palette[g], width=2.4),
            marker=dict(size=7, color=palette[g], line=dict(color="#fff", width=1)),
            hovertemplate="%{x}<br>" + g + " : <b>%{y:,.0f}</b><extra></extra>"))
    if ypct:
        ticks = [0, 25, 50, 75, 100]
        tt = [f"{t}%" for t in ticks]
    else:
        ticks = nice_ticks(float(df[y].max()), 4)
        tt = [yfmt(t) for t in ticks]
    _layout(fig, height, t=34, b=2)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", x=-0.02, y=1.22, xanchor="left", yanchor="top", itemwidth=30,
                                                   font=dict(size=11), itemsizing="constant", tracegroupgap=0))
    fig.update_yaxes(tickvals=ticks, ticktext=tt, gridcolor=GRID, zeroline=False, tickfont=dict(size=12),
                     range=yrange or [0, ticks[-1] * 1.0])
    fig.update_xaxes(showgrid=False, tickfont=dict(size=9.5 if len(df[x].unique()) > 7 else 12), type="category", tickangle=0)
    return fig


# --------------------------------------------------------------------------------------
# Blocs HTML
# --------------------------------------------------------------------------------------
def create_top5(df: pd.DataFrame, colors: list[str] | None = None, unit: str = "") -> str:
    """Barres horizontales « Top 5 » (piste grise + remplissage + valeur à droite)."""
    if df.empty:
        return '<div style="color:#7b8794;padding:20px 0">Aucune localité pour cette sélection.</div>'
    vmax = float(df["Valeur"].max()) or 1.0
    colors = colors or [THEME["green"], "#45b08c", "#4fbf9f", "#58c9aa", "#62d1b3"]
    rows = []
    for i, r in df.reset_index(drop=True).iterrows():
        pct = max(r["Valeur"] / vmax * 100, 3)
        rows.append(f'<div class="row"><span>{r["Localité"]}</span><div class="track"><div class="fill" '
                    f'style="width:{pct:.1f}%;background:{colors[i % len(colors)]}"></div></div>'
                    f'<span class="val">{fmt_int(r["Valeur"])}{unit}</span></div>')
    return f'<div class="top5">{"".join(rows)}</div>'


def create_ring(value_text: str, pct: float, color: str) -> str:
    """Anneau de progression (conic-gradient) avec la valeur au centre."""
    pct = max(0, min(pct, 100))
    return (f'<div class="ring" style="background:conic-gradient({color} {pct * 3.6:.0f}deg,#e8eff1 0)">'
            f'<span style="color:{color}">{value_text}</span></div>')


def create_quality_block(q: dict) -> str:
    """4 colonnes : disponibilité, débit, latence, satisfaction (icône + libellé + anneau)."""
    items = [
        ("fa-tower-cell", THEME["green"], "Taux de disponibilité", f"{fmt_dec(q['dispo'], 1)}%", q["dispo"]),
        ("fa-gauge-high", "#1488ee", "Débit moyen (Mbps)", fmt_dec(q["debit"], 1), q["debit"] / 20 * 100),
        ("fa-clock", "#f5b800", "Temps de latence (ms)", fmt_int(q["latence"]), 100 - q["latence"]),
        ("fa-star", "#2bb673", "Taux de satisfaction", f"{fmt_int(q['satisf'])}%", q["satisf"]),
    ]
    cells = "".join(
        f'<div class="q-item"><div class="q-ico" style="background:{c}"><i class="fa-solid {ic}"></i></div>'
        f'<div class="q-lab">{lab}</div>{create_ring(txt, pct, c)}</div>' for ic, c, lab, txt, pct in items)
    return f'<div class="q-grid">{cells}</div>'


def create_key_indicators(rates: dict, deltas: dict) -> str:
    """Panneau « Indicateurs clés » : pastille d'icône, libellé, valeur et variation vs 2024."""
    items = [("fa-users-viewfinder", "Taux de pénétration des services numériques", "penetration"),
             ("fa-mobile-screen-button", "Taux d'utilisation du paiement mobile", "paiement"),
             ("fa-star", "Taux de satisfaction des usagers", "satisfaction")]
    out = []
    for icon, lab, k in items:
        out.append(
            f'<div class="ind-row"><div class="ind-ico"><i class="fa-solid {icon}"></i></div><div style="flex:1">'
            f'<div class="ind-lab">{lab}</div><div style="display:flex;align-items:baseline;gap:10px">'
            f'<span class="ind-val">{fmt_dec(rates[k], 1)}%</span>'
            f'<span class="ind-delta"><i class="fa-solid fa-arrow-up"></i> +{fmt_dec(deltas[k], 1)}% vs. 2024</span>'
            f'</div></div></div>')
    return "".join(out)


def operator_donut(df: pd.DataFrame, total: float, center_bottom: str, key: str, height: int = 190,
                   nd: int = 1) -> None:
    """Donut par opérateur + légende HTML (nom, pourcentage) côte à côte."""
    from components.ui import legend_rows
    ops = list(df["Opérateur"])
    vals = [float(v) for v in df["Valeur" if "Valeur" in df else "Agences"]]
    tot = sum(vals) or 1.0
    c_left, c_right = st.columns([1.05, 1], gap="small")
    with c_left:
        show(create_donut_chart(ops, vals, [OP_COLORS[o] for o in ops], fmt_int(total), center_bottom, height), key)
    with c_right:
        st.markdown('<div style="height:14px"></div>' + legend_rows(
            [(OP_COLORS[o], o, fmt_pct_int(v / tot * 100, nd)) for o, v in zip(ops, vals)]), unsafe_allow_html=True)


def fmt_pct_int(p: float, nd: int = 1) -> str:
    return f"{fmt_dec(p, nd)}%"
