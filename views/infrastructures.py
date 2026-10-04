"""Page « Infrastructures » — état des réseaux et services numériques au Togo (maquette n°3)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, maps
from components.kpi_cards import create_kpi_row
from components.sidebar import create_sidebar
from components.styles import OP_COLORS
from components.ui import flush_panel_css, page_title, panel
from data import data as D

f = create_sidebar("infrastructures")
page_title("fa-tower-cell", "Infrastructures", "État des infrastructures des réseaux et des services numériques au Togo.")

# ---- KPI (titre + valeur uniquement) -------------------------------------------------------
k = D.infra_kpis(f)
create_kpi_row([
    {"title": "Stations de téléphonie mobile", "value": D.fmt_int(k["stations"]), "icon": "fa-tower-cell", "variant": "green"},
    {"title": "Sites Internet", "value": D.fmt_int(k["sites"]), "icon": "fa-wifi", "variant": "blue"},
    {"title": "Fibre optique (km)", "value": D.fmt_int(k["fibre"]), "icon": "fa-share-nodes", "variant": "yellow"},
    {"title": f"Couverture {k['tech']}", "value": f"{D.fmt_dec(k['couverture'], 1)} %", "icon": "fa-satellite-dish", "variant": "ghost"},
    {"title": "Points d'accès publics", "value": D.fmt_int(k["points"]), "icon": "fa-building", "variant": "teal"},
])

# ---- Corps : carte (gauche) | donut + qualité (centre) | top 5 + évolution 4G (droite) ----
c_map, c_mid, c_right = st.columns([1.3, 1.08, 1.0], gap="small")

with c_map:
    with panel("map", "Couverture du réseau mobile par région", "fa-location-dot", height=514, menu=False):
        mv = D.infra_map_values(f)
        df = pd.DataFrame({"code": mv["prefecture"], "Territoire": mv["label"], "Région": mv["region"], "Valeur": mv["value"]})
        df["cls"] = maps.classify_thresholds(df["Valeur"])
        maps.create_map("Préfecture", df, maps.INFRA_LEGEND, key="map_infra", height=440,
                        value_label=f"Couverture {k['tech']}", fmt=lambda v: f"{D.fmt_dec(v, 1)} %")

with c_mid:
    with panel("op", "Répartition des infrastructures par opérateur", "fa-chart-pie", height=250, menu=False):
        df, total, unit = D.infra_operateurs(f)
        charts.operator_donut(df, total, unit, "donut_infra", height=190)
    with panel("qual", "Qualité des services réseau", "fa-signal", height=250, menu=False):
        st.markdown(charts.create_quality_block(D.infra_qualite(f)), unsafe_allow_html=True)

with c_right:
    top, unit = D.infra_top_localites(f)
    with panel("top", f"Top 5 des localités par nombre de {unit}", "fa-location-dot", height=250, menu=False):
        st.markdown(charts.create_top5(top), unsafe_allow_html=True)
    with panel("evo", f"Évolution de la couverture {k['tech']}" if f.get("technologie") else "Évolution de la couverture 4G",
               "fa-chart-line", height=250, menu=False):
        ev = D.infra_cov4g_evolution(f)
        charts.show(charts.create_line_chart(ev, "Mois", "Couverture", "Opérateur", OP_COLORS, height=185, ypct=True,
                                             yrange=[0, 100]), "line_cov4g")

flush_panel_css()
