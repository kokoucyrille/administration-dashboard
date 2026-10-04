"""Petits éléments d'interface partagés : titres de page, panneaux, formats."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
_PANEL_HEIGHTS: dict[str, int] = {}      # clé de panneau -> hauteur (px), vidé par flush_panel_css()


@lru_cache(maxsize=1)
def flag_data_uri() -> str:
    """Drapeau du Togo encodé en base64 (utilisable dans le HTML injecté)."""
    raw = (ASSETS / "logo_togo.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def page_title(icon: str, title: str, subtitle: str) -> None:
    """Titre + sous-titre de page (icône Font Awesome à gauche)."""
    st.markdown(
        f'<div class="page-title"><div class="pi"><i class="fa-solid {icon}"></i></div>'
        f'<div><h1>{title}</h1><p>{subtitle}</p></div></div>', unsafe_allow_html=True)


@contextmanager
def panel(key: str, title: str, icon: str, height: int | None = None, menu: bool = False):
    """
    Carte blanche à bordure légère avec titre (icône + libellé ; `menu=True` ajoute un « ··· » décoratif, désactivé par défaut car sans action).
    `height` fixe la hauteur pour aligner les panneaux d'une même rangée.
    """
    if height:
        _PANEL_HEIGHTS[key] = height
    with st.container(key=f"panel_{key}"):
        dots = '<span class="dots">&middot;&middot;&middot;</span>' if menu else ""
        st.markdown(f'<div class="panel-title"><i class="fa-solid {icon}"></i><span>{title}</span>{dots}</div>',
                    unsafe_allow_html=True)
        yield


def legend_rows(items: list[tuple[str, str, str]]) -> str:
    """HTML de légende : (couleur, libellé, valeur) -> pastille + libellé + valeur alignée à droite."""
    rows = "".join(
        f'<div class="leg-row"><span><span class="legend-dot" style="background:{c}"></span>{lab}</span><b>{val}</b></div>'
        for c, lab, val in items)
    return rows


def flush_panel_css() -> None:
    """Émet UNE seule balise <style> avec la hauteur fixe de chaque panneau (à appeler en fin de page)."""
    if _PANEL_HEIGHTS:
        css = "".join(f".st-key-panel_{k}{{height:{h}px !important;flex:0 0 auto !important;}}" for k, h in _PANEL_HEIGHTS.items())
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        _PANEL_HEIGHTS.clear()
