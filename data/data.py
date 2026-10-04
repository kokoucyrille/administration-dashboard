"""
Données synthétiques du dashboard « Économie Numérique – Togo ».

Principe
--------
* Les totaux nationaux (par défaut, tout le Togo, août 2025) reproduisent EXACTEMENT les valeurs
  visibles sur les maquettes (19 788 agents, 3 842 760 utilisateurs, 2 834 stations, 72,3 %, …).
* Chaque indicateur est ventilé par région ; la somme des régions redonne le total national.
* Les filtres (région > préfecture > commune/canton, opérateur, type de service, période,
  technologie) recalculent les valeurs à partir de ces ventilations.

Tous les chiffres sont fictifs : ils servent uniquement à démontrer l'interface.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent

# --------------------------------------------------------------------------------------
# Constantes générales
# --------------------------------------------------------------------------------------
REGIONS = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
OPERATEURS = ["Togocom", "Moov", "Yas", "Autres"]
SERVICE_TYPES = ["Paiements mobiles", "E-administration", "E-santé", "Autres"]
PAYMENT_MODES = ["Espèces", "Carte bancaire", "Mobile money", "Virement"]
INFRA_TYPES = ["Stations de téléphonie mobile", "Sites Internet", "Points d'accès publics", "Fibre optique (km)"]
TECHNOLOGIES = ["2G", "3G", "4G", "5G"]

ALL_REGIONS, ALL_PREFS, ALL_COMMUNES = "Toutes les régions", "Toutes les préfectures", "Toutes les communes"
ALL_PROVINCES = "Toutes les provinces"
ALL_OPS, ALL_TYPES, ALL_INFRA, ALL_TECH = (
    "Tous les opérateurs", "Tous les types", "Tous les types", "Toutes les technologies")

DATA_START, DATA_END = date(2025, 1, 1), date(2025, 8, 31)       # bornes du sélecteur de période
AUG_START, AUG_END = date(2025, 8, 1), date(2025, 8, 31)         # période de référence des maquettes
DEFAULT_PERIOD = (AUG_START, AUG_END)

# Libellés accentués des préfectures (la source open data est en ASCII)
PREF_LABELS = {
    "Lome Commune": "Lomé", "Agoe-Nyive": "Agoè-Nyivé", "Ave": "Avé", "Kpele": "Kpélé", "Anie": "Anié",
    "Keran": "Kéran", "Cinkasse": "Cinkassé", "Tone": "Tône", "Tandjoare": "Tandjoaré",
    "Plaine du Mo": "Plaine du Mô", "Akebou": "Akébou",
}
# Poids relatifs des préfectures dans leur région (villes principales plus peuplées)
PREF_WEIGHTS = {
    "Lome Commune": 11, "Golfe": 2.5, "Agoe-Nyive": 2.5, "Zio": 1.2, "Vo": 0.7, "Lacs": 0.8, "Yoto": 0.6,
    "Bas-Mono": 0.4, "Ave": 0.6, "Kozah": 4.0, "Tchaoudjo": 4.0, "Ogou": 2.6, "Kloto": 2.2, "Tone": 3.0,
    "Oti": 1.8, "Haho": 1.5,
}
URBAN_PREFS = {"Lome Commune", "Golfe", "Agoe-Nyive", "Kozah", "Tchaoudjo", "Ogou", "Tone", "Kloto"}


# --------------------------------------------------------------------------------------
# Outils numériques
# --------------------------------------------------------------------------------------
def fmt_int(n: float) -> str:
    """19788 -> '19 788' (espace insécable, format français)."""
    return f"{int(round(n)):,}".replace(",", "\u00a0")


def fmt_dec(x: float, nd: int = 1) -> str:
    """72.3 -> '72,3'."""
    return f"{x:,.{nd}f}".replace(",", "\u00a0").replace(".", ",")


def fmt_pct(x: float, nd: int = 1) -> str:
    return f"{fmt_dec(x, nd)}%"


def centered(values: dict, weights: dict, target: float) -> dict:
    """Décale `values` d'une constante pour que leur moyenne pondérée vaille exactement `target`."""
    w = np.array([weights[r] for r in values], float)
    v = np.array(list(values.values()), float)
    shift = target - (w * v).sum() / w.sum()
    return {r: float(x + shift) for r, x in zip(values, v)}


def centered_matrix(weights: dict, base: dict, d_togocom: dict, d_moov: dict) -> pd.DataFrame:
    """
    Matrice de parts région x opérateur (chaque ligne somme à 1) dont la moyenne pondérée par
    `weights` redonne exactement les parts nationales `base`.
    """
    rows = {}
    for r in REGIONS:
        dt, dm = d_togocom[r], d_moov[r]
        rows[r] = {"Togocom": dt, "Moov": dm, "Yas": -0.8 * (dt + dm), "Autres": -0.2 * (dt + dm)}
    raw = pd.DataFrame(rows).T[OPERATEURS]
    w = pd.Series(weights)[REGIONS]
    raw = raw - (raw.mul(w, axis=0).sum() / w.sum())          # centrage de chaque colonne
    return raw + pd.Series(base)[OPERATEURS]


