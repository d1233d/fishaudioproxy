from flask import Flask, request, jsonify, send_file
import requests
import io
import base64
import os
import boto3
import uuid
from botocore.exceptions import BotoCoreError

app = Flask(__name__)

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_DOMAIN = os.getenv("AWS_S3_DOMAIN")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


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
        "format":data.get("format")
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


    try:
        audio_bytes = audio_base64
        filename = f"{uuid.uuid4().hex}.{data.get('format', 'mp3')}"
        s3_key = f"tts_outputs/{filename}"

        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/{data.get('format', 'mp3')}",
            ACL="public-read"
        )

        audio_url = f"{AWS_S3_DOMAIN}/{s3_key}"

        return jsonify({
            "audio_url": audio_url
        })
    except BotoCoreError as e:
        return jsonify({"error": "Upload failed: {str(e)}"}), 500



@app.route("/openapi.json")
def openapi():
    return send_file("openapi.json", mimetype="application/json")

@app.route("/logo.png")
def logo():
    return send_file("logo.png", mimetype="image/png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)