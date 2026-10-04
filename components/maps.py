"""
Cartographie du Togo.

* create_region_map()   : petite carte Plotly (sans fond) de l'accueil, régions en dégradé de vert.
* create_map()          : carte Folium interactive (fond clair, zoom, échelle, boussole, légende, marqueurs)
                          pour les pages Infrastructures et Services numériques.
"""
from __future__ import annotations

import json

import folium
import numpy as np
import pandas as pd
import plotly.colors as pc
import plotly.graph_objects as go
import streamlit as st
from branca.element import Element, MacroElement
from jinja2 import Template
import streamlit.components.v1 as components

from components.charts import show
from data import data as D

TOGO_BOUNDS = [[6.0, -0.25], [11.2, 1.9]]
TOGO_CENTER = [8.62, 0.98]
GREEN_SCALE = [[0, "#cfe8da"], [1, "#016b4b"]]

# légendes
SERVICES_LEGEND = [("Très élevée", "#016b4b"), ("Élevée", "#1488ee"), ("Moyenne", "#fec902"),
                   ("Faible", "#f20e36"), ("Très faible", "#8b3fe0")]
INFRA_LEGEND = [("Très bonne", "#0b6b4b"), ("Bonne", "#35a37a"), ("Moyenne", "#7cc99f"),
                ("Faible", "#fbe27a"), ("Très faible", "#bfeadb")]


# --------------------------------------------------------------------------------------
# Accueil : carte Plotly des régions
# --------------------------------------------------------------------------------------
def region_colors(parts: dict) -> dict:
    """Couleur de chaque région selon sa part (dégradé vert clair -> vert institutionnel)."""
    vals = {r: v for r, v in parts.items() if v == v}                 # ignore NaN
    lo, hi = min(vals.values()), max(vals.values())
    out = {}
    for r, v in vals.items():
        t = 0.5 if hi == lo else (v - lo) / (hi - lo)
        out[r] = pc.sample_colorscale(GREEN_SCALE, [0.12 + 0.88 * t])[0]
    return out


def _polygons(geometry: dict):
    """Anneaux extérieurs (liste de listes de (lon, lat)) d'une géométrie Polygon / MultiPolygon."""
    polys = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return [p[0] for p in polys]


def create_region_map(parts: dict, height: int = 190) -> go.Figure:
    """
    Carte des régions dessinée directement avec des polygones Plotly (aucun fond externe requis).
    Les préfectures sont nuancées dans la couleur de leur région (effet « mosaïque » de la maquette).
    """
    colors = region_colors(parts)
    rng = np.random.default_rng(5)
    fig = go.Figure()
    for ft in D.prefectures_geojson()["features"]:
        reg, name = ft["properties"]["region"], ft["properties"]["label"]
        if reg in colors:
            rgb = [int(x) for x in colors[reg].strip("rgb()").split(",")]
            k = rng.uniform(-12, 12)
            fill = "rgb({},{},{})".format(*[max(0, min(255, int(c + k))) for c in rgb])
        else:
            fill = "#e6eeee"                                          # hors sélection
        for ring in _polygons(ft["geometry"]):
            xs, ys = zip(*ring)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor=fill, line=dict(color="#ffffff", width=0.8),
                                     hoverinfo="text", text=f"{reg} — {name}", showlegend=False))
    fig.update_xaxes(visible=False, constrain="domain")
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1.0)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=False, hoverlabel=dict(font_size=12))
    return fig


def region_map_legend(parts: dict) -> list[tuple[str, str, str]]:
    colors = region_colors(parts)
    return [(colors[r], r, f"{D.fmt_dec(v, 1)}%") for r, v in parts.items() if v == v]


