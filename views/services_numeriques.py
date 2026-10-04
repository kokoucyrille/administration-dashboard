"""Page « Services numériques » — e-administration, e-paiement, e-santé… (maquette n°2)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, maps, tables
from components.kpi_cards import create_kpi_row
from components.sidebar import create_sidebar
from components.ui import flush_panel_css, page_title, panel
from data import data as D

f = create_sidebar("services")
page_title("fa-wifi", "Services numériques", "État des services numériques au Togo (e-administration, e-paiement, e-santé, etc.).")

# ---- KPI (titre + valeur uniquement) -------------------------------------------------------
k = D.services_kpis(f)
create_kpi_row([
    {"title": "Utilisateurs des services numériques", "value": D.fmt_int(k["users"]), "icon": "fa-mobile-screen", "variant": "green"},
    {"title": "Transactions en ligne", "value": D.fmt_int(k["transactions"]), "icon": "fa-credit-card", "variant": "blue"},
    {"title": "Paiements mobiles", "value": D.fmt_int(k["paiements"]), "icon": "fa-coins", "variant": "yellow"},
    {"title": "Services e-administration", "value": D.fmt_int(k["eadmin"]), "icon": "fa-users", "variant": "purple"},
    {"title": "Services e-santé", "value": D.fmt_int(k["esante"]), "icon": "fa-suitcase-medical", "variant": "teal"},
])

# ---- Barre de contrôle : Vue par | Indicateur principal | Afficher + export ------------------
LEVELS = ["Région", "Préfecture", "Commune"]
c1, c2, c3 = st.columns([1.0, 1.15, 1.0], gap="small")
with c1:
    with st.container(key="ctl_vue"):
        a, b = st.columns([0.22, 1.0], gap="small", vertical_alignment="center")
        a.markdown('<span class="ctl-label">Vue par</span>', unsafe_allow_html=True)
        level = b.segmented_control("Vue par", LEVELS, default="Région", key="svc_level", label_visibility="collapsed") or "Région"
with c2:
    with st.container(key="ctl_ind"):
        a, b = st.columns([0.5, 1.0], gap="small", vertical_alignment="center")
        a.markdown('<span class="ctl-label">Indicateur principal</span>', unsafe_allow_html=True)
        indicator = b.selectbox("Indicateur principal", list(D.SERV_INDICATORS), key="svc_indicator", label_visibility="collapsed")
with c3:
    with st.container(key="ctl_view"):
        a, b, c = st.columns([0.25, 0.55, 0.2], gap="small", vertical_alignment="center")
        a.markdown('<span class="ctl-label">Afficher</span>', unsafe_allow_html=True)
        mode = b.segmented_control("Afficher", ["Carte", "Liste"], default="Carte", key="svc_mode", label_visibility="collapsed") or "Carte"

# données du territoire selon la vue et l'indicateur choisis
lv = D.services_by_level(f, level, indicator)
if not lv.empty:
    lv["cls"] = maps.classify_rank(lv["Valeur"])
with c3:
    with c:
        export = lv.drop(columns=[x for x in ("cls", "code", "share") if x in lv.columns]).copy() if not lv.empty else pd.DataFrame()
        st.download_button("Exporter", export.to_csv(index=False).encode("utf-8-sig"), "services_numeriques.csv", "text/csv",
                           key="dl_btn", help="Exporter les données affichées (CSV)", width="stretch")

# ---- Corps : carte/liste | donut + top 5 | indicateurs clés + évolution ----------------------
c_map, c_mid, c_right = st.columns([1.3, 1.08, 1.0], gap="small")

with c_map:
    with panel("map", f"Répartition {'des utilisateurs' if indicator.startswith('Utilisateurs') else 'de « ' + indicator.lower() + ' »'} par {level.lower()}",
               "fa-location-dot", height=473, menu=False):
        if lv.empty:
            st.markdown('<div style="color:#7b8794;padding:30px 0">Aucune donnée pour cette sélection.</div>', unsafe_allow_html=True)
        elif mode == "Carte":
            maps.create_map(level, lv, maps.SERVICES_LEGEND, key=f"map_services_{level}", height=400, value_label=indicator)
        else:
            show = lv.sort_values("Valeur", ascending=False).head(60)
            cols = [c for c in ("Territoire", "Préfecture", "Région", "Valeur") if c in show.columns]
            table = tables.create_table(show[cols].copy(),
                                        formats={"Valeur": D.fmt_int})
            st.markdown(f'<div class="list-scroll">{table}</div>', unsafe_allow_html=True)

with c_mid:
    with panel("op", "Répartition des services par opérateur", "fa-chart-pie", height=239, menu=False):
        df, total = D.services_operateurs(f)
        charts.operator_donut(df, total, "Utilisateurs", "donut_services", height=180)
    with panel("top", "Top 5 des localités par nombre d'utilisateurs", "fa-users", height=220, menu=False):
        st.markdown(charts.create_top5(D.services_top_localites(f)), unsafe_allow_html=True)

with c_right:
    with panel("ind", "Indicateurs clés", "fa-chart-simple", height=239, menu=False):
        st.markdown(charts.create_key_indicators(D.services_rates(f), D.RATES_DELTA), unsafe_allow_html=True)
    with panel("evo", "Évolution des services numériques", "fa-chart-line", height=220, menu=False):
        ev = D.services_evolution(f)
        ev["Jour"] = ev["Date"].map(lambda d: d.strftime("%d/%m"))
        colors = {"Paiements mobiles": "#016b4b", "E-administration": "#ffc903", "E-santé": "#1488ee", "Autres": "#e040fb"}
        charts.show(charts.create_line_chart(ev, "Jour", "Valeur", "Service", colors, height=160), "line_services")

flush_panel_css()
