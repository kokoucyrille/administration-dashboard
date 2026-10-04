"""Page « Module en préparation » pour les menus non encore développés."""
from __future__ import annotations

import streamlit as st


def make_placeholder(title: str, icon: str):
    """Retourne une fonction de page Streamlit affichant un message élégant."""
    def _page():
        st.markdown(
            f'<div class="placeholder"><i class="fa-solid {icon}"></i><h2>{title}</h2>'
            f'<p>Module en préparation</p></div>', unsafe_allow_html=True)
    _page.__name__ = title.lower().replace(" ", "_")
    return _page
