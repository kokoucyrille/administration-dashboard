"""
Dashboard « Économie Numérique — Togo » (Streamlit).

Point d'entrée : `streamlit run app.py`
Chaque page vit dans pages/ ; l'en-tête, la barre de navigation et le CSS sont partagés ici.
"""
import streamlit as st

st.set_page_config(page_title="Économie Numérique – Togo", page_icon="assets/favicon.png", layout="wide",
                   initial_sidebar_state="expanded")

from components.header import create_header          # noqa: E402  (après set_page_config)
from components.navbar import create_navbar          # noqa: E402
from components.placeholder import make_placeholder  # noqa: E402
from components.styles import inject_css             # noqa: E402

# ---- Déclaration des pages (la navigation native est masquée : on utilise notre propre navbar) ----
PAGES = {
    "accueil": st.Page("views/accueil.py", title="Accueil", url_path="accueil", default=True),
    "services_numeriques": st.Page("views/services_numeriques.py", title="Services numériques", url_path="services-numeriques"),
    "infrastructures": st.Page("views/infrastructures.py", title="Infrastructures", url_path="infrastructures"),
    "recommandations": st.Page("views/recommandations.py", title="Recommandations", url_path="recommandations"),
    "zones_blanches": st.Page(make_placeholder("Zones blanches", "fa-tower-cell"), title="Zones blanches", url_path="zones-blanches"),
    "rapports_pdf": st.Page(make_placeholder("Rapports PDF", "fa-file-lines"), title="Rapports PDF", url_path="rapports-pdf"),
    "carte": st.Page(make_placeholder("Carte", "fa-map"), title="Carte", url_path="carte"),
    "metriques": st.Page(make_placeholder("Métriques", "fa-chart-simple"), title="Métriques", url_path="metriques"),
}
current = st.navigation(list(PAGES.values()), position="hidden")
current_key = next(k for k, p in PAGES.items() if p.url_path == current.url_path or (k == "accueil" and current.url_path == ""))

inject_css()
with st.container(key="topbar"):                    # bandeau fixe : header (68 px) + navbar (61 px)
    create_header()
    create_navbar(PAGES, current_key)
current.run()