# --------------------------------------------------------------------------------------
# Territoire (région > préfecture > canton/commune)
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def territoire() -> pd.DataFrame:
    """Table des 373 cantons avec leur part dans la préfecture et dans la région."""
    t = pd.read_csv(DATA_DIR / "togo_territoire.csv")
    rng = np.random.default_rng(2026)
    pref = t[["region", "prefecture"]].drop_duplicates().copy()
    pref["wp"] = [PREF_WEIGHTS.get(p, float(rng.uniform(0.6, 1.3))) for p in pref["prefecture"]]
    pref["wp"] = pref["wp"] / pref.groupby("region")["wp"].transform("sum")
    t = t.merge(pref, on=["region", "prefecture"])
    t["wc"] = rng.uniform(0.6, 1.4, len(t))
    t["wc"] = t["wc"] / t.groupby("prefecture")["wc"].transform("sum")
    t["share"] = t["wp"] * t["wc"]                               # somme = 1 par région
    t["prefecture_label"] = t["prefecture"].map(lambda p: PREF_LABELS.get(p, p))
    return t


def prefectures_of(region: str | None) -> list[str]:
    t = territoire()
    if region:
        t = t[t["region"] == region]
    return sorted(t["prefecture_label"].unique(), key=str.casefold)


def communes_of(region: str | None, prefecture: str | None) -> list[str]:
    t = territoire()
    if region:
        t = t[t["region"] == region]
    if prefecture:
        t = t[t["prefecture_label"] == prefecture]
    return sorted(t["canton"].unique(), key=str.casefold)


def territory_share(f: dict) -> dict:
    """Part de chaque région couverte par la sélection territoriale (0 si hors sélection)."""
    t = territoire()
    sel = t
    if f.get("region"):
        sel = sel[sel["region"] == f["region"]]
    if f.get("prefecture"):
        sel = sel[sel["prefecture_label"] == f["prefecture"]]
    if f.get("commune"):
        sel = sel[sel["canton"] == f["commune"]]
    s = sel.groupby("region")["share"].sum()
    return {r: float(s.get(r, 0.0)) for r in REGIONS}


def period_factor(f: dict) -> float:
    """Proportion de la période de référence (31 jours) couverte par la période choisie."""
    start, end = f.get("period") or DEFAULT_PERIOD
    return max((end - start).days + 1, 1) / 31.0


# --------------------------------------------------------------------------------------
# Données de base par région (les sommes redonnent les valeurs des maquettes)
# --------------------------------------------------------------------------------------
POP_SHARE = {"Maritime": 0.41, "Plateaux": 0.205, "Centrale": 0.10, "Kara": 0.12, "Savanes": 0.165}
POPULATION_TOTAL = 8_866_372
_pop = {r: int(POPULATION_TOTAL * s) for r, s in POP_SHARE.items()}
_pop["Maritime"] += POPULATION_TOTAL - sum(_pop.values())

# --- Accueil -----------------------------------------------------------------------
ACC = {
    "agents_mm": {"Maritime": 7462, "Plateaux": 3857, "Kara": 3270, "Savanes": 2851, "Centrale": 2348},   # 19 788
    "agents_fin": {"Maritime": 0.89, "Plateaux": 0.46, "Kara": 0.33, "Savanes": 0.30, "Centrale": 0.25},  # 2,23
    "datacenters": {"Maritime": 2, "Plateaux": 0, "Centrale": 0, "Kara": 1, "Savanes": 0},                # 3
    "population": _pop,                                                                                   # 8 866 372
    "zones_blanches": {"Maritime": 6, "Plateaux": 14, "Centrale": 15, "Kara": 17, "Savanes": 26},         # 78
}
# Agences télécoms : matrice entière région x opérateur (total 90 ; 56 / 25 / 5 / 4 -> 62 / 28 / 6 / 4 %)
AGENCES = pd.DataFrame(
    {"Togocom": [22, 11, 7, 8, 8], "Moov": [11, 5, 3, 4, 2], "Yas": [3, 1, 1, 0, 0], "Autres": [2, 1, 0, 1, 0]},
    index=["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"])
# Part de chaque région dans la couverture réseau (carte de l'accueil)
COUVERTURE_PART = {"Maritime": 28.7, "Plateaux": 20.4, "Centrale": 15.6, "Kara": 12.3, "Savanes": 7.9}
# Performances par région : CA (milliards FCFA), ventes, marge %, évolution %
PERF = pd.DataFrame(
    {"CA": [42.8, 31.5, 28.7, 24.3, 18.6], "Ventes": [748, 623, 561, 498, 412],
     "Marge": [24.5, 22.1, 20.4, 19.8, 18.7], "Evolution": [12.3, 9.8, 7.6, 5.2, 4.9]},
    index=["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"])
# Évolution des ventes par mode de paiement (valeur au 01/08 et au 31/08)
VENTES_MODES = {"Espèces": (63, 173), "Carte bancaire": (40, 131), "Mobile money": (28, 96), "Virement": (10, 62)}

# --- Infrastructures ---------------------------------------------------------------
INF = {
    "stations": {"Maritime": 1020, "Plateaux": 610, "Centrale": 330, "Kara": 470, "Savanes": 404},        # 2 834
    "sites": {"Maritime": 560, "Plateaux": 250, "Centrale": 120, "Kara": 190, "Savanes": 128},            # 1 248
    "fibre": {"Maritime": 1720, "Plateaux": 1060, "Centrale": 640, "Kara": 810, "Savanes": 505},          # 4 735 km
    "points": {"Maritime": 215, "Plateaux": 120, "Centrale": 62, "Kara": 90, "Savanes": 75},              # 562
}
COV4G_REGION = {"Maritime": 88.0, "Plateaux": 72.0, "Centrale": 60.0, "Kara": 58.0, "Savanes": 51.5}   # moy. pond. = 72,3
COV_BY_TECH = {"2G": 94.6, "3G": 85.2, "4G": 72.3, "5G": 8.4}
TECH_SHARE = {"2G": 0.16, "3G": 0.27, "4G": 0.52, "5G": 0.05}      # répartition des stations par technologie
OP_SHARE = {"Togocom": 0.452, "Moov": 0.326, "Yas": 0.168, "Autres": 0.054}   # 45,2 / 32,6 / 16,8 / 5,4 %
QUALITE = {"dispo": 99.2, "debit": 18.7, "latence": 28.0, "satisf": 92.0}
QUALITE_REGION = {   # écarts régionaux (recentrés pour que la moyenne nationale reste exacte)
    "dispo": {"Maritime": 0.5, "Plateaux": 0.1, "Centrale": -0.2, "Kara": -0.3, "Savanes": -0.6},
    "debit": {"Maritime": 4.0, "Plateaux": 0.5, "Centrale": -1.5, "Kara": -2.0, "Savanes": -3.5},
    "latence": {"Maritime": -6.0, "Plateaux": -1.0, "Centrale": 3.0, "Kara": 4.0, "Savanes": 7.0},
    "satisf": {"Maritime": 2.0, "Plateaux": 0.5, "Centrale": -1.0, "Kara": -1.0, "Savanes": -2.5},
}
# Couverture 4G par opérateur, janvier -> août 2025
COV4G_OPS = {
    "Togocom": [33, 45, 50, 58, 68, 74, 80, 89], "Moov": [20, 26, 34, 40, 48, 55, 62, 70],
    "Yas": [10, 17, 22, 27, 32, 39, 44, 50], "Autres": [1, 5, 8, 12, 18, 22, 28, 34],
}
# Évolution mensuelle des infrastructures mobiles (stations / sites), janvier -> août 2025
INFRA_MOIS = {"Stations": [2410, 2478, 2541, 2609, 2672, 2734, 2790, 2834],
              "Sites Internet": [1020, 1058, 1094, 1131, 1165, 1198, 1226, 1248]}

# --- Services numériques -----------------------------------------------------------
USERS_REGION = {"Maritime": 1_672_760, "Plateaux": 640_000, "Centrale": 470_000, "Kara": 700_000,
                "Savanes": 360_000}                                                                    # 3 842 760
USERS_TOTAL = sum(USERS_REGION.values())
SERV_TOTALS = {"transactions": 1_245_320, "paiements": 2_036_571, "eadmin": 684_210, "esante": 348_792}
TYPE_BASE = {"Paiements mobiles": SERV_TOTALS["paiements"] / USERS_TOTAL,
             "E-administration": SERV_TOTALS["eadmin"] / USERS_TOTAL,
             "E-santé": SERV_TOTALS["esante"] / USERS_TOTAL}
TYPE_BASE["Autres"] = 1 - sum(TYPE_BASE.values())
RATES = {"penetration": 45.2, "paiement": 68.3, "satisfaction": 92.4}
RATES_DELTA = {"penetration": 4.5, "paiement": 8.9, "satisfaction": 4.2}
RATES_REGION = {
    "penetration": {"Maritime": 9.0, "Plateaux": 1.0, "Centrale": -4.0, "Kara": -3.0, "Savanes": -7.0},
    "paiement": {"Maritime": 6.0, "Plateaux": 1.5, "Centrale": -3.0, "Kara": -2.0, "Savanes": -5.5},
    "satisfaction": {"Maritime": 1.2, "Plateaux": 0.4, "Centrale": -0.8, "Kara": -0.6, "Savanes": -1.4},
}
TECH_USERS = {"2G": 0.12, "3G": 0.28, "4G": 0.55, "5G": 0.05}   # part des utilisateurs par technologie d'accès
SERV_EVOL = {"Paiements mobiles": (300_000, 830_000), "E-administration": (170_000, 650_000),
             "E-santé": (90_000, 460_000), "Autres": (20_000, 290_000)}   # valeurs au 01/08 et au 31/08


# Localités principales (ville, préfecture source, région, utilisateurs, stations)
LOCALITES = pd.DataFrame([
    ("Lomé", "Lome Commune", "Maritime", 1_023_540, 248), ("Kara", "Kozah", "Kara", 412_680, 176),
    ("Sokodé", "Tchaoudjo", "Centrale", 298_760, 142), ("Atakpamé", "Ogou", "Plateaux", 243_510, 118),
    ("Dapaong", "Tone", "Savanes", 187_430, 92),
    ("Kpalimé", "Kloto", "Plateaux", 176_240, 88), ("Tsévié", "Zio", "Maritime", 168_900, 81),
    ("Aného", "Lacs", "Maritime", 121_350, 64), ("Bassar", "Bassar", "Kara", 92_480, 49),
    ("Mango", "Oti", "Savanes", 88_130, 47), ("Notsé", "Haho", "Plateaux", 84_900, 45),
    ("Vogan", "Vo", "Maritime", 77_650, 38), ("Niamtougou", "Doufelgou", "Kara", 71_560, 41),
    ("Bafilo", "Assoli", "Kara", 66_310, 36), ("Tchamba", "Tchamba", "Centrale", 61_240, 33),
    ("Blitta", "Blitta", "Centrale", 58_470, 31), ("Tabligbo", "Yoto", "Maritime", 54_320, 29),
    ("Badou", "Wawa", "Plateaux", 52_760, 28), ("Cinkassé", "Cinkasse", "Savanes", 49_180, 26),
    ("Amlamé", "Amou", "Plateaux", 47_900, 25),
], columns=["localite", "prefecture", "region", "utilisateurs", "stations"])


CITIES = {"Lomé": (6.1725, 1.2314), "Kara": (9.5511, 1.1861), "Sokodé": (8.9833, 1.1333),
          "Atakpamé": (7.5333, 1.1333), "Dapaong": (10.8633, 0.2076)}


# --------------------------------------------------------------------------------------
# Matrices de parts opérateur / type de service (moyennes nationales exactes)
# --------------------------------------------------------------------------------------
_W_POP, _W_USERS = POP_SHARE, {r: USERS_REGION[r] for r in REGIONS}
_W_STAT = INF["stations"]
OPS_USERS = centered_matrix(_W_USERS, OP_SHARE,
                            {"Maritime": .05, "Plateaux": .0, "Centrale": -.03, "Kara": -.02, "Savanes": -.05},
                            {"Maritime": -.02, "Plateaux": .02, "Centrale": .03, "Kara": .01, "Savanes": .05})
OPS_STATIONS = centered_matrix(_W_STAT, OP_SHARE,
                               {"Maritime": .04, "Plateaux": .01, "Centrale": -.02, "Kara": -.02, "Savanes": -.04},
                               {"Maritime": -.01, "Plateaux": .02, "Centrale": .02, "Kara": .01, "Savanes": .03})
OPS_AGENTS = centered_matrix(ACC["agents_mm"], {"Togocom": .55, "Moov": .38, "Yas": .04, "Autres": .03},
                             {"Maritime": .04, "Plateaux": .0, "Centrale": -.03, "Kara": -.02, "Savanes": -.05},
                             {"Maritime": -.03, "Plateaux": .01, "Centrale": .03, "Kara": .02, "Savanes": .04})
_ag = AGENCES.div(AGENCES.sum(axis=1), axis=0)                    # parts réelles de la matrice entière


def _type_matrix() -> pd.DataFrame:
    """Parts région x type de service, moyenne pondérée (par utilisateurs) = TYPE_BASE."""
    raw = pd.DataFrame({
        "Paiements mobiles": {"Maritime": -.03, "Plateaux": .02, "Centrale": .03, "Kara": .02, "Savanes": .04},
        "E-administration": {"Maritime": .03, "Plateaux": -.01, "Centrale": -.02, "Kara": -.01, "Savanes": -.03},
        "E-santé": {"Maritime": .01, "Plateaux": .0, "Centrale": -.01, "Kara": .0, "Savanes": -.02},
    })
    raw["Autres"] = -raw.sum(axis=1)
    raw = raw.loc[REGIONS, SERVICE_TYPES]
    w = pd.Series(_W_USERS)[REGIONS]
    raw = raw - raw.mul(w, axis=0).sum() / w.sum()
    return raw + pd.Series(TYPE_BASE)[SERVICE_TYPES]


TYPES_USERS = _type_matrix()


# --------------------------------------------------------------------------------------
# Agrégation générique
# --------------------------------------------------------------------------------------
def _ops_frac(f: dict, matrix: pd.DataFrame) -> dict:
    """Part de l'activité de chaque région attribuée aux opérateurs sélectionnés."""
    ops = f.get("operateurs") or OPERATEURS
    return {r: float(matrix.loc[r, ops].sum()) for r in REGIONS}


def _tech_users(f: dict) -> float:
    t = f.get("technologie")
    return TECH_USERS[t] if t else 1.0


def _types_frac(f: dict) -> dict:
    types = f.get("types") or SERVICE_TYPES
    return {r: float(TYPES_USERS.loc[r, types].sum()) for r in REGIONS}


def regional(f: dict, base: dict, ops_matrix: pd.DataFrame | None = None, flow: bool = False,
             extra: dict | None = None) -> dict:
    """Valeur par région après application des filtres territoire / opérateur / période."""
    share = territory_share(f)
    of = _ops_frac(f, ops_matrix) if ops_matrix is not None else {r: 1.0 for r in REGIONS}
    pf = period_factor(f) if flow else 1.0
    ex = extra or {r: 1.0 for r in REGIONS}
    return {r: base[r] * share[r] * of[r] * pf * ex[r] for r in REGIONS}


def _active(f: dict) -> list[str]:
    return [r for r, s in territory_share(f).items() if s > 0]


def _sum(d: dict) -> float:
    return float(sum(d.values()))


# --------------------------------------------------------------------------------------
# Séries temporelles
# --------------------------------------------------------------------------------------
def sample_dates(f: dict, n: int = 7) -> list[date]:
    """Jusqu'à `n` dates régulièrement espacées dans la période (comme 01/08, 05/08, … 31/08)."""
    start, end = f.get("period") or DEFAULT_PERIOD
    days = (end - start).days
    if days <= 0:
        return [start]
    if (start, end) == DEFAULT_PERIOD:
        return [date(2025, 8, d) for d in (1, 5, 10, 15, 20, 25, 31)]
    k = min(n, days + 1)
    return sorted({start + timedelta(days=int(round(i * days / (k - 1)))) for i in range(k)})


def _curve(v0: float, v1: float, d: date, seed: int) -> float:
    """Valeur du jour `d` : croissance linéaire 01/08 -> 31/08, légère irrégularité déterministe."""
    t = (d - AUG_START).days
    v = v0 + (v1 - v0) * t / 30.0
    v = max(v, 0.3 * v0)
    wiggle = 1 + 0.012 * np.sin(1.7 * t + seed) * np.sin(np.pi * min(max(t, 0), 30) / 30.0)
    return v * wiggle


def month_labels(f: dict) -> list[str]:
    _, end = f.get("period") or DEFAULT_PERIOD
    n = max(1, min(end.month, 8)) if end.year == 2025 else 8
    return [f"{m:02d}/2025" for m in range(1, n + 1)]


# ======================================================================================
# ACCUEIL
# ======================================================================================
def accueil_kpis(f: dict) -> dict:
    agents = regional(f, ACC["agents_mm"], OPS_AGENTS)
    agences = 0.0
    share, of = territory_share(f), _ops_frac(f, _ag)
    for r in REGIONS:
        agences += AGENCES.loc[r].sum() * share[r] * of[r]
    return {
        "agents_mm": _sum(agents),
        "agences": agences,
        "agents_fin": _sum(regional(f, ACC["agents_fin"])),
        "datacenters": _sum(regional(f, ACC["datacenters"])),
        "population": _sum(regional(f, ACC["population"])),
        "zones_blanches": _sum(regional(f, ACC["zones_blanches"])),
    }


def accueil_agents_region(f: dict) -> pd.DataFrame:
    v = regional(f, ACC["agents_mm"], OPS_AGENTS)
    order = ["Maritime", "Plateaux", "Kara", "Savanes", "Centrale"]
    return pd.DataFrame({"Région": [r for r in order if v[r] > 0], "Agents": [v[r] for r in order if v[r] > 0]})


def accueil_agences_operateur(f: dict) -> pd.DataFrame:
    share = territory_share(f)
    ops = f.get("operateurs") or OPERATEURS
    vals = {op: sum(AGENCES.loc[r, op] * share[r] for r in REGIONS) for op in OPERATEURS}
    return pd.DataFrame({"Opérateur": ops, "Agences": [vals[o] for o in ops]})


def _mode_factor(f: dict) -> float:
    modes = f.get("types") or PAYMENT_MODES
    tot = sum(VENTES_MODES[m][1] for m in PAYMENT_MODES)
    return sum(VENTES_MODES[m][1] for m in modes) / tot


def accueil_performances(f: dict) -> pd.DataFrame:
    share, pf, mf = territory_share(f), period_factor(f), _mode_factor(f)
    of = _ops_frac(f, OPS_AGENTS)
    rows = []
    for r in ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]:
        k = share[r] * pf * mf * (of[r] if f.get("operateurs") else 1.0)
        if share[r] <= 0:
            continue
        p = PERF.loc[r]
        rows.append({"Région": r, "CA (Md)": p.CA * k, "Ventes": p.Ventes * k, "Marge (%)": p.Marge,
                     "Évolution": p.Evolution})
    return pd.DataFrame(rows)


def accueil_couverture(f: dict) -> pd.DataFrame:
    share = territory_share(f)
    of = _ops_frac(f, OPS_STATIONS) if f.get("operateurs") else {r: 1.0 for r in REGIONS}
    order = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
    return pd.DataFrame({"Région": order,
                         "Part": [COUVERTURE_PART[r] * of[r] if share[r] > 0 else np.nan for r in order]})


def accueil_ventes_evolution(f: dict) -> pd.DataFrame:
    modes = f.get("types") or PAYMENT_MODES
    nat = _sum({r: PERF.loc[r, "Ventes"] for r in REGIONS})
    sel = sum(PERF.loc[r, "Ventes"] * s for r, s in territory_share(f).items())
    k = sel / nat
    rows = []
    for i, m in enumerate(modes):
        v0, v1 = VENTES_MODES[m]
        for d in sample_dates(f):
            rows.append({"Date": d, "Mode": m, "Valeur": _curve(v0, v1, d, i) * k})
    return pd.DataFrame(rows)


# ======================================================================================
# INFRASTRUCTURES
# ======================================================================================
def _tech_factor(f: dict) -> float:
    t = f.get("technologie")
    return TECH_SHARE[t] if t else 1.0                # part des stations utilisant la technologie


def infra_kpis(f: dict) -> dict:
    tf = _tech_factor(f)
    stations = regional(f, INF["stations"], OPS_STATIONS, extra={r: tf for r in REGIONS})
    sites = regional(f, INF["sites"], OPS_STATIONS)
    fibre = regional(f, INF["fibre"])
    points = regional(f, INF["points"])
    tech = f.get("technologie") or "4G"
    # couverture : moyenne pondérée par la population des régions sélectionnées
    share = territory_share(f)
    w = {r: POP_SHARE[r] * share[r] for r in REGIONS}
    cov_reg = centered(COV4G_REGION, POP_SHARE, 72.3)
    cov = sum(cov_reg[r] * w[r] for r in REGIONS) / max(sum(w.values()), 1e-9)
    cov *= COV_BY_TECH[tech] / 72.3
    return {"stations": _sum(stations), "sites": _sum(sites), "fibre": _sum(fibre), "points": _sum(points),
            "couverture": min(cov, 99.9), "tech": tech}


def infra_operateurs(f: dict) -> tuple[pd.DataFrame, float, str]:
    """Donut : répartition par opérateur du type d'infrastructure choisi (stations par défaut)."""
    typ = f.get("infra_type") or INFRA_TYPES[0]
    base, unit = {"Stations de téléphonie mobile": (INF["stations"], "stations"), "Sites Internet": (INF["sites"], "sites"),
                  "Points d'accès publics": (INF["points"], "points"), "Fibre optique (km)": (INF["fibre"], "km")}[typ]
    ex = {r: _tech_factor(f) for r in REGIONS} if typ == INFRA_TYPES[0] else None
    share, ops = territory_share(f), f.get("operateurs") or OPERATEURS
    vals = {op: sum(base[r] * share[r] * OPS_STATIONS.loc[r, op] * (ex[r] if ex else 1) for r in REGIONS)
            for op in OPERATEURS}
    df = pd.DataFrame({"Opérateur": ops, "Valeur": [vals[o] for o in ops]})
    return df, float(df["Valeur"].sum()), unit


def infra_top_localites(f: dict, n: int = 5) -> tuple[pd.DataFrame, str]:
    """Top localités par nombre de stations (ou par type d'infrastructure choisi)."""
    typ = f.get("infra_type") or INFRA_TYPES[0]
    key = {"Stations de téléphonie mobile": "stations", "Sites Internet": "sites",
           "Points d'accès publics": "points", "Fibre optique (km)": "fibre"}[typ]
    ratio = {r: INF[key][r] / INF["stations"][r] for r in REGIONS}
    return _top_loc(f, "stations", ratio, n), {"stations": "stations", "sites": "sites", "points": "points d'accès",
                                               "fibre": "km de fibre"}[key]


def _top_loc(f: dict, col: str, ratio: dict, n: int) -> pd.DataFrame:
    """Classement des localités ; au niveau préfecture/commune, classement des cantons de la sélection."""
    t = territoire()
    if f.get("prefecture") or f.get("commune"):
        sel = t[t["prefecture_label"] == f["prefecture"]] if f.get("prefecture") else t
        if f.get("region"):
            sel = sel[sel["region"] == f["region"]]
        if f.get("commune"):
            sel = sel[sel["canton"] == f["commune"]]
        base = {"stations": INF["stations"], "utilisateurs": USERS_REGION}[col]
        rr = ratio if col == "stations" else {x: 1 for x in REGIONS}
        out = pd.DataFrame({"Localité": sel["canton"], "Valeur": [base[r] * s * rr[r] for r, s in zip(sel["region"], sel["share"])]})
        return out.nlargest(n, "Valeur").reset_index(drop=True)
    loc = LOCALITES if not f.get("region") else LOCALITES[LOCALITES["region"] == f["region"]]
    vals = loc[col].astype(float) * loc["region"].map(ratio if col == "stations" else {r: 1 for r in REGIONS})
    out = pd.DataFrame({"Localité": loc["localite"], "Valeur": vals})
    return out.nlargest(n, "Valeur").reset_index(drop=True)


def infra_qualite(f: dict) -> dict:
    share = territory_share(f)
    w = {r: INF["stations"][r] * share[r] for r in REGIONS}
    tot = max(sum(w.values()), 1e-9)
    out = {}
    for k, base in QUALITE.items():
        reg = centered({r: base + QUALITE_REGION[k][r] for r in REGIONS}, INF["stations"], base)
        out[k] = sum(reg[r] * w[r] for r in REGIONS) / tot
    return out


def infra_cov4g_evolution(f: dict) -> pd.DataFrame:
    labels = month_labels(f)
    share = territory_share(f)
    w = {r: POP_SHARE[r] * share[r] for r in REGIONS}
    cov_reg = centered(COV4G_REGION, POP_SHARE, 72.3)
    k = (sum(cov_reg[r] * w[r] for r in REGIONS) / max(sum(w.values()), 1e-9)) / 72.3
    ops = f.get("operateurs") or OPERATEURS
    rows = [{"Mois": lab, "Opérateur": op, "Couverture": min(COV4G_OPS[op][i] * k, 100)}
            for op in ops for i, lab in enumerate(labels)]
    return pd.DataFrame(rows)


def infra_mobiles_evolution(f: dict) -> pd.DataFrame:
    labels = month_labels(f)
    share = territory_share(f)
    k = sum(INF["stations"][r] * s for r, s in share.items()) / sum(INF["stations"].values())
    rows = [{"Mois": lab, "Série": s, "Valeur": INFRA_MOIS[s][i] * k} for s in INFRA_MOIS for i, lab in enumerate(labels)]
    return pd.DataFrame(rows)


def infra_fibre_region(f: dict) -> pd.DataFrame:
    v = regional(f, INF["fibre"])
    order = ["Maritime", "Plateaux", "Kara", "Centrale", "Savanes"]
    return pd.DataFrame({"Région": [r for r in order if v[r] > 0], "Km": [v[r] for r in order if v[r] > 0]})


def infra_operateurs_table(f: dict) -> pd.DataFrame:
    share = territory_share(f)
    rows = []
    for op in f.get("operateurs") or OPERATEURS:
        st = sum(INF["stations"][r] * share[r] * OPS_STATIONS.loc[r, op] for r in REGIONS)
        si = sum(INF["sites"][r] * share[r] * OPS_STATIONS.loc[r, op] for r in REGIONS)
        fi = sum(INF["fibre"][r] * share[r] * OPS_STATIONS.loc[r, op] for r in REGIONS)
        pt = sum(INF["points"][r] * share[r] * OPS_STATIONS.loc[r, op] for r in REGIONS)
        rows.append({"Opérateur": op, "Stations": st, "Sites Internet": si, "Fibre (km)": fi, "Points d'accès": pt})
    return pd.DataFrame(rows)


@lru_cache(maxsize=1)
def prefecture_coverage() -> dict:
    """Couverture 4G par préfecture (région + écart urbain/rural déterministe), pour la carte."""
    t = territoire()[["region", "prefecture"]].drop_duplicates()
    rng = np.random.default_rng(11)
    reg = centered(COV4G_REGION, POP_SHARE, 72.3)
    out = {}
    for r, p in zip(t["region"], t["prefecture"]):
        out[p] = float(np.clip(reg[r] + (12 if p in URBAN_PREFS else 0) + rng.normal(0, 7), 12, 99))
    return out


def infra_map_values(f: dict) -> pd.DataFrame:
    """Couverture par préfecture, pour la carte (valeurs hors sélection masquées)."""
    cov = prefecture_coverage()
    t = territoire()[["region", "prefecture", "prefecture_label"]].drop_duplicates()
    sel = set(_selected_prefs(f))
    tf = COV_BY_TECH[f.get("technologie") or "4G"] / 72.3
    return pd.DataFrame({"prefecture": t["prefecture"], "label": t["prefecture_label"], "region": t["region"],
                         "value": [min(cov[p] * tf, 99.5) if p in sel else np.nan for p in t["prefecture"]]})


def _selected_prefs(f: dict) -> list[str]:
    t = territoire()
    if f.get("region"):
        t = t[t["region"] == f["region"]]
    if f.get("prefecture"):
        t = t[t["prefecture_label"] == f["prefecture"]]
    if f.get("commune"):
        t = t[t["canton"] == f["commune"]]
    return list(t["prefecture"].unique())


# ======================================================================================
# SERVICES NUMÉRIQUES
# ======================================================================================
SERV_INDICATORS = {
    "Utilisateurs des services numériques": "users", "Transactions en ligne": "transactions",
    "Paiements mobiles": "paiements", "Services e-administration": "eadmin", "Services e-santé": "esante",
}


def _serv_region_values(f: dict) -> dict[str, dict]:
    """Valeurs de chaque indicateur par région, après filtres."""
    tf = _types_frac(f)
    ops = {r: v for r, v in _ops_frac(f, OPS_USERS).items()}
    share, pf = territory_share(f), period_factor(f)
    ratio_tr = SERV_TOTALS["transactions"] / USERS_TOTAL
    tu = _tech_users(f)
    out = {"users": {}, "transactions": {}, "paiements": {}, "eadmin": {}, "esante": {}}
    for r in REGIONS:
        k = USERS_REGION[r] * share[r] * ops[r] * tu
        out["users"][r] = k * tf[r]
        out["transactions"][r] = k * tf[r] * ratio_tr * pf
        out["paiements"][r] = k * TYPES_USERS.loc[r, "Paiements mobiles"]
        out["eadmin"][r] = k * TYPES_USERS.loc[r, "E-administration"]
        out["esante"][r] = k * TYPES_USERS.loc[r, "E-santé"]
    return out


def services_kpis(f: dict) -> dict:
    vals = _serv_region_values(f)
    return {k: _sum(v) for k, v in vals.items()}


def services_operateurs(f: dict) -> tuple[pd.DataFrame, float]:
    share, tf = territory_share(f), _types_frac(f)
    ops = f.get("operateurs") or OPERATEURS
    tu = _tech_users(f)
    vals = {op: sum(USERS_REGION[r] * share[r] * tf[r] * tu * OPS_USERS.loc[r, op] for r in REGIONS) for op in OPERATEURS}
    df = pd.DataFrame({"Opérateur": ops, "Valeur": [vals[o] for o in ops]})
    return df, float(df["Valeur"].sum())


def services_rates(f: dict) -> dict:
    share = territory_share(f)
    w = {r: USERS_REGION[r] * share[r] for r in REGIONS}
    tot = max(sum(w.values()), 1e-9)
    out = {}
    for k, base in RATES.items():
        reg = centered({r: base + RATES_REGION[k][r] for r in REGIONS}, USERS_REGION, base)
        out[k] = sum(reg[r] * w[r] for r in REGIONS) / tot
    return out


def services_top_localites(f: dict, n: int = 5) -> pd.DataFrame:
    """Top localités par nombre d'utilisateurs (filtré par région, opérateur et type de service)."""
    if f.get("prefecture") or f.get("commune"):
        return _top_loc(f, "utilisateurs", {r: 1 for r in REGIONS}, n)
    loc = LOCALITES if not f.get("region") else LOCALITES[LOCALITES["region"] == f["region"]]
    k = loc["region"].map(_ops_frac(f, OPS_USERS)) * loc["region"].map(_types_frac(f)) * _tech_users(f)
    out = pd.DataFrame({"Localité": loc["localite"], "Valeur": loc["utilisateurs"].astype(float) * k})
    return out.nlargest(n, "Valeur").reset_index(drop=True)


def services_evolution(f: dict) -> pd.DataFrame:
    types = f.get("types") or SERVICE_TYPES
    share, ops = territory_share(f), _ops_frac(f, OPS_USERS)
    k = _tech_users(f) * sum(USERS_REGION[r] * share[r] * ops[r] for r in REGIONS) / USERS_TOTAL
    rows = []
    for i, t in enumerate(SERVICE_TYPES):
        if t not in types:
            continue
        v0, v1 = SERV_EVOL[t]
        for d in sample_dates(f):
            rows.append({"Date": d, "Service": t, "Valeur": _curve(v0, v1, d, i + 3) * k})
    return pd.DataFrame(rows)


def services_by_level(f: dict, level: str, indicator: str) -> pd.DataFrame:
    """Valeur de l'indicateur choisi par région / préfecture / commune (canton), pour carte et liste."""
    key = SERV_INDICATORS[indicator]
    vals = _serv_region_values(f)[key]
    t = territoire()
    sel = t
    if f.get("region"):
        sel = sel[sel["region"] == f["region"]]
    if f.get("prefecture"):
        sel = sel[sel["prefecture_label"] == f["prefecture"]]
    if f.get("commune"):
        sel = sel[sel["canton"] == f["commune"]]
    # valeur « pleine région » (sans filtre territorial) pour répartir ensuite selon les parts
    full = _serv_region_values({**f, "region": None, "prefecture": None, "commune": None})[key]
    if level == "Région":
        v = {r: full[r] * float(sel.loc[sel["region"] == r, "share"].sum()) for r in REGIONS}
        return pd.DataFrame({"Territoire": REGIONS, "Région": REGIONS, "Valeur": [v[r] for r in REGIONS]}) \
            .query("Valeur > 0").reset_index(drop=True)
    if level == "Préfecture":
        g = sel.groupby(["region", "prefecture", "prefecture_label"])["share"].sum().reset_index()
        g["Valeur"] = [full[r] * s for r, s in zip(g["region"], g["share"])]
        return g.rename(columns={"prefecture_label": "Territoire", "region": "Région", "prefecture": "code"})[
            ["Territoire", "Région", "Valeur", "code"]]
    s = sel[["region", "prefecture_label", "canton", "lat", "lon", "share"]].copy()
    s["Valeur"] = [full[r] * x for r, x in zip(s["region"], s["share"])]
    return s.rename(columns={"canton": "Territoire", "region": "Région", "prefecture_label": "Préfecture"})


# ======================================================================================
# Géométries
# ======================================================================================
@lru_cache(maxsize=1)
def regions_geojson() -> dict:
    return json.loads((DATA_DIR / "togo_regions.geojson").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def prefectures_geojson() -> dict:
    gj = json.loads((DATA_DIR / "togo_prefectures.geojson").read_text(encoding="utf-8"))
    for ft in gj["features"]:
        ft["properties"]["label"] = PREF_LABELS.get(ft["properties"]["name"], ft["properties"]["name"])
    return gj
