"""
Sidebar verticale de filtres.

Chaque page possède son jeu de filtres (cf. PAGE_FILTERS). Les valeurs choisies sont des
« brouillons » (widgets `w_<page>_<nom>`) ; elles ne deviennent effectives qu'au clic sur
« Appliquer les filtres » (copiées dans `applied_<page>`). « Réinitialiser » remet tout à zéro.
La période est globale et s'applique immédiatement (synchronisée avec celle de l'en-tête).
"""
from __future__ import annotations

import streamlit as st

from components.header import sync_period
from components.ui import flag_data_uri
from data import data as D

# nom du filtre -> (libellé, icône Font Awesome, type de widget, valeur par défaut)
FIELDS = {
    "region": ("Région", "fa-location-dot", "select", D.ALL_REGIONS),
    "prefecture": ("Préfecture", "fa-building", "select", D.ALL_PREFS),
    "province": ("Province", "fa-building-columns", "select", D.ALL_PROVINCES),
    "commune": ("Commune", "fa-location-crosshairs", "select", D.ALL_COMMUNES),
    "operateur": ("Opérateur", "fa-tower-cell", "select", D.ALL_OPS),
    "type_paiement": ("Type de service", "fa-layer-group", "select", D.ALL_TYPES),
    "infra_type": ("Type d'infrastructure", "fa-tower-broadcast", "select", D.ALL_INFRA),
    "technologie": ("Technologie", "fa-wifi", "select", D.ALL_TECH),
    "operateurs": ("Opérateur / Fournisseur", "fa-tower-cell", "multi", []),
    "types": ("Type de service", "fa-layer-group", "multi", []),
}

PAGE_FILTERS = {
    "accueil": {"title": "FILTRES", "fields": ["region", "prefecture", "commune", "operateur", "type_paiement"]},
    "infrastructures": {"title": "FILTRES", "fields": ["region", "province", "commune", "infra_type", "operateur", "technologie"]},
    "recommandations": {"title": "FILTRES", "fields": ["region", "prefecture", "commune", "operateur", "type_paiement", "technologie"]},
    "services": {"title": "FILTRES AVANCÉS", "fields": ["region", "prefecture", "commune", "types", "operateurs", "technologie"]},
}
TERRITORY_ALL = {"region": D.ALL_REGIONS, "prefecture": D.ALL_PREFS, "province": D.ALL_PROVINCES, "commune": D.ALL_COMMUNES}


# --------------------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------------------
def _key(page: str, name: str) -> str:
    return f"w_{page}_{name}"


def _pref_name(page: str) -> str:
    return "province" if "province" in PAGE_FILTERS[page]["fields"] else "prefecture"


def _on_region(page: str) -> None:
    """Quand la région change, les niveaux inférieurs reviennent à « Toutes… »."""
    st.session_state[_key(page, _pref_name(page))] = TERRITORY_ALL[_pref_name(page)]
    st.session_state[_key(page, "commune")] = D.ALL_COMMUNES


def _on_pref(page: str) -> None:
    st.session_state[_key(page, "commune")] = D.ALL_COMMUNES


def _apply(page: str) -> None:
    names = PAGE_FILTERS[page]["fields"]
    st.session_state[f"applied_{page}"] = {n: st.session_state[_key(page, n)] for n in names if _key(page, n) in st.session_state}


def _reset(page: str) -> None:
    for n in PAGE_FILTERS[page]["fields"]:
        st.session_state[_key(page, n)] = FIELDS[n][3]
    st.session_state[f"applied_{page}"] = {}
    st.session_state["periode"] = st.session_state["periode_h"] = st.session_state["periode_s"] = D.DEFAULT_PERIOD


# --------------------------------------------------------------------------------------
# Rendu
# --------------------------------------------------------------------------------------
def _label(text: str, icon: str) -> None:
    st.markdown(f'<div class="f-label"><i class="fa-solid {icon}"></i><span>{text}</span></div>', unsafe_allow_html=True)


def _options(page: str, name: str) -> list:
    """Options d'un filtre (cascade région > préfecture > commune selon les brouillons)."""
    ss = st.session_state
    region = ss.get(_key(page, "region"), D.ALL_REGIONS)
    region = None if region == D.ALL_REGIONS else region
    pname = _pref_name(page)
    pref = ss.get(_key(page, pname), TERRITORY_ALL[pname])
    pref = None if pref in (D.ALL_PREFS, D.ALL_PROVINCES) else pref
    return {
        "region": [D.ALL_REGIONS] + D.REGIONS,
        "prefecture": [D.ALL_PREFS] + D.prefectures_of(region),
        "province": [D.ALL_PROVINCES] + D.prefectures_of(region),
        "commune": [D.ALL_COMMUNES] + D.communes_of(region, pref),
        "operateur": [D.ALL_OPS] + D.OPERATEURS,
        "type_paiement": [D.ALL_TYPES] + D.PAYMENT_MODES,
        "infra_type": [D.ALL_INFRA] + D.INFRA_TYPES,
        "technologie": [D.ALL_TECH] + D.TECHNOLOGIES,
        "operateurs": D.OPERATEURS,
        "types": D.SERVICE_TYPES,
    }[name]


