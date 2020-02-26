import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies_dataset=pd.read_csv('movies.csv')
ratings_dataset=pd.read_csv('ratings.csv')

Genre = []
Genres = {}
for num in range(0,len(movies_dataset)):
    key = movies_dataset.iloc[num]['title']
    value = movies_dataset.iloc[num]['genres'].split('|')
    Genres[key] = value
    Genre.append(value)

movies_dataset['new'] = Genre

p = re.compile(r"(?:\((\d{4})\))?\s*$")
years = []
for movies in movies_dataset['title']:
    m = p.search(movies)
    year = m.group(1)
    years.append(year)
movies_dataset['year'] = years

movies_name = []
raw = []
for movies in movies_dataset['title']:
    m = p.search(movies)
    year = m.group(0)
    new = re.split(year, movies)
    raw.append(new)
for i in range(len(raw)):
    movies_name.append(raw[i][0][:-2])

movies_dataset['movie_name']=movies_name

movies_dataset['new'] = movies_dataset['new'].apply(' '.join)

tfid = TfidfVectorizer(stop_words='english')
#matrix after applying the tfidf
matrix = tfid.fit_transform(movies_dataset['new'])

cosine_sim = cosine_similarity(matrix, matrix)

movies_dataset = movies_dataset.reset_index()
titles = movies_dataset['movie_name']
indices = pd.Series(movies_dataset.index, index=movies_dataset['movie_name'])


def recommendation(movie):
    result = []
    # Getting the id of the movie for which the user want recommendation
    ind = indices[movie]
    # Getting all the similar cosine score for that movie
    sim_scores = list(enumerate(cosine_sim[ind]))
    # Sorting the list obtained
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    # Getting all the id of the movies that are related to the movie Entered by the user
    movie_id = [iu[0] for iu in sim_scores]
    # Variable to print only top 10 movies
    count = 0
    for ied in range(0, len(movie_id)):
        # to ensure that the movie entered by the user is doesn't come in his/her recommendation
        if ind != movie_id[ied]:
            ratings = ratings_dataset[ratings_dataset['movieId'] == movie_id[ied]]['rating']
            avg_ratings = round(np.mean(ratings), 2)
            # To print only those movies which have an average ratings that is more than 3.5
            if avg_ratings > 3.5:
                count += 1
                result.append(titles[movie_id[ied]])
            if count >= 5:
                break
    return result
'''
result = recommendation(text)
df_result = pd.DataFrame(result)
df_result.columns = ['Movies', 'Ratings']
df_result = df_result.sort_values(by=['Ratings'], ascending=False)
df_result.index = range(1, 11)
'''