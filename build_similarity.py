import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pickle.load(open('movie_informations/movie_information.pkl', 'rb'))

# IMPORTANT : l'index doit être 0..n-1 car app.py utilise similarity[index]
movies = movies.reset_index(drop=True)

def to_tokens(x):
    """Gère les listes ET les chaînes, et supprime les espaces
    (ex: 'Tom Hanks' -> 'TomHanks') pour que chaque nom reste un seul token."""
    if isinstance(x, (list, tuple, set)):
        return [str(i).replace(" ", "") for i in x]
    if pd.isna(x):
        return []
    return [str(x).replace(" ", "")]

def overview_tokens(x):
    return str(x).split() if pd.notna(x) else []

movies['tags'] = (
    movies['overview'].apply(overview_tokens)
    + movies['genres'].apply(to_tokens)
    + movies['cast'].apply(to_tokens)
    + movies['crew'].apply(to_tokens)
)
movies['tags'] = movies['tags'].apply(lambda t: " ".join(t).lower())

cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(movies['tags'])

similarity = cosine_similarity(vectors).astype(np.float32)  # float32 = fichier 2x plus léger

pickle.dump(similarity, open('movie_informations/similarity.pkl', 'wb'))
# Si tu as reset l'index, resauvegarde aussi le DataFrame pour rester cohérent :
pickle.dump(movies.drop(columns=['tags']), open('movie_informations/movie_information.pkl', 'wb'))

print("OK :", similarity.shape)