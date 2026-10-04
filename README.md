# Dashboard « Économie Numérique — Togo » (Streamlit)

Dashboard du Ministère de l'Économie Numérique : **Accueil**, **Infrastructures**, **Services numériques**
et **Recommandations** (synthèse décisionnelle en trois priorités). Les menus *Rapports PDF*, *Carte* et
*Métriques* affichent « Module en préparation ». La page *Zones blanches* reste enregistrée dans `app.py`
(URL `/zones-blanches`) mais n'apparaît plus dans la barre de navigation : pour la réafficher, ajouter une
entrée dans `NAV_ITEMS` (`components/navbar.py`) et son icône par index dans `components/styles.py`.

## Lancer l'application

```bash
pip install -r requirements.txt
streamlit run app.py
```

Résolution de référence : **1670 × 942 px** (maquettes). L'interface reste utilisable sur portable,
écran large et tablette (CSS responsive). Les polices (Nunito Sans) et les icônes (Font Awesome) sont
**embarquées dans le CSS** (`assets/embedded_fonts.css`) : elles s'affichent sans Internet, sans dossier
`static/` et sans fichier de configuration. Seules les cartes (pages Infrastructures et Services numériques)
ont besoin d'Internet : Leaflet et le fond OpenStreetMap sont chargés depuis leurs serveurs.

## Structure

```
app.py                      point d'entrée : pages, header, navbar, CSS
views/                      une page par menu (accueil, infrastructures, services_numeriques, recommandations)
components/
    styles.py               palette + CSS global (dimensions relevées sur les maquettes)
    header.py  navbar.py  sidebar.py
    kpi_cards.py            create_kpi_card() — titre + valeur, AUCUN texte dessous
    charts.py               create_bar_chart / create_donut_chart / create_line_chart, Top 5, anneaux
    maps.py                 create_map() (Folium) et create_region_map() (Plotly)
    tables.py               create_table()
    recommendation_cards.py cartes « Priorité » + lignes d'actions (page Recommandations)
    placeholder.py  ui.py
data/
    data.py                 données synthétiques + fonctions de calcul filtrées
    togo_*.geojson/csv      contours des régions/préfectures, 373 cantons
tools/build_embedded_fonts.py   régénère assets/embedded_fonts.css (voir ci-dessous)
assets/logo_togo.png        drapeau
assets/embedded_fonts.css   polices + icônes en base64 (généré)
.streamlit/config.toml      thème
```

> Le dossier s'appelle `views/` et non `pages/` : avec `pages/`, Streamlit exécute le fichier seul lors
> d'un rechargement direct de l'URL (sans en-tête ni CSS).

## Filtres

La sidebar est propre à chaque page. Les choix ne sont appliqués qu'au clic sur **Appliquer les filtres**
(état dans `st.session_state`) ; **Réinitialiser** remet tout à zéro. La période (en-tête ou sidebar)
s'applique immédiatement. Région → préfecture → commune sont en cascade. Les KPI, graphiques, cartes et
tableaux sont recalculés à partir des filtres.

## Données

Entièrement synthétiques (`data/data.py`) mais cohérentes : sans filtre, les totaux sont ceux des
maquettes (19 788 agents, 90 agences, 2 834 stations, 72,3 %, 3 842 760 utilisateurs…), et la somme des
régions redonne le total national. Les contours viennent de données administratives ouvertes (préfectures
reconstituées à partir de leurs chefs-lieux, découpées au contour du pays) : ils sont indicatifs.

## Ajouter une icône

Les icônes sont des `<i class="fa-solid fa-xxx">` dont seules les glyphes utilisés sont embarqués. Après avoir
utilisé une nouvelle icône Font Awesome, régénérer le CSS :

```bash
pip install fonttools brotli
npm pack @fortawesome/fontawesome-free @fontsource/nunito-sans     # puis décompresser les 2 archives
python tools/build_embedded_fonts.py <fontawesome-free/package> <nunito-sans/package/files>
```

## Personnaliser

- Couleurs et dimensions : `components/styles.py`.
- Fond de carte : `TILE_URL` dans `components/maps.py`.
- Données réelles : remplacer les dictionnaires de `data/data.py` en conservant les signatures.
