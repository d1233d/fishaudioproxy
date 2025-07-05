from flask import Flask, request, jsonify, send_file
import requests
import io
import base64
import os

app = Flask(__name__)

PROXY_TOKEN = os.getenv("PROXY_TOKEN")
FISH_API_URL = "https://api.fish.audio/v1/tts"

@app.route("/")
def home():
    return "FishAudio Proxy API is running."

@app.route("/proxy/tts", methods=["POST"])
def proxy_tts():
    data = request.get_json()
    if not data or data.get("proxy_token") != PROXY_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    payload = {
        "text": data.get("text"),
        "reference_id": data.get("reference_id"),
    }

    headers = {
        "Authorization": data.get("fish_api_key"),
        "Content-Type": "application/json",
        "model": data.get("model")
    }

    resp = requests.post(FISH_API_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        return jsonify({"error": "Fish.Audio API failed", "details": resp.text}), 500

    audio_data = resp.content
    audio_base64 = base64.b64encode(audio_data).decode("utf-8")

    return jsonify({
        "audio_base64": audio_base64,
        "format": payload["format"]
    })

@app.route("/openapi.json")
def openapi():
    return send_file("openapi.json", mimetype="application/json")

@app.route("/logo.png")
def logo():
    return send_file("logo.png", mimetype="image/png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)