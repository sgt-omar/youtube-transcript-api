import os, re
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

app = Flask(__name__)
# Allow your Bolt app to call this API from the browser/app
CORS(app, resources={r"/*": {"origins": "*"}})

YOUTUBE_ID_RE = re.compile(
    r"(?:v=|/videos/|embed/|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})"
)

def extract_video_id(url_or_id: str) -> str | None:
    url_or_id = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    m = YOUTUBE_ID_RE.search(url_or_id)
    return m.group(1) if m else None

@app.get("/transcript")
def transcript():
    """
    GET /transcript?url=<youtube url or id>&langs=en,ar&join=true
    - langs: comma-separated preference order (default en,ar)
    - join: if "true", also return a flat "text" field
    """
    url = request.args.get("url", "")
    langs = request.args.get("langs", "en,ar").split(",")
    join_text = request.args.get("join", "true").lower() == "true"

    vid = extract_video_id(url)
    if not vid:
        return jsonify({"error": "Invalid YouTube URL or ID."}), 400

    try:
        # Try preferred human transcripts first; then auto-generated.
        listing = YouTubeTranscriptApi.list_transcripts(vid)
        transcript_data = None
        used_lang = None

        # Preferred languages (human-made)
        for lg in langs:
            try:
                t = listing.find_manually_created_transcript([lg])
                transcript_data = t.fetch()
                used_lang = t.language_code
                break
            except Exception:
                pass

        # If not found, try auto-generated
        if transcript_data is None:
            for lg in langs:
                try:
                    t = listing.find_generated_transcript([lg])
                    transcript_data = t.fetch()
                    used_lang = t.language_code
                    break
                except Exception:
                    pass

        if transcript_data is None:
            raise NoTranscriptFound(vid)

        payload = {
            "video_id": vid,
            "language": used_lang,
            "items": transcript_data,
        }
        if join_text:
            payload["text"] = " ".join([seg["text"] for seg in transcript_data if seg["text"].strip()])

        return jsonify(payload), 200

    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video."}), 403
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found."}), 404
    except VideoUnavailable:
        return jsonify({"error": "Video unavailable or private."}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    # Render sets PORT; default to 5000 locally
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
