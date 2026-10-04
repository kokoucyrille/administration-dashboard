"""Page « Accueil » — vue d'ensemble des indicateurs clés du numérique au Togo."""
from __future__ import annotations

import streamlit as st

from components import charts, maps, tables
from components.kpi_cards import create_kpi_row
from components.sidebar import create_sidebar
from components.styles import OP_COLORS, THEME
from components.ui import flush_panel_css, legend_rows, page_title, panel
from data import data as D

f = create_sidebar("accueil")                       # filtres appliqués (sidebar de gauche)
page_title("fa-chart-simple", "Vue d'ensemble", "Indicateurs clés du numérique au Togo.")

# ---- Rangée de KPI (titre + valeur uniquement) ---------------------------------------------
k = D.accueil_kpis(f)
create_kpi_row([
    {"title": "Agents mobile money", "value": D.fmt_int(k["agents_mm"]), "icon": "fa-database", "variant": "green"},
    {"title": "Agences télécoms", "value": D.fmt_int(k["agences"]), "icon": "fa-tower-cell", "variant": "green"},
    {"title": "Agents financiers", "value": D.fmt_dec(k["agents_fin"], 2), "icon": "fa-building-columns", "variant": "yellow"},
    {"title": "Datacenters", "value": D.fmt_int(k["datacenters"]), "icon": "fa-server", "variant": "gray"},
    {"title": "Population 2026", "value": D.fmt_int(k["population"]), "icon": "fa-users", "variant": "green"},
    {"title": "Zones blanches", "value": D.fmt_int(k["zones_blanches"]), "icon": "fa-tower-cell", "variant": "red"},
])

# ---- Rangée 2 : barres + donut -----------------------------------------------------------------
c1, c2 = st.columns([1.14, 1.0], gap="small")
with c1:
    with panel("agents", "Agents mobile money par région", "fa-chart-simple", height=278):
        df = D.accueil_agents_region(f)
        bar_colors = ["#016949", "#ffc903", "#ee1438", "#59b78d", "#df9401"]
        charts.show(charts.create_bar_chart(df, "Région", "Agents", bar_colors, height=176, hover_unit=" agents"), "bar_agents")
        st.markdown(f'<div style="text-align:center;color:{THEME["blue_link"]};font-size:12.5px;margin-top:-4px">'
                    f'<span class="legend-dot" style="background:{THEME["green"]};width:9px;height:9px"></span>'
                    f'Agents mobile money</div>', unsafe_allow_html=True)
with c2:
    with panel("agences", "Agences télécoms par opérateur", "fa-chart-pie", height=278):
        df = D.accueil_agences_operateur(f)
        charts.operator_donut(df.rename(columns={"Agences": "Valeur"}), float(df["Agences"].sum()), "Agences",
                              "donut_agences", height=210, nd=0)

# ---- Rangée 3 : tableau + carte + courbes -----------------------------------------------
c3, c4, c5 = st.columns([1.21, 1.0, 1.24], gap="small")
with c3:
    with panel("perf", "Performances par région", "fa-gear", height=252):
        tables.render_table(D.accueil_performances(f), formats=tables.FMT_PERF, up_cols=("Évolution",))
with c4:
    with panel("couv", "Couverture réseau par région", "fa-tower-broadcast", height=252):
        parts = D.accueil_couverture(f).set_index("Région")["Part"].to_dict()
        m_col, l_col = st.columns([0.8, 1.0], gap="small")
        with m_col:
            charts.show(maps.create_region_map(parts, height=185), "map_couv")
        with l_col:
            st.markdown('<div style="height:6px"></div>' + legend_rows(maps.region_map_legend(parts)).replace("margin: 12px 0", "margin: 8px 0"),
                        unsafe_allow_html=True)
with c5:
    with panel("ventes", "Évolution des ventes par mode de paiement", "fa-arrow-trend-up", height=252):
        ev = D.accueil_ventes_evolution(f)
        ev["Jour"] = ev["Date"].map(lambda d: d.strftime("%d/%m"))
        colors = {"Espèces": THEME["green"], "Carte bancaire": "#ffc903", "Mobile money": "#f20e36", "Virement": "#a24df0"}
        charts.show(charts.create_line_chart(ev, "Jour", "Valeur", "Mode", colors, height=190), "line_ventes")

flush_panel_css()
