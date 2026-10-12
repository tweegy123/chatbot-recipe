"""Public-hosting version: serves the same chatbot with Flask (PythonAnywhere, etc.).
chat.py, database.json, index.html and style.css stay exactly as they are."""
# This is about the publish in public web ( DO NOT TOUCH THIS CODE KASE SENSitive)
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from chat import reply_to

BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10_000 


@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.route("/style.css")
def stylesheet():
    return send_from_directory(BASE, "style.css")


@app.post("/chat.py")
def chat():
    message = (request.get_json(silent=True) or {}).get("message", "")
    return jsonify(reply_to(str(message).strip()[:300]))
