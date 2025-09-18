import json
import os

FILENAME = "movies.json"

def get_movies():
    """
    Loads movies from the JSON file and returns them as
    a list of dictionaries.
    Returns an empty list if the file does not exist
    or is invalid.
    """
    if not os.path.exists(FILENAME):
        return []
    try:
        with open(FILENAME, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_movies(movies):
    """
    Saves the list of movie dictionaries to the JSON file.
    """
    with open(FILENAME, "w") as file:
        json.dump(movies, file, indent = 2)

def add_movie(title, rating, year):
    """
    Adds a new movie to the list.
    Overwrites if title already exists (case-insensitive).
    """
    movies = get_movies()

    for movie in movies:
        if movie.get("Title", "").lower() == title.lower():
            movie["Year"] = year
            movie["Rating"] = rating
            save_movies(movies)
            return

    new_movie = {"Title": title, "Rating": rating, "Year": year}
    movies.append(new_movie)
    save_movies(movies)

def delete_movie(delete_movie):
    """
    Deletes a movie from the list
    based on its titel (case-insensitive).
    """
    movies = get_movies()
    updated = [movie for movie in movies
               if movie.get("Title", "").lower() != delete_movie.lower()
               ]
    save_movies(updated)

def update_movie(check_movie, new_rating):
    """
    Updates the rating of an existing movie by title
    (case-insensitive).
    """
    movies = get_movies()
    for movie in movies:
        if movie.get("Title", "").lower() == check_movie.lower():
            movie["Rating"] = new_rating
            save_movies(movies)
            return
