import sqlite3
from flask import Flask, render_template, g, abort

app = Flask(__name__)

# ---------- Database helpers ----------

DATABASE = 'lea.db'


def get_db():
    """Get a database connection scoped to the current request.
    
    Reuses the same connection across multiple calls within one request,
    then closes it automatically when the request ends.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # makes rows behave like dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close the DB connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """Run a SELECT and return rows.
    
    one=True returns a single row (or None). Otherwise returns a list of rows.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ---------- Routes ----------

@app.route("/")
def index():
    """Homepage — show all available albums."""
    albums = query_db("SELECT * FROM albums ORDER BY release_date DESC")
    return render_template("index.html", albums=albums)


@app.route("/album/<int:album_id>")
def album(album_id):
    """Album detail page — show album info and tracklist."""
    album = query_db("SELECT * FROM albums WHERE id = ?", [album_id], one=True)
    if album is None:
        abort(404)
    
    tracks = query_db(
        "SELECT * FROM tracks WHERE album_id = ? ORDER BY track_number",
        [album_id]
    )
    return render_template("album.html", album=album, tracks=tracks)


if __name__ == "__main__":
    app.run(debug=True)