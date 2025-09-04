from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re

app = Flask(__name__)

def extract_video_id(url):
    """
    Extract the YouTube video ID from different URL formats.
    """
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

@app.route("/")
def home():
    return "✅ YouTube Transcript API server is running"

@app.route("/list", methods=["GET"])
def list_transcripts():
    """
    List all available transcripts (languages + type) for a given video.
    Example:
      /list?url=https://youtu.be/VIDEO_ID
    """
    url = request.args.get("url")
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available = []
        for transcript in transcript_list:
            available.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated
            })
        return jsonify({"available": available})
    except Exception as e:
        return jsonify({"error": str(e)}), 403

@app.route("/transcript", methods=["GET"])
def transcript():
    """
    Fetch transcript in requested languages (default: en).
    Example:
      /transcript?url=https://youtu.be/VIDEO_ID&langs=en&join=true
    """
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
