from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "<h1>LEA — coming soon</h1><p>Listening Experience Album</p>"


if __name__ == "__main__":
    app.run(debug=True)