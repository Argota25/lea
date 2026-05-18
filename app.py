import sqlite3
import os
import re
from functools import wraps
from flask import Flask, render_template, g, abort, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# CRITICAL: this key signs the session cookie. NEVER commit a real secret to git.
# For local dev this fallback is fine; for AWS we'll set the env var.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-before-deploy")

# ---------- Database helpers ----------

DATABASE = 'lea.db'


def get_db():
    """Get a database connection scoped to the current request."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close the DB connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """Run a SELECT and return rows."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ---------- Auth helpers ----------

def login_required(f):
    """Decorator: redirect to login if no user_id in session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_email(email):
    """Basic email format check — good enough for MVP."""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


# ---------- Public routes ----------

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

@app.route("/library")
@login_required
def library():
    """User's library — albums they've purchased."""
    user_id = session["user_id"]
    albums = query_db(
        """
        SELECT albums.* FROM albums
        JOIN purchases ON purchases.album_id = albums.id
        WHERE purchases.user_id = ?
        ORDER BY purchases.purchased_at DESC
        """,
        [user_id]
    )
    return render_template("library.html", albums=albums)


# ---------- Auth routes ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    # Kill any existing session before registering
    session.clear()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        # Validation
        if not is_valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("register.html"), 400

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("register.html"), 400

        if password != confirmation:
            flash("Passwords don't match.")
            return render_template("register.html"), 400

        # Check for existing user
        existing = query_db("SELECT id FROM users WHERE email = ?", [email], one=True)
        if existing is not None:
            flash("An account with that email already exists.")
            return render_template("register.html"), 400

        # Create the user
        password_hash = generate_password_hash(password)
        db = get_db()
        cur = db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            [email, password_hash]
        )
        db.commit()

        # Log them in immediately
        session["user_id"] = cur.lastrowid
        flash("Welcome to LEA.")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    session.clear()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password required.")
            return render_template("login.html"), 400

        user = query_db("SELECT * FROM users WHERE email = ?", [email], one=True)

        # Generic error on either bad email OR bad password — prevents enumeration
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html"), 400

        session["user_id"] = user["id"]
        flash(f"Signed in as {user['email']}.")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Sign out and clear session."""
    session.clear()
    flash("Signed out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)