"""En-tête institutionnel : drapeau + intitulés à gauche ; titre du challenge et boutons FR / EN à droite."""
from __future__ import annotations

import streamlit as st

from components.ui import flag_data_uri
from data.data import DATA_END, DATA_START, DEFAULT_PERIOD


def sync_period(src: str, dst: str) -> None:
    """Recopie la période choisie dans le sélecteur `src` vers `dst` et vers l'état global."""
    v = st.session_state.get(src)
    if isinstance(v, (tuple, list)) and len(v) == 2:
        st.session_state["periode"] = tuple(v)
        st.session_state[dst] = tuple(v)


def _set_lang(lang: str) -> None:
    st.session_state["lang"] = lang
    if lang == "en":
        st.toast("English version coming soon — l'interface reste en français pour l'instant.", icon="🌐")


def create_header() -> None:
    st.session_state.setdefault("periode", DEFAULT_PERIOD)
    st.session_state.setdefault("lang", "fr")
    st.session_state.setdefault("periode_h", st.session_state["periode"])

    with st.container(key="header"):
        c_logo, c_title, c_fr, c_en = st.columns([4.0, 5.4, 0.5, 0.5], gap="small")
        c_logo.markdown(
            f'<div class="hdr"><img src="{flag_data_uri()}" alt="Togo">'
            '<div><div class="t1">RÉPUBLIQUE TOGOLAISE</div>'
            '<div class="t2">TRAVAIL - LIBERTÉ - PATRIE</div></div></div>', unsafe_allow_html=True)
        c_title.markdown('<div class="hdr-challenge">DATA CHALLENGE - ADMINISTRATION TERRITORIALE ET MOBILITÉ | DÉFI 1</div>',
                         unsafe_allow_html=True)
        for col, code in ((c_fr, "fr"), (c_en, "en")):
            with col:
                st.button(code.upper(), key=f"lang_{code}", on_click=_set_lang, args=(code,),
                          type="primary" if st.session_state["lang"] == code else "secondary", width="stretch")
