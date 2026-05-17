from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)

# Implement function for viewing/playing album 

# take in user input (user_id, password_hash)

# implement a buy feature

# Give unique key for album purchase utilizing metadata

