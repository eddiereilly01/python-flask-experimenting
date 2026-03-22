from flask import Flask, jsonify
from fetch import fetch

app = Flask(__name__)

fetch()

@app.route("/")
def health():
    return jsonify({"status": "running"})

@app.route("/scrape")
def manual_scrape():
    fetch()
    return jsonify({"status": "done"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