# --------------------------------------------------------------------------------------
# Folium : éléments communs
# --------------------------------------------------------------------------------------
class _HomeButton(MacroElement):
    """Bouton « recentrer sur le Togo » sous les boutons de zoom."""
    _template = Template("""
        {% macro script(this, kwargs) %}
        var HomeCtl = L.Control.extend({
            options: {position: 'topleft'},
            onAdd: function (map) {
                var c = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                var a = L.DomUtil.create('a', '', c);
                a.href = '#'; a.title = 'Recentrer'; a.innerHTML = '&#9678;'; a.style.fontSize = '18px';
                L.DomEvent.on(a, 'click', function (e) { L.DomEvent.stop(e);
                    {{ this._parent.get_name() }}.fitBounds({{ this.bounds }}); });
                return c;
            }});
        {{ this._parent.get_name() }}.addControl(new HomeCtl());
        {% endmacro %}""")

    def __init__(self, bounds):
        super().__init__()
        self._name = "HomeButton"
        self.bounds = bounds


def _legend_html(title: str, entries: list[tuple[str, str]]) -> str:
    rows = "".join(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                   f'<span style="width:11px;height:11px;border-radius:50%;background:{c};display:inline-block"></span>{lab}</div>'
                   for lab, c in entries)
    return (f'<div style="position:absolute;top:12px;right:12px;z-index:9999;background:#fff;padding:8px 14px;'
            f'border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.2);font:600 13px \'Nunito Sans\',Arial,sans-serif;color:#0a4a9a">'
            f'{rows}</div>')


_COMPASS = ('<div style="position:absolute;bottom:26px;right:14px;z-index:9999;width:34px;height:34px;border-radius:50%;'
            'background:#fff;box-shadow:0 1px 5px rgba(0,0,0,.25);display:flex;flex-direction:column;align-items:center;'
            'justify-content:center;font:800 10px Arial;color:#0a4a9a"><span>N</span>'
            '<span style="width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;'
            'border-bottom:12px solid #0a4a9a"></span></div>')


# Fond de carte sans clé API. Pour un autre fournisseur (Mapbox, Stadia, …), modifier TILE_URL / TILE_ATTR.
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_ATTR = "&copy; contributeurs d'OpenStreetMap"
# Filtre CSS : désature et éclaircit les tuiles (rendu pastel proche des maquettes)
_TILE_CSS = ("<style>.leaflet-tile-pane{filter:grayscale(.55) saturate(.8) brightness(1.07) contrast(.92);}"
             ".leaflet-container{background:#dcebf3;font-family:'Nunito Sans',Arial,sans-serif;}"
             ".leaflet-control-zoom a{color:#0a4a9a;font-weight:700;}</style>")


def _base_map() -> folium.Map:
    m = folium.Map(location=TOGO_CENTER, zoom_start=7, tiles=None, control_scale=True,
                   zoom_control=True, min_zoom=6, max_zoom=13, attribution_control=True,
                   zoom_snap=0.1, zoom_delta=0.5)
    folium.TileLayer(tiles=TILE_URL, attr=TILE_ATTR, name="Fond de carte", max_zoom=19).add_to(m)
    m.get_root().html.add_child(Element(_TILE_CSS))
    m.fit_bounds(TOGO_BOUNDS, padding=(6, 6))
    m.add_child(_HomeButton(TOGO_BOUNDS))
    return m


def _add_cities(m: folium.Map) -> None:
    """Marqueurs des villes principales."""
    for name, (lat, lon) in D.CITIES.items():
        folium.CircleMarker([lat, lon], radius=4, color="#fff", weight=1.5, fill=True, fill_color="#0a4a9a",
                            fill_opacity=1, tooltip=name).add_to(m)


def build_map(level: str, df: pd.DataFrame, legend: list[tuple[str, str]], value_label: str = "Valeur",
              fmt=D.fmt_int, cls_col: str = "cls") -> folium.Map:
    """
    Construit la carte Folium (sans l'afficher : permet de la tester isolément).
    level : "Région" | "Préfecture" (polygones colorés par classe) | "Commune" (bulles par canton)
    df    : colonnes Territoire, valeur (`Valeur`), classe (`cls`, 0 = classe la plus haute de la légende,
            NaN = hors sélection) ; pour Préfecture : colonne `code` (nom source de la préfecture).
    """
    m = _base_map()
    palette = [c for _, c in legend]
    labels = [l for l, _ in legend]

    if level in ("Région", "Préfecture"):
        gj = json.loads(json.dumps(D.regions_geojson() if level == "Région" else D.prefectures_geojson()))
        key_col = "Territoire" if level == "Région" else "code"
        info = {r[key_col]: r for _, r in df.iterrows()}
        for ft in gj["features"]:
            nm = ft["properties"]["name"]
            r = info.get(nm)
            ft["properties"]["_txt"] = (f"{fmt(r['Valeur'])} · {labels[int(r[cls_col])]}" if r is not None and r[cls_col] == r[cls_col]
                                        else "Hors sélection")
            ft["properties"]["_nm"] = ft["properties"].get("label", nm)
            ft["properties"]["_cls"] = int(r[cls_col]) if r is not None and r[cls_col] == r[cls_col] else -1

        def style(ft):
            c = ft["properties"]["_cls"]
            return {"fillColor": palette[c] if c >= 0 else "#e8eef0", "color": "#ffffff", "weight": 1.2,
                    "fillOpacity": 0.82 if c >= 0 else 0.35}

        folium.GeoJson(gj, style_function=style, highlight_function=lambda f: {"weight": 2.5, "color": "#0a4a9a"},
                       tooltip=folium.GeoJsonTooltip(fields=["_nm", "_txt"], aliases=["", value_label + " :"],
                                                     sticky=True)).add_to(m)
    else:                                                           # bulles par canton / commune
        folium.GeoJson(D.regions_geojson(), style_function=lambda f: {"fillColor": "#f4f9f6", "color": "#8fb9a8",
                                                                     "weight": 1.2, "fillOpacity": 0.35}).add_to(m)
        d = df.dropna(subset=["lat", "lon", cls_col])
        vmax = float(d["Valeur"].max()) or 1.0
        for _, r in d.iterrows():
            folium.CircleMarker(
                [float(r["lat"]), float(r["lon"])], radius=3 + 8 * float(np.sqrt(r["Valeur"] / vmax)), weight=0.8,
                color="#ffffff", fill=True, fill_color=palette[int(r[cls_col])], fill_opacity=0.88,
                tooltip=f"{r['Territoire']} ({r['Préfecture']}) — {fmt(r['Valeur'])}").add_to(m)

    _add_cities(m)
    m.get_root().html.add_child(Element(_legend_html("", [(l, c) for l, c in legend])))
    m.get_root().html.add_child(Element(_COMPASS))
    return m


def create_map(level: str, df: pd.DataFrame, legend: list[tuple[str, str]], key: str, height: int = 420,
               value_label: str = "Valeur", fmt=D.fmt_int, cls_col: str = "cls") -> None:
    """Affiche la carte dans Streamlit (zoom, échelle, boussole, légende, marqueurs des villes)."""
    m = build_map(level, df, legend, value_label, fmt, cls_col)
    # Iframe à hauteur fixe : plus fiable que st_folium (dont la hauteur peut s'effondrer selon la version de Streamlit)
    components.html(m.get_root().render(), height=height, scrolling=False)


# --------------------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------------------
def classify_rank(values: pd.Series, n: int = 5) -> pd.Series:
    """Classes par rang (0 = valeurs les plus élevées ... 4 = les plus faibles), équilibrées en effectif."""
    s = values.astype(float)
    ranks = s.rank(method="first", ascending=False)
    cls = np.floor((ranks - 1) / max(len(s), 1) * n).clip(0, n - 1)
    return cls.where(s.notna())


def classify_thresholds(values: pd.Series, edges=(85, 70, 58, 50)) -> pd.Series:
    """Classes absolues pour un taux de couverture : >=85 très bonne, >=70 bonne, >=58 moyenne, >=50 faible."""
    s = values.astype(float)
    cls = pd.Series(4, index=s.index)
    for i, e in reversed(list(enumerate(edges))):
        cls = cls.where(~(s >= e), i)
    return cls.where(s.notna())