def _has_pending(page: str) -> bool:
    """Vrai si un filtre a été modifié sans avoir été appliqué (brouillon différent de la valeur appliquée)."""
    ss = st.session_state
    applied = ss.get(f"applied_{page}", {})
    return any(_key(page, n) in ss and ss[_key(page, n)] != applied.get(n, FIELDS[n][3]) for n in PAGE_FILTERS[page]["fields"])


def create_sidebar(page: str) -> dict:
    """Dessine la sidebar de la page et renvoie le dictionnaire de filtres APPLIQUÉS."""
    spec = PAGE_FILTERS[page]
    ss = st.session_state
    applied = ss.setdefault(f"applied_{page}", {})
    ss.setdefault("periode", D.DEFAULT_PERIOD)
    ss.setdefault("periode_s", ss["periode"])

    with st.sidebar:
        st.markdown(f'<div class="f-title"><i class="fa-solid fa-filter"></i><span>{spec["title"]}</span></div>',
                    unsafe_allow_html=True)
        _label("Période", "fa-calendar-days")
        st.date_input("Période", key="periode_s", format="DD/MM/YYYY", min_value=D.DATA_START, max_value=D.DATA_END,
                      label_visibility="collapsed", on_change=sync_period, args=("periode_s", "periode_h"))

        for name in spec["fields"]:
            label, icon, kind, default = FIELDS[name]
            key = _key(page, name)
            if key not in ss:                                   # restaure la valeur appliquée
                ss[key] = applied.get(name, default)
            opts = _options(page, name)
            if kind == "select" and ss[key] not in opts:        # sécurité : valeur devenue invalide
                ss[key] = default
            if kind == "multi":
                ss[key] = [v for v in ss[key] if v in opts]
            _label(label, icon)
            cb = {"region": (_on_region, (page,)), "prefecture": (_on_pref, (page,)), "province": (_on_pref, (page,))}.get(name)
            kw = {"on_change": cb[0], "args": cb[1]} if cb else {}
            if kind == "select":
                st.selectbox(label, opts, key=key, label_visibility="collapsed", **kw)
            else:
                st.multiselect(label, opts, key=key, label_visibility="collapsed", placeholder=FIELDS[name][3] or "Tous", **kw)

        hint = ('<i class="fa-solid fa-circle-info"></i><span>Modifications non appliquées</span>' if _has_pending(page) else "")
        st.markdown(f'<div class="f-hint">{hint}</div>', unsafe_allow_html=True)
        st.button("Appliquer les filtres", key=f"apply_{page}", type="primary",
                  width="stretch", on_click=_apply, args=(page,))
        st.button("Réinitialiser", key=f"reset_{page}", type="secondary",
                  width="stretch", on_click=_reset, args=(page,))
        st.markdown(f'<div class="side-foot"><img src="{flag_data_uri()}" alt=""><div><b>Togo Numérique</b>'
                    f'<span>Plus proche de vous</span></div></div>', unsafe_allow_html=True)
    return build_filters(page)


def build_filters(page: str) -> dict:
    """Convertit les valeurs appliquées en filtres exploitables par la couche de données."""
    a = st.session_state.get(f"applied_{page}", {})
    none_if = lambda v, *alls: None if v in alls or v is None else v          # noqa: E731
    pref = a.get("prefecture", a.get("province"))
    f = {
        "period": tuple(st.session_state.get("periode", D.DEFAULT_PERIOD)),
        "region": none_if(a.get("region"), D.ALL_REGIONS),
        "prefecture": none_if(pref, D.ALL_PREFS, D.ALL_PROVINCES),
        "commune": none_if(a.get("commune"), D.ALL_COMMUNES),
        "operateurs": ([a["operateur"]] if none_if(a.get("operateur"), D.ALL_OPS) else a.get("operateurs") or []),
        "types": ([a["type_paiement"]] if none_if(a.get("type_paiement"), D.ALL_TYPES) else a.get("types") or []),
        "infra_type": none_if(a.get("infra_type"), D.ALL_INFRA),
        "technologie": none_if(a.get("technologie"), D.ALL_TECH),
    }
    return f
