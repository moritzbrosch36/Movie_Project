from sqlalchemy import create_engine, text

# ---------------------------
# Database setup
# ---------------------------
DB_URL = "sqlite:///movies.db"
engine = create_engine(DB_URL, echo=True)

# Create the movies table if it does not exist
with engine.begin() as connection:  # auto commit
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL,
            poster_url TEXT
        )
    """))

# ---------------------------
# CRUD functions
# ---------------------------
def list_movies():
    """Retrieve all movies from the database."""
    try:
        with engine.begin() as connection:
            result = connection.execute(text(
                "SELECT title, year, rating, poster_url FROM movies"
            ))
            movies = result.fetchall()
        return {
            row[0]: {"year": row[1], "rating": row[2], "poster_url": row[3]}
            for row in movies
        }
    except Exception as e:
        print(f"⚠️ Error fetching movies: {e}")
        return {}


def add_movie(title, year, rating=None, poster_url=None):
    """Add a new movie to the database."""
    if not title.strip():
        print("⚠️ Movie title cannot be empty.")
        return
    try:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO movies (title, year, rating, poster_url)
                    VALUES (:title, :year, :rating, :poster_url)
                """),
                {
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "poster_url": poster_url
                }
            )
        print(f"✅ Movie '{title}' added successfully.")
    except Exception as e:
        print(f"⚠️ Error adding movie '{title}': {e}")


def delete_movie(title):
    """Delete a movie from the database."""
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("DELETE FROM movies WHERE title = :title"),
                {"title": title}
            )
        if result.rowcount > 0:
            print(f"✅ Movie '{title}' deleted successfully.")
        else:
            print(f"⚠️ Movie '{title}' not found.")
    except Exception as e:
        print(f"⚠️ Error deleting movie '{title}': {e}")


def update_movie(title, rating=None, poster_url=None):
    """Update a movie's rating and/or poster URL in the database."""
    if rating is None and poster_url is None:
        print("⚠️ Nothing to update. Provide rating or poster_url.")
        return

    try:
        with engine.begin() as connection:
            if rating is not None and poster_url is not None:
                query = text("""
                    UPDATE movies 
                    SET rating = :rating, poster_url = :poster_url 
                    WHERE title = :title
                """)
                params = {
                    "title": title, "rating": rating, "poster_url": poster_url
                }
            elif rating is not None:
                query = text(
                    "UPDATE movies SET rating = :rating WHERE title = :title"
                )
                params = {"title": title, "rating": rating}
            else:  # only poster_url
                query = text(
                    "UPDATE movies "
                    "SET poster_url = :poster_url "
                    "WHERE title = :title"
                )
                params = {"title": title, "poster_url": poster_url}

            result = connection.execute(query, params)

        if result.rowcount > 0:
            print(f"✅ Movie '{title}' updated successfully.")
        else:
            print(f"⚠️ Movie '{title}' not found.")
    except Exception as e:
        print(f"⚠️ Error updating movie '{title}': {e}")