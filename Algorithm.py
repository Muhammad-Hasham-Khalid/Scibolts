import os
import time

# data science imports
import math
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# utils import
from fuzzywuzzy import fuzz

df_movies = pd.read_csv("movies.csv", usecols=['movieId', 'title'], dtype={'movieId': 'int32', 'title': 'str'})
df_ratings = pd.read_csv("ratings.csv", usecols=['userId', 'movieId', 'rating'], dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})

num_users = len(df_ratings.userId.unique())
num_items = len(df_ratings.movieId.unique())

df_ratings_cnt_tmp = pd.DataFrame(df_ratings.groupby('rating').size(), columns=['count'])

# there are a lot more counts in rating of zero
total_cnt = num_users * num_items
rating_zero_cnt = total_cnt - df_ratings.shape[0]
# append counts of zero rating to df_ratings_cnt
df_ratings_cnt = df_ratings_cnt_tmp.append(
    pd.DataFrame({'count': rating_zero_cnt}, index=[0.0]),
    verify_integrity=True,
).sort_index()

df_ratings_cnt['log_count'] = np.log(df_ratings_cnt['count'])

df_movies_cnt = pd.DataFrame(df_ratings.groupby('movieId').size(), columns=['count'])

df_movies_cnt['count'].quantile(np.arange(1, 0.6, -0.05))

popularity_thres = 50
popular_movies = list(set(df_movies_cnt.query('count >= @popularity_thres').index))
df_ratings_drop_movies = df_ratings[df_ratings.movieId.isin(popular_movies)]

df_users_cnt = pd.DataFrame(df_ratings_drop_movies.groupby('userId').size(), columns=['count'])

df_users_cnt['count'].quantile(np.arange(1, 0.5, -0.05))

ratings_thres = 50
active_users = list(set(df_users_cnt.query('count >= @ratings_thres').index))
df_ratings_drop_users = df_ratings_drop_movies[df_ratings_drop_movies.userId.isin(active_users)]

# pivot and create movie-user matrix
movie_user_mat = df_ratings_drop_users.pivot(index='movieId', columns='userId', values='rating').fillna(0)
# create mapper from movie title to index
movie_to_idx = {
    movie: i for i, movie in
    enumerate(list(df_movies.set_index('movieId').loc[movie_user_mat.index].title))
}
# transform matrix to scipy sparse matrix
movie_user_mat_sparse = csr_matrix(movie_user_mat.values)

model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
# fit
model_knn.fit(movie_user_mat_sparse)

def fuzzy_matching(mapper, fav_movie, verbose=True):
    match_tuple = []
    # get match
    for title, idx in mapper.items():
        ratio = fuzz.ratio(title.lower(), fav_movie.lower())
        if ratio >= 60:
            match_tuple.append((title, idx, ratio))
    # sort
    match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
    if not match_tuple:
        print('Oops! No match is found')
        return False, [], []
    if verbose:
        result = [x[0] for x in match_tuple]
        print('Found possible matches in our database: {0}\n'.format(result))
    return True, match_tuple[0][1], result


def make_recommendation(model_knn, data, mapper, fav_movie, n_recommendations):
    res = [] # the resultant list
    # fit
    model_knn.fit(data)
    # get input movie index
    print('You have input movie:', fav_movie)
    flag, idx, res = fuzzy_matching(mapper, fav_movie, verbose=True)
    if flag:
        # inference
        print('Recommendation system start to make inference')
        print('......\n')
        distances, indices = model_knn.kneighbors(data[idx], n_neighbors=n_recommendations + 1)
        # get list of raw idx of recommendations
        raw_recommends = \
            sorted(list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())), key=lambda x: x[1])[:0:-1]
        # get reverse mapper
        reverse_mapper = {v: k for k, v in mapper.items()}
        # print recommendations
        for i, (idx, dist) in enumerate(raw_recommends):
            print('{0}: {1}, with distance of {2}'.format(i + 1, reverse_mapper[idx], dist))
            res.append(reverse_mapper[idx])
        return res
    else:
        return []

def resultant(my_favourite):
    print("Recommendation for :", my_favourite)
    result = make_recommendation(model_knn=model_knn, data=movie_user_mat_sparse, fav_movie=my_favourite, mapper=movie_to_idx, n_recommendations=5)
    return result
