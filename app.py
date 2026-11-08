import difflib
import html
import math
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

# set_page_config doit être la 1re commande Streamlit
st.set_page_config(layout="wide", page_title="ESTFLIX")

st.markdown("""
<style>
:root {
    --card-w: 180px;          /* largeur affiche + bouton + tooltip */
    --card-h: 270px;          /* hauteur affiche + bouton */
    --tip-w: var(--card-w);   /* tooltip = même largeur que l'affiche */
    --img-h: var(--card-h);   /* hauteur de l'image au survol */
    --pop-up: 40px;           /* l'image monte de 40px au survol */
}

/* Rien ne doit couper l'image ni le tooltip */
[data-testid="stHorizontalBlock"],
[data-testid="stColumn"],
[data-testid="stColumn"] [data-testid="stVerticalBlock"],
[data-testid="stColumn"] [data-testid="stElementContainer"],
[data-testid="stColumn"] [data-testid="stMarkdownContainer"] {
    overflow: visible !important;
}

/* La rangée et la colonne survolées passent au-dessus des autres */
[data-testid="stHorizontalBlock"]:has(.tooltip) {
    position: relative !important;
    z-index: 1;
}
[data-testid="stHorizontalBlock"]:has(.tooltip):hover {
    z-index: 100 !important;
}
[data-testid="stColumn"]:has(.tooltip):hover {
    position: relative !important;
    z-index: 60 !important;
}

.tooltip { position: relative; cursor: pointer; }

/* La carte = le bloc vertical d'une colonne qui contient une affiche */
[data-testid="stColumn"] [data-testid="stVerticalBlock"]:has(.tooltip) {
    position: relative !important;
    width: var(--card-w) !important;
    gap: 0 !important;
}

/* Conteneur de l'affiche */
[data-testid="stColumn"] [data-testid="stElementContainer"]:has(.tooltip) {
    width: var(--card-w) !important;
    height: var(--card-h) !important;
}
[data-testid="stColumn"] [data-testid="stElementContainer"]:has(.tooltip) p {
    margin: 0 !important;
}
[data-testid="stColumn"] .tooltip,
[data-testid="stColumn"] div[style*="inline-block"] {
    display: block !important;
    width: var(--card-w) !important;
    height: var(--card-h) !important;
    margin: 0 !important;
}

/* Affiche : au repos = la carte */
[data-testid="stColumn"] .tooltip img {
    position: absolute !important;
    top: 0;
    left: 0;
    width: var(--card-w) !important;
    height: var(--card-h) !important;
    object-fit: cover !important;
    border-radius: 10px !important;
    z-index: 1;
    transition: all .2s ease;
}

/* Affiche : au survol, elle monte et passe par-dessus */
[data-testid="stColumn"] [data-testid="stVerticalBlock"]:has(.tooltip):hover .tooltip img {
    top: calc(-1 * var(--pop-up));
    left: calc((var(--card-w) - var(--tip-w)) / 2);
    width: var(--tip-w) !important;
    height: var(--img-h) !important;
    border-radius: 16px 16px 0 0 !important;
    box-shadow: 0 -8px 30px rgba(0,0,0,0.6);
    z-index: 998;
    pointer-events: none;
}

/* Conteneur du bouton : remonté exactement sur l'affiche */
[data-testid="stColumn"] [data-testid="stElementContainer"]:has(.stButton) {
    width: var(--card-w) !important;
    height: var(--card-h) !important;
    margin-top: calc(-1 * var(--card-h)) !important;
    position: relative !important;
    z-index: 5;
}
[data-testid="stColumn"] .stButton,
[data-testid="stColumn"] .stButton > div {
    width: var(--card-w) !important;
    height: var(--card-h) !important;
}

/* Bouton transparent : même taille que l'affiche */
[data-testid="stColumn"] .stButton button {
    width: var(--card-w) !important;
    height: var(--card-h) !important;
    min-width: 0 !important;
    background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 35%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    display: flex !important;
    align-items: flex-end !important;
    justify-content: center !important;
    padding: 0 6px 8px 6px !important;
    font-size: 13px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stColumn"] .stButton button:hover {
    box-shadow: inset 0 0 0 2px #ff4b4b !important;
    color: #ff4b4b !important;
}

/* ================= TOOLTIP : texte sous l'image ================= */
.tooltip .tooltiptext {
    visibility: hidden;
    opacity: 0;
    position: absolute !important;
    top: calc(var(--img-h) - var(--pop-up)) !important;
    left: calc((var(--card-w) - var(--tip-w)) / 2) !important;
    bottom: auto !important;
    margin: 0 !important;
    width: var(--tip-w) !important;
    max-height: 220px;
    overflow: hidden;
    box-sizing: border-box;
    background: #1b1e27 !important;
    color: #fff !important;
    text-align: left !important;
    font-size: 12px;
    line-height: 1.5;
    word-break: break-word;
    border-radius: 0 0 16px 16px !important;
    padding: 10px 12px 12px !important;
    box-shadow: 0 14px 40px rgba(0,0,0,0.6);
    transition: opacity .2s !important;
    pointer-events: none;
    z-index: 999 !important;
}
.tooltip .tooltiptext b {
    color: #8e93a3;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .5px;
}

/* Visible seulement pour la carte survolée */
[data-testid="stColumn"] [data-testid="stVerticalBlock"]:has(.tooltip):hover .tooltiptext {
    visibility: visible !important;
    opacity: 1 !important;
}

/* La carte survolée passe au-dessus de ses voisines */
[data-testid="stColumn"] [data-testid="stVerticalBlock"]:has(.tooltip):hover {
    z-index: 50 !important;
}
</style>
""", unsafe_allow_html=True)


# =====================================================================
#  CONFIG & OUTILS
# =====================================================================
ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ART = ROOT / "movie_informations"

# Clé TMDB : de préférence dans la variable d'environnement TMDB_API_KEY
API_KEY = os.environ.get("TMDB_API_KEY", "8265bd1679663a7ea12ac168da84d2e8")

NO_POSTER = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750'%3E"
             "%3Crect width='100%25' height='100%25' fill='%23222'/%3E%3C/svg%3E")
PER_PAGE = 10


def is_missing(v):
    return v is None or (isinstance(v, float) and pd.isna(v))


def as_list(v):
    """Liste de textes, que la valeur soit une liste ou une chaîne 'A, B, C'."""
    if isinstance(v, (list, tuple, set)):
        return [str(i) for i in v]
    if is_missing(v):
        return []
    return [s.strip() for s in str(v).split(",") if s.strip()]


def fmt_list(v):
    if isinstance(v, (list, tuple, set)):
        return ", ".join(str(i) for i in v)
    return "" if is_missing(v) else str(v)


def fmt_date(v):
    d = pd.to_datetime(v, errors="coerce")
    return "N/A" if pd.isna(d) else d.strftime("%Y-%m-%d")


def esc(v):
    """Échappe le HTML et le '$' (sinon Streamlit le prend pour du LaTeX)."""
    return html.escape(str(v)).replace("$", "&#36;")


def shorten_title(title, max_length=11):
    title = str(title)
    return title[:max_length] + "..." if len(title) > max_length else title


# =====================================================================
#  API TMDB (un seul appel par film, mis en cache)
# =====================================================================
@st.cache_data(show_spinner=False, ttl=24 * 3600)
def fetch_details(movie_id):
    out = {"poster": NO_POSTER, "rating": None, "videos": []}
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/movie/{int(movie_id)}",
            params={"api_key": API_KEY, "language": "en-US", "append_to_response": "videos"},
            timeout=10,
        )
        d = r.json()
    except Exception:
        return out
    if d.get("poster_path"):
        out["poster"] = "https://image.tmdb.org/t/p/w500" + d["poster_path"]
    if d.get("vote_average"):
        out["rating"] = round(d["vote_average"], 1)
    results = (d.get("videos") or {}).get("results", [])
    out["videos"] = [v for v in results if v.get("site") == "YouTube"]
    return out


def fetch_poster(movie_id):
    return fetch_details(movie_id)["poster"]


def fetch_rating(movie_id):
    return fetch_details(movie_id)["rating"]


def fetch_videos(movie_id):
    return fetch_details(movie_id)["videos"]


# =====================================================================
#  DONNÉES
# =====================================================================
st.markdown("<h1 style='text-align: center;'>ESTFLIX</h1>", unsafe_allow_html=True)

logo = ART / "ESTFLIX.png"
_, logo_col, _ = st.columns(3)
if logo.exists():
    with logo_col:
        st.image(str(logo))
    st.sidebar.image(str(logo))

needed = ["movie_information.pkl", "similarity.pkl", "movie_information (1).pkl"]
missing = [n for n in needed if not (ART / n).exists()]
if missing:
    st.error("Fichier(s) manquant(s) dans le dossier movie_informations : " + ", ".join(missing))
    if "similarity.pkl" in missing:
        st.info("Génère-le avec :  python build_similarity.py")
    st.stop()


@st.cache_resource(show_spinner="Chargement des données...")
def load_data():
    with open(ART / "movie_information.pkl", "rb") as f:
        movies = pickle.load(f)
    with open(ART / "similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
    with open(ART / "movie_information (1).pkl", "rb") as f:
        movies2 = pickle.load(f)
    return movies, similarity, movies2


movies, similarity, movies2 = load_data()

if similarity.shape[0] != len(movies):
    st.error(f"similarity.pkl ({similarity.shape[0]} lignes) ne correspond pas à "
             f"movie_information.pkl ({len(movies)} films). Relance :  python build_similarity.py")
    st.stop()


def similar_movie_ids(movie_id, n=10):
    """Les n films les plus proches (le film lui-même et les doublons exclus)."""
    ids_col = movies["movie_id"].to_numpy()
    pos = np.flatnonzero(ids_col == movie_id)
    if len(pos) == 0:
        return []
    order = np.argsort(-np.asarray(similarity[pos[0]]), kind="stable")
    seen, result = {int(movie_id)}, []
    for j in order:
        mid = int(ids_col[j])
        if mid in seen:
            continue
        seen.add(mid)
        result.append(mid)
        if len(result) == n:
            break
    return result


# =====================================================================
#  ÉTAT (callbacks)
# =====================================================================
def open_movie(movie_id):
    st.session_state.clicked_movie_id = int(movie_id)


def reset_movie():
    """Un filtre a changé : on quitte la page film et la recherche."""
    st.session_state.pop("clicked_movie_id", None)
    st.session_state.search_active = False


def start_search():
    """Clic sur Search : on ferme la page film et on vide les filtres."""
    st.session_state.pop("clicked_movie_id", None)
    st.session_state.search_active = True
    st.session_state.search_query = st.session_state.get("search_input", "").strip()
    for k in ("sel_genres", "sel_actors", "sel_directors"):
        st.session_state[k] = []


def go_home():
    st.session_state.pop("clicked_movie_id", None)
    st.session_state.search_active = False
    st.session_state.search_input = ""
    for k in ("sel_genres", "sel_actors", "sel_directors"):
        st.session_state[k] = []


# =====================================================================
#  AFFICHAGE
# =====================================================================
def poster_card(m, ctx):
    """Une affiche + tooltip + bouton (cliquable partout sur l'affiche)."""
    d = fetch_details(m["movie_id"])
    rating = f'{d["rating"]} ⭐' if d["rating"] else "N/A"
    # tout sur UNE ligne : Streamlit traite sinon les lignes indentées comme du code
    tip = (
        '<span class="tooltiptext">'
        f'<b>TITRE ORIGINAL:</b> {esc(m["title"])}<br/>'
        f'<b>DATE DE SORTIE:</b> {fmt_date(m["release_date"])}<br/>'
        f'<b>GENRE:</b> {esc(fmt_list(m["genres"]))}<br/>'
        f'<b>LANGUE ORIGINALE:</b> {esc(m["original_language"])}<br/>'
        f'<b>RATING:</b> {rating}<br/>'
        f'<b>RÉALISATEUR:</b> {esc(fmt_list(m["crew"]))}<br/>'
        f'<b>ACTEURS:</b> {esc(fmt_list(m["cast"]))}<br/>'
        '</span>'
    )
    st.markdown(f'<div class="tooltip"><img src="{d["poster"]}" alt="">{tip}</div>',
                unsafe_allow_html=True)
    st.button(shorten_title(m["title"]), key=f"btn_{ctx}_{int(m['movie_id'])}",
              on_click=open_movie, args=(m["movie_id"],))


def show_cards(df, ctx):
    """Affiche un DataFrame de films en rangées de 5 (rangée incomplète comprise)."""
    df = df.drop_duplicates("movie_id")
    for start in range(0, len(df), 5):
        cols = st.columns(5)
        for col, (_, m) in zip(cols, df.iloc[start:start + 5].iterrows()):
            with col:
                poster_card(m, ctx)


def span(text):
    return ("<span style='font-family:Times New Roman; color:gray; font-size: 16px;'>"
            f"{esc(text)}</span>")


def show_movie_details(film):
    d = fetch_details(film["movie_id"])
    st.header("")
    st.write("Searched Movie:")
    col_img, col_info = st.columns(2)
    with col_img:
        st.image(d["poster"])
    with col_info:
        fields = [
            ("TITRE ORIGINAL", film["title"]),
            ("DATE DE SORTIE", fmt_date(film["release_date"])),
            ("GENRE", fmt_list(film["genres"])),
            ("LANGUE ORIGINALE", film["original_language"]),
            ("RATING", f'{d["rating"]} ⭐' if d["rating"] else "N/A"),
            ("RÉALISATEUR", fmt_list(film["crew"])),
            ("ACTEURS", fmt_list(film["cast"])),
        ]
        for label, value in fields:
            a, b = st.columns(2)
            a.markdown(f"**{label} :**")
            b.markdown(span(value), unsafe_allow_html=True)
        a, b = st.columns(2)
        a.markdown("**TRAILER :**")
        if d["videos"]:
            b.markdown(f"[Watch Trailer](https://www.youtube.com/watch?v={d['videos'][0]['key']})")
    st.markdown("**SYNOPSIS :**")
    overview = film["overview"] if "overview" in film.index else ""
    st.markdown(span("" if is_missing(overview) else overview), unsafe_allow_html=True)


def show_similar(movie_id):
    st.header("Films Similaires :")
    ids = similar_movie_ids(movie_id)
    if not ids:
        st.write("No recommendations found for the selected movie.")
        return
    base = movies.drop_duplicates("movie_id").set_index("movie_id", drop=False)
    show_cards(base.loc[ids].reset_index(drop=True), "sim")


# =====================================================================
#  RECHERCHE + FILTRES (sidebar)
# =====================================================================
@st.cache_data(show_spinner=False)
def title_index():
    """{titre: movie_id} (un seul identifiant par titre)."""
    t = movies.dropna(subset=["title"]).drop_duplicates("title")
    return dict(zip(t["title"].astype(str), t["movie_id"].astype(int)))


@st.cache_data(show_spinner=False)
def suggest_titles(query, n=6, cutoff=0.6):
    """Titres qui contiennent le texte ou qui lui ressemblent (fautes d'orthographe)."""
    q = query.lower().strip()
    scored = []
    for title in title_index():
        tl = title.lower()
        if q in tl:
            score = 1.5 + (0.1 if tl.startswith(q) else 0)
        else:
            score = 0
            # on compare au titre entier, puis à son début (ignore le sous-titre)
            for cand in (tl, tl[:len(q) + 3]):
                sm = difflib.SequenceMatcher(None, q, cand)
                if sm.real_quick_ratio() >= cutoff and sm.quick_ratio() >= cutoff:
                    score = max(score, sm.ratio())
        if score >= cutoff:
            scored.append((-score, len(title), title))
    scored.sort()
    return [t for _, _, t in scored[:n]]


def show_suggestions():
    q = st.session_state.get("search_input", "").strip()
    if not q or "clicked_movie_id" in st.session_state:
        return
    index = title_index()
    if q.lower() in {t.lower() for t in index}:
        return                      # le titre existe : rien à suggérer
    suggestions = suggest_titles(q)
    if not suggestions:
        return
    st.caption("Aucun titre exact. Vouliez-vous dire :")
    for i, title in enumerate(suggestions):
        st.button(title, key=f"sugg_{i}", on_click=open_movie, args=(index[title],))


st.text_input("Search for a movie", key="search_input")
st.button("Search", on_click=start_search)
show_suggestions()


@st.cache_data(show_spinner=False)
def unique_options(col):
    values = set()
    for v in movies2[col]:
        values.update(as_list(v))
    return sorted(values)


selected_genres = st.sidebar.multiselect("Select genres", unique_options("genres"),
                                         key="sel_genres", on_change=reset_movie)
selected_actors = st.sidebar.multiselect("Select actors", unique_options("cast"),
                                         key="sel_actors", on_change=reset_movie)
selected_directors = st.sidebar.multiselect("Select directors", unique_options("crew"),
                                            key="sel_directors", on_change=reset_movie)


# =====================================================================
#  PAGES
# =====================================================================
def page_movie(movie_id):
    rows = movies[movies["movie_id"] == movie_id]
    if rows.empty:
        st.session_state.pop("clicked_movie_id", None)
        st.warning("Film introuvable.")
        return
    st.button("← Accueil", key="home_btn", on_click=go_home)
    show_movie_details(rows.iloc[0])
    show_similar(movie_id)


def page_search(query):
    if not query:
        st.info("Tape le titre d'un film puis clique sur Search.")
        return
    match = movies[movies["title"].str.lower() == query.lower()]
    if match.empty:
        st.header("")
        st.write("No recommendations found for the selected movie.")
        return
    film = match.iloc[0]
    show_movie_details(film)
    show_similar(film["movie_id"])


def page_filters():
    mask = pd.Series(True, index=movies2.index)
    if selected_genres:
        mask &= movies2["genres"].apply(lambda v: bool(set(as_list(v)) & set(selected_genres)))
    if selected_actors:
        mask &= movies2["cast"].apply(lambda v: bool(set(as_list(v)) & set(selected_actors)))
    if selected_directors:
        mask &= movies2["crew"].apply(lambda v: bool(set(as_list(v)) & set(selected_directors)))

    filtered = movies2[mask].copy()
    filtered["release_year"] = pd.to_datetime(filtered["release_date"], errors="coerce").dt.year
    filtered = filtered.dropna(subset=["release_year"])
    if filtered.empty:
        st.sidebar.warning("No movies available with valid release years in the selected criteria.")
        st.warning("Aucun film ne correspond à ces critères.")
        return

    lo, hi = int(filtered["release_year"].min()), int(filtered["release_year"].max())
    if lo < hi:
        y0, y1 = st.sidebar.slider("Select a range of release years", lo, hi, (lo, hi))
        filtered = filtered[(filtered["release_year"] >= y0) & (filtered["release_year"] <= y1)]
    else:
        st.sidebar.warning("There is only one year available in the selected criteria.")

    total_pages = max(1, math.ceil(len(filtered) / PER_PAGE))
    page = int(st.sidebar.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1))
    start = (page - 1) * PER_PAGE

    st.header("")
    show_cards(filtered.iloc[start:start + PER_PAGE], "filter")
    st.write("Page", page, "of", total_pages)


def page_home():
    st.header("")
    st.header("Films Populaires :")
    show_cards(movies.sort_values(by="popularity", ascending=False).head(10), "pop")
    st.header("Films Récents :")
    show_cards(movies.sort_values(by="release_date", ascending=False).head(10), "recent")


clicked = st.session_state.get("clicked_movie_id")
if clicked is not None:
    page_movie(clicked)
elif st.session_state.get("search_active", False):
    page_search(st.session_state.get("search_query", ""))
elif selected_genres or selected_actors or selected_directors:
    page_filters()
else:
    page_home()