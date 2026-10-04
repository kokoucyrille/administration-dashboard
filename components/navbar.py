"""Barre de navigation horizontale (vert foncé) ; l'entrée active est jaune/or."""
from __future__ import annotations

import streamlit as st

# (libellé, icône [indicatif], clé de page, poids de colonne). L'icône réellement affichée est définie
# par index (.st-key-nav_<i>) dans components/styles.py.
NAV_ITEMS = [
    ("Économie Numérique", "filter_alt", "accueil", 1.55),
    ("Accueil", "home", "accueil", 1.0),
    ("Infrastructures", "cell_tower", "infrastructures", 1.5),
    ("Services numériques", "wifi", "services_numeriques", 1.75),
    ("Recommandations", "lightbulb", "recommandations", 1.7),
    ("Rapports PDF", "description", "rapports_pdf", 1.4),
    ("Carte", "map", "carte", 1.0),
    ("Métriques", "bar_chart", "metriques", 1.25),
]


def create_navbar(pages: dict, current: str) -> None:
    """`pages` : clé -> st.Page ; `current` : clé de la page affichée (menu actif en jaune)."""
    with st.container(key="navbar"):
        cols = st.columns([w for *_, w in NAV_ITEMS], gap="small")
        for i, (col, (label, icon, key, _)) in enumerate(zip(cols, NAV_ITEMS)):
            is_active = key == current and label != "Économie Numérique"
            with col:
                if st.button(label, key=f"nav_{i}", type="primary" if is_active else "secondary", width="stretch"):
                    st.switch_page(pages[key])
