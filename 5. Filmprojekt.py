"""
A simple command-line movie database application.

Features:
- Add, delete, update, and list movies.
- View statistics such as average and median rating.
- Get a random movie suggestion.
- Search movies by partial name (case-insensitive).
- View movies sorted by rating or year.
- Filter movies by rating and year range.
- Exit the application via menu option.
"""

import random
import requests
import os
from dotenv import load_dotenv
import re
import statistics
import movie_storage_sql as storage

# .env-data load
load_dotenv()

API_KEY = os.getenv("API_KEY")
OMDB_URL = os.getenv("OMDB_URL")

MAX_TITLE_LENGTH = 40

# Option 1: List movies
def list_movies(_=None):
    """List all movies with year and rating."""
    movies = storage.list_movies()
    print(f"{len(movies)} movies in total")
    for title, data in movies.items():
        print(f"{title} ({data['year']}): {data['rating']}")


# Option 2: Add movie
def add_movie(_=None):
    """Add a new movie using OMDb API lookup, with robust error handling."""

    # --- 1️⃣ Title-Input ---
    while True:
        title = input("Enter movie title: ").strip()
        if not title:
            print("⚠️ Movie title cannot be blank.")
        elif not re.search(r"\w", title, re.UNICODE):
            print("⚠️ Title must contain at least one letter or number.")
        else:
            break

    # --- 2️⃣ API-Request with detailed errors ---
    params = {"t": title, "apikey": API_KEY}
    try:
        response = requests.get(OMDB_URL, params=params, timeout=5)
        response.raise_for_status()  # Check HTTP error codes
    except requests.exceptions.ConnectionError:
        print("⚠️ No internet connection. Please check your network.")
        return
    except requests.exceptions.Timeout:
        print("⚠️ The request timed out. Try again later.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"⚠️ HTTP error: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error connecting to OMDb API: {e}")
        return

    # --- 3️⃣ Evaluate JSON ---
    try:
        data = response.json()
    except ValueError:
        print("⚠️ Invalid JSON response from OMDb.")
        return

    if data.get("Response") == "False":
        print(f"⚠️ Movie '{title}' not found in OMDb.")
        return

    # --- 4️⃣ Extract movie data ---
    movie_title = data.get("Title", title)

    # Parse Year safely
    year_raw = data.get("Year", "")
    try:
        movie_year = int(year_raw.split("–")[0])
    except (ValueError, AttributeError):
        movie_year = 0

    # Parse IMDb ratings safely
    try:
        movie_rating = (
            float(data.get("imdbRating"))
            if data.get("imdbRating") not in (None, "N/A") else None
        )
    except ValueError:
        movie_rating = None

    poster_url = data.get("Poster", "")

    # --- 5️⃣ Check for duplicates ---
    try:
        movies = storage.list_movies()
    except Exception as e:
        print(f"⚠️ Error accessing movie database: {e}")
        return

    if movie_title.lower() in (m.lower() for m in movies):
        print(f"⚠️ Movie '{movie_title}' already exists in the database.")
        return

    # --- 6️⃣ User rating (if necessary) ---
    while movie_rating is None or movie_rating == 0:
        try:
            user_input = input("Enter movie rating (0-10): ").strip()
            movie_rating = float(user_input)
            if not (0 <= movie_rating <= 10):
                print("⚠️ Rating must be between 0 and 10.")
                movie_rating = None
        except ValueError:
            print("⚠️ Invalid input. Please enter a number between 0 and 10.")

    # --- 7️⃣ Save to database ---
    try:
        storage.add_movie(movie_title, movie_year, movie_rating, poster_url)
    except Exception as e:
        print(f"⚠️ Failed to add movie to database: {e}")
        return

    print(
        f"✅ Added movie: {movie_title} ({movie_year}) "
        f"| Rating: {movie_rating} "
        f"| Poster: {poster_url}"
    )


# Option 3: Delete movie
def delete_movie(_=None):
    """Delete a movie by title."""
    title = input("Enter movie to delete: ").strip()
    movies = storage.list_movies()

    if title in movies:
        storage.delete_movie(title)
        print(f"🗑️ Movie '{title}' successfully deleted.")
    else:
        print(f"⚠️ Movie '{title}' doesn't exist.")


# Option 4: Update movie rating
def update_movie_rating(_=None):
    """Update the rating of an existing movie."""
    title = input("Enter movie name to update: ").strip()
    movies = storage.list_movies()

    if title not in movies:
        print(f"⚠️ Movie '{title}' doesn't exist.")
        return

    try:
        current_rating = movies[title]["rating"]
        print(f"Current rating of '{title}': {current_rating}")
        new_rating = float(input("Enter new movie rating (0-10): "))
        if not (0 <= new_rating <= 10):
            raise ValueError("Rating must be between 0 and 10.")
    except ValueError as error:
        print(f"Invalid rating: {error}")
        return

    confirm = input(
        "Do you really want to update the rating? (y/n): "
    ).strip().lower()
    if confirm != "y":
        print("Update cancelled.")
        return

    storage.update_movie(title, new_rating)
    print(f"✅ Movie '{title}' successfully updated.")


# Option 5: Show statistics
def show_movie_stats(_=None):
    """Show average, median, best, and worst movies."""
    movies = storage.list_movies()
    if not movies:
        print("❌ No movies in the database.")
        return

    ratings = [
        data["rating"] for data in movies.values()
        if isinstance(data.get("rating"), (int, float))
    ]
    if not ratings:
        print("⚠️ No valid ratings found.")
        return

    average_rating = sum(ratings) / len(ratings)
    median = statistics.median(ratings)

    max_rating = max(ratings)
    min_rating = min(ratings)
    best_movies = [
        title for title, data in movies.items()
        if data["rating"] == max_rating
    ]
    worst_movies = [
        title for title, data in movies.items()
        if data["rating"] == min_rating
    ]

    print("\n📊 Movie Statistics")
    print("-" * 40)
    print(f"⭐️ Average Rating : {average_rating:.1f}")
    print(f"📈 Median Rating  : {median:.1f}")
    print(f"🏆 Best Movie(s)  : {', '.join(best_movies)} ({max_rating})")
    print(f"💩 Worst Movie(s) : {', '.join(worst_movies)} ({min_rating})")


# Option 6: Random movie
def recommend_random_movie(_=None):
    """Suggest a random movie."""
    movies = storage.list_movies()
    if not movies:
        print("No movies in the database.")
        return

    title, data = random.choice(list(movies.items()))
    print("\n🎬 Movie Recommendation")
    print("-" * 40)
    print(f"🎞️ Title : {title}")
    print(f"⭐ Rating: {data['rating']}")
    print(f"📅 Year  : {data['year']}")


# Option 7: Search movies
def search_movies(_=None):
    """Search movies by partial title (case-insensitive)."""
    query = input("Enter part of movie name: ").strip().lower()
    movies = storage.list_movies()
    matches = {
        title: data for title, data in movies.items()
        if query in title.lower()
    }

    if matches:
        print(f"Found movies ({len(matches)}):")
        print("-" * 41)
        for title, data in matches.items():
            print(f"{title} ({data['year']}): Rating {data['rating']}")
            print("-" * 41)
    else:
        print("No movies found.")


# Option 8: Sort movies by rating
def sort_movies_by_rating(_=None):
    """Display movies sorted by rating (high to low)."""
    movies = storage.list_movies()
    sorted_movies = sorted(movies.items(),
                           key=lambda x: x[1]["rating"],
                           reverse=True)

    print(f"{'Title':<40} {'Year':<8} {'Rating':<6}")
    print("-" * 56)
    for title, data in sorted_movies:
        display_title = (            title) if len(title) <= MAX_TITLE_LENGTH \
            else title[:MAX_TITLE_LENGTH - 3] + "..."
        print(f"{display_title:<40} {data['year']:<8} {data['rating']:<6}")


# Option 9: Sort movies by year
def sort_movies_by_year(_=None):
    """Display movies sorted by year (newest first)."""
    movies = storage.list_movies()
    sorted_movies = sorted(movies.items(),
                           key=lambda x: x[1]["year"],
                           reverse=True)

    print(f"{'Title':<40} {'Year':<8} {'Rating':<6}")
    print("-" * 56)
    for title, data in sorted_movies:
        display_title = (title) if len(title) <= MAX_TITLE_LENGTH \
            else title[:MAX_TITLE_LENGTH - 3] + "..."
        print(f"{display_title:<40} {data['year']:<8} {data['rating']:<6}")


# Option 10: Filter movies
def filter_movies_by_criteria(_=None):
    """Filter movies by minimum rating and year range."""
    movies = storage.list_movies()

    min_rating_input = input(
        "Enter minimum rating (leave blank for no minimum): "
    ).strip()
    start_year_input = input(
        "Enter start year (leave blank for no start): "
    ).strip()
    end_year_input = input(
        "Enter end year (leave blank for no end): "
    ).strip()

    try:
        min_rating = float(min_rating_input) if min_rating_input else 0
    except ValueError:
        print("⚠️ Invalid input for rating, default 0 used.")
        min_rating = 0

    try:
        year_from = int(start_year_input) if start_year_input else 0
    except ValueError:
        print("⚠️ Invalid input for start year, default 0 used.")
        year_from = 0

    try:
        year_to = int(end_year_input) if end_year_input else 9999
    except ValueError:
        print("⚠️ Invalid input for end year, default 9999 used.")
        year_to = 9999

    filtered_movies = {
        title: data
        for title, data in movies.items()
        if min_rating <= data["rating"] <= 10
           and year_from <= data["year"] <= year_to
    }

    if filtered_movies:
        print(f"\nFound films ({len(filtered_movies)}):")
        print(f"{'Title':<40} {'Year':<8} {'Rating':<6}")
        print("-" * 56)
        for title, data in filtered_movies.items():
            print(f"{title:<40} {data['year']:<8} {data['rating']:<6}")
    else:
        print("\nNo film meets the filter criteria.")


# Option 11: Generate Website
def generate_website(_=None):
    """Generate an HTML website showing all movies with poster, title, and year."""
    OUTPUT_HTML = "index.html"
    PLACEHOLDER_POSTER = "placeholder.jpg"  # Fallback, falls kein Poster vorhanden

    HTML_TEMPLATE = """
    <html>
    <head>
        <title>Movie Library</title>
        <link rel="stylesheet" href="style.css"/>
    </head>
    <body>
        <div class="list-movies-title">
            <h1>Movie Library</h1>
        </div>
        <div>
            <ol class="movie-grid">
                __TEMPLATE_MOVIE_GRID__
            </ol>
        </div>
    </body>
    </html>
    """

    movies = storage.list_movies()
    if not movies:
        movie_grid = "<p>No movies in the database.</p>"
    else:
        movie_grid = ""
        for title, data in movies.items():
            poster = data.get("poster_url") or PLACEHOLDER_POSTER
            year = data.get("year", "N/A")
            movie_grid += f"""
            <li>
                <div class="movie">
                    <img class="movie-poster" src="{poster}" alt="Poster of {title}"/>
                    <div class="movie-title">{title}</div>
                    <div class="movie-year">{year}</div>
                </div>
            </li>
            """

    html_content = HTML_TEMPLATE.replace("__TEMPLATE_MOVIE_GRID__", movie_grid)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Website generated successfully at '{OUTPUT_HTML}' with {len(movies)} movies.")


# Option 0: Exit
def exit_program(_=None):
    """Exit the program."""
    print("Bye!")
    exit()


# Menu actions mapping
menu_actions = {
    "0": exit_program,
    "1": list_movies,
    "2": add_movie,
    "3": delete_movie,
    "4": update_movie_rating,
    "5": show_movie_stats,
    "6": recommend_random_movie,
    "7": search_movies,
    "8": sort_movies_by_rating,
    "9": sort_movies_by_year,
    "10": filter_movies_by_criteria,
    "11": generate_website
}


def main():
    while True:
        print("\n********** My Movie Database **********\n")
        print("Menu:")
        print("0.  Exit")
        print("1.  List movies")
        print("2.  Add movie")
        print("3.  Delete movie")
        print("4.  Update movie rating")
        print("5.  Stats")
        print("6.  Random movie")
        print("7.  Search movies")
        print("8.  Movies sorted by rating")
        print("9.  Movies sorted by year")
        print("10. Filter movies")
        print("11. Generate website")
        print()

        your_choice = input("Enter choice (0-10): ").strip()
        print()

        action = menu_actions.get(your_choice)

        if action:
            action()
        else:
            print("❌ Invalid choice, please select a number from 0 to 10.")

        print()
        input("Press enter to continue...")
        print()


if __name__ == "__main__":
    main()
