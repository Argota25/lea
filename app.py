import sqlite3
import os
import re
from functools import wraps
from flask import Flask, render_template, g, abort, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import stripe

# Load environment variables from .env file BEFORE we access them
load_dotenv()

app = Flask(__name__)

# Flask session signing key — loaded from .env
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-do-not-use-in-prod")

# Stripe API key — server-side only, NEVER expose to frontend
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# ---------- Database helpers ----------

DATABASE = 'lea.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ---------- Auth helpers ----------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_email(email):
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


# ---------- Public routes ----------

@app.route("/")
def index():
    albums = query_db("SELECT * FROM albums ORDER BY release_date DESC")
    return render_template("index.html", albums=albums)


@app.route("/album/<int:album_id>")
def album(album_id):
    album = query_db("SELECT * FROM albums WHERE id = ?", [album_id], one=True)
    if album is None:
        abort(404)
    
    tracks = query_db(
        "SELECT * FROM tracks WHERE album_id = ? ORDER BY track_number",
        [album_id]
    )
    
    # Check if the currently logged-in user owns this album
    owned = False
    if session.get("user_id"):
        owned_row = query_db(
            "SELECT id FROM purchases WHERE user_id = ? AND album_id = ?",
            [session["user_id"], album_id],
            one=True
        )
        owned = owned_row is not None
    
    return render_template("album.html", album=album, tracks=tracks, owned=owned)


# ---------- Library (protected) ----------

@app.route("/library")
@login_required
def library():
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

@app.route("/track/<int:track_id>")
@login_required
def track(track_id):
    """Track liner notes page — owner-only content."""
    track = query_db("SELECT * FROM tracks WHERE id = ?", [track_id], one=True)
    if track is None:
        abort(404)
    
    album = query_db("SELECT * FROM albums WHERE id = ?", [track['album_id']], one=True)
    
    # Ownership gate: only album owners see liner notes
    owned = query_db(
        "SELECT id FROM purchases WHERE user_id = ? AND album_id = ?",
        [session["user_id"], album['id']],
        one=True
    )
    if owned is None:
        flash("Liner notes are exclusive to album owners.")
        return redirect(url_for("album", album_id=album['id']))
    
    return render_template("track.html", track=track, album=album)


# ---------- Purchase routes ----------

@app.route("/buy/<int:album_id>", methods=["POST"])
@login_required
def buy(album_id):
    """Initiate a Stripe Checkout session for the given album."""
    album = query_db("SELECT * FROM albums WHERE id = ?", [album_id], one=True)
    if album is None:
        abort(404)
    
    # Prevent buying an album the user already owns
    existing = query_db(
        "SELECT id FROM purchases WHERE user_id = ? AND album_id = ?",
        [session["user_id"], album_id],
        one=True
    )
    if existing is not None:
        flash("You already own this album.")
        return redirect(url_for("album", album_id=album_id))
    
    try:
        # Tell Stripe to create a one-time-use Checkout Session.
        # The line_items, price, and product info all come from OUR database,
        # never from the user's request — so they can't tamper with the price.
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": album["title"],
                        "description": f"by {album['artist']}",
                    },
                    "unit_amount": album["price_cents"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("purchase_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("album", album_id=album_id, _external=True),
            # Metadata travels round-trip with the session — we read it back on success.
            metadata={
                "user_id": str(session["user_id"]),
                "album_id": str(album_id),
            }
        )
        # 303 See Other = "go to this other URL via GET"
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Could not initiate purchase: {str(e)}")
        return redirect(url_for("album", album_id=album_id))


@app.route("/purchase/success")
@login_required
def purchase_success():
    """Verify Stripe payment succeeded, then record the purchase."""
    session_id = request.args.get("session_id")
    if not session_id:
        flash("Invalid session.")
        return redirect(url_for("index"))
    
    try:
        # SERVER-TO-SERVER VERIFICATION.
        # We call Stripe's API to ask "is this session real and paid?"
        # The redirect from Stripe is just a HINT; this call is the proof.
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Even if the session exists, only proceed if Stripe says it was actually paid
        if checkout_session.payment_status != "paid":
            flash("Payment was not completed.")
            return redirect(url_for("index"))
        
        # Pull user_id and album_id from metadata.
        # Stripe's StripeObject exposes metadata via attribute access (Stripe-native pattern).
        try:
            user_id_raw = checkout_session.metadata.user_id
            album_id_raw = checkout_session.metadata.album_id
        except AttributeError:
            flash("Purchase metadata missing — please contact support.")
            return redirect(url_for("index"))
        
        # Defensive: empty strings would slip past the AttributeError above
        if not user_id_raw or not album_id_raw:
            flash("Purchase metadata incomplete — please contact support.")
            return redirect(url_for("index"))
        
        user_id = int(user_id_raw)
        album_id = int(album_id_raw)

        # Defense in depth: verify the metadata user matches the currently logged-in user.
        # This stops someone from copying a success URL from another user's checkout.
        if user_id != session["user_id"]:
            flash("That checkout session doesn't belong to you.")
            return redirect(url_for("index"))
        
        # Record the purchase. UNIQUE(user_id, album_id) prevents duplicates if the user
        # refreshes this page — second insert will fail gracefully.
        db = get_db()
        try:
            db.execute(
                "INSERT INTO purchases (user_id, album_id, stripe_charge_id) VALUES (?, ?, ?)",
                [user_id, album_id, checkout_session.payment_intent]
            )
            db.commit()
            flash("Album purchased! Welcome to your library.")
        except sqlite3.IntegrityError:
            # User already owns it — could happen on page refresh after purchase
            flash("You already own this album.")
        
        return redirect(url_for("library"))
    
    except Exception as e:
        # Log to terminal for debugging, show user a clean message
        print(f"[purchase_success] {type(e).__name__}: {e}", flush=True)
        flash("Could not verify purchase. Please try again or contact support.")
        return redirect(url_for("index"))
# ---------- Auth routes ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not is_valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("register.html"), 400

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("register.html"), 400

        if password != confirmation:
            flash("Passwords don't match.")
            return render_template("register.html"), 400

        existing = query_db("SELECT id FROM users WHERE email = ?", [email], one=True)
        if existing is not None:
            flash("An account with that email already exists.")
            return render_template("register.html"), 400

        password_hash = generate_password_hash(password)
        db = get_db()
        cur = db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            [email, password_hash]
        )
        db.commit()
        session["user_id"] = cur.lastrowid
        flash("Welcome to LEA.")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password required.")
            return render_template("login.html"), 400

        user = query_db("SELECT * FROM users WHERE email = ?", [email], one=True)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html"), 400

        session["user_id"] = user["id"]
        flash(f"Signed in as {user['email']}.")
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)