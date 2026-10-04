"""Page « Recommandations » — pistes d'actions pour un numérique plus inclusif et performant au Togo."""
from __future__ import annotations

import streamlit as st

from components.recommendation_cards import create_priority_card
from components.sidebar import create_sidebar
from components.styles import THEME
from components.ui import page_title

create_sidebar("recommandations")      # même sidebar que les autres pages (page de synthèse : contenu non filtré)
page_title("fa-lightbulb", "Recommandations", "Pistes d'actions pour un numérique plus inclusif et performant au Togo.")

# Contenu éditorial (textes et chiffres exacts de la consigne) : (icône, titre, couleur du titre, actions)
PRIORITES = [
    {
        "icon": '<i class="fa-solid fa-tower-cell"></i>',
        "title": "Priorité 1 — Connecter les zones blanches", "color": THEME["green"],
        "actions": [
            ("A1", "Hubs communautaires solaires",
             "déployer 50 hubs 4G dans les cantons blancs les plus peuplés (Tchamba, Kpendjal, Haho), en priorité dans les chefs-lieux de canton."),
            ("A2", "Obligations de couverture",
             "conditionner les licences et renouvellements à des cibles par préfecture, publiées annuellement au niveau cantonal."),
            ("A3", "Backhaul des services publics",
             "raccorder par satellite ou 4G les centres de santé et collèges situés en zone blanche."),
        ],
    },
    {
        "icon": '<span class="box"><i class="fa-solid fa-mobile-screen-button"></i></span>',
        "title": "Priorité 2 — Approfondir l'inclusion financière mobile", "color": THEME["blue_link"],
        "actions": [
            ("B1", "Agents multifonctions",
             "transformer les 19 788 points mobile money en guichets de services publics numériques (paiement, identité, protection sociale)."),
            ("B2", "Cantons sans point",
             "subventionner l'installation d'agents dans les 23 cantons qui n'en comptent aucun, avec interopérabilité renforcée."),
            ("B3", "Concurrence et tarifs",
             "encourager l'offre Moov/Togocom pour faire progresser les abonnements mobiles (80,8 pour 100, contre 184 en Côte d'Ivoire)."),
        ],
    },
    {
        "icon": '<i class="fa-solid fa-building-columns"></i>',
        "title": "Priorité 3 — Réduire la fracture territoriale", "color": THEME["blue_link"],
        "actions": [
            ("C1", "40 agences cantonales",
             "ouvrir une agence ou franchise dans les cantons denses sans présence opérateur d'ici 2030 pour faire passer la couverture à 5 points de plus de 50% à 70%."),
            ("C2", "Interopérabilité des services",
             "garantir la connexion entre les services mobiles et les services e-administration dans toutes les régions."),
            ("C3", "Suivi et évaluation",
             "mettre en place un tableau de bord de suivi des zones blanches avec des indicateurs trimestriels et un rapport public."),
        ],
    },
]

for p in PRIORITES:
    st.markdown(create_priority_card(p["icon"], p["title"], p["color"], "PRIORITÉ 1", p["actions"]), unsafe_allow_html=True)
