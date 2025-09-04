from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re

app = Flask(__name__)

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

@app.route("/")
def home():
    return "YouTube Transcript API is running 🎉"

@app.route("/transcript", methods=["GET"])
def transcript():
    url = request.args.get("url")
    langs = request.args.get("langs", "en").split(",")
    join = request.args.get("join", "false").lower() == "true"

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
        if join:
            formatter = TextFormatter()
            return jsonify({"transcript": formatter.format_transcript(transcript)})
        return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": str(e)}), 403
