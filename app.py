"""ytgrab: a tiny local web UI over yt-dlp. Paste a link, pick a format, download."""
import os
import re
import shutil
import tempfile
import threading
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, after_this_request, jsonify, render_template, request, send_file

app = Flask(__name__)

# Only these hosts are accepted, so the server can't be used as a generic fetcher (SSRF guard).
ALLOWED_HOSTS = set(
    os.environ.get(
        "ALLOWED_HOSTS", "youtube.com,www.youtube.com,m.youtube.com,music.youtube.com,youtu.be"
    ).split(",")
)
# Downloads are CPU/bandwidth heavy (yt-dlp + ffmpeg). Cap how many run at once; extra requests get 429.
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "2"))
slots = threading.BoundedSemaphore(MAX_CONCURRENT)

AUDIO_FORMATS = [
    {"id": "mp3-320", "label": "MP3 · 320 kbps", "codec": "mp3", "quality": "320"},
    {"id": "mp3-192", "label": "MP3 · 192 kbps", "codec": "mp3", "quality": "192"},
    {"id": "m4a", "label": "M4A · best quality", "codec": "m4a", "quality": "0"},
    {"id": "opus", "label": "Opus · best quality", "codec": "opus", "quality": "0"},
    {"id": "wav", "label": "WAV · lossless", "codec": "wav", "quality": "0"},
]
VIDEO_HEIGHTS = [2160, 1440, 1080, 720, 480, 360, 240, 144]


def clean_url(url: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Please enter a full http(s) link.")
    if parsed.hostname.lower() not in ALLOWED_HOSTS:
        raise ValueError("Only YouTube links are supported.")
    return url


def fetch_info(url: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.post("/api/info")
def info():
    try:
        url = clean_url((request.get_json(silent=True) or {}).get("url"))
        data = fetch_info(url)
    except Exception as e:  # yt-dlp raises a variety of errors
        return jsonify(error=re.sub(r"\x1b\[[0-9;]*m", "", str(e))), 400

    available = {f["height"] for f in data.get("formats", []) if f.get("height") and f.get("vcodec") != "none"}
    top = max(available or {0})
    videos = [{"id": f"mp4-{h}", "label": f"MP4 · {h}p"} for h in VIDEO_HEIGHTS if h <= top]
    if not videos and available:
        videos = [{"id": "mp4-best", "label": "MP4 · best available"}]

    return jsonify(
        title=data.get("title"),
        channel=data.get("uploader"),
        duration=data.get("duration"),
        thumbnail=data.get("thumbnail"),
        video=videos,
        audio=[{"id": a["id"], "label": a["label"]} for a in AUDIO_FORMATS],
    )


@app.get("/api/download")
def download():
    try:
        url = clean_url(request.args.get("url"))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    fmt = request.args.get("format", "")
    if not slots.acquire(blocking=False):
        return jsonify(error="Server is busy with other downloads. Try again in a moment."), 429

    tmp = tempfile.mkdtemp(prefix="ytgrab-")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": os.path.join(tmp, "%(title).150B.%(ext)s"),
    }

    if fmt.startswith("mp4-"):
        h = fmt[4:]
        if h != "best" and not h.isdigit():
            shutil.rmtree(tmp, ignore_errors=True)
            slots.release()
            return jsonify(error="Unknown format."), 400
        sel = "bv*+ba/b" if h == "best" else f"bv*[height<={int(h)}]+ba/b[height<={int(h)}]"
        opts.update(format=sel, merge_output_format="mp4")
    else:
        audio = next((a for a in AUDIO_FORMATS if a["id"] == fmt), None)
        if not audio:
            shutil.rmtree(tmp, ignore_errors=True)
            slots.release()
            return jsonify(error="Unknown format."), 400
        opts.update(
            format="bestaudio/best",
            postprocessors=[
                {"key": "FFmpegExtractAudio", "preferredcodec": audio["codec"], "preferredquality": audio["quality"]}
            ],
        )

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        path = os.path.join(tmp, os.listdir(tmp)[0])
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        slots.release()
        return jsonify(error=re.sub(r"\x1b\[[0-9;]*m", "", str(e))), 400

    @after_this_request
    def cleanup(resp):
        # Temp files live only for the duration of the response, then are removed.
        shutil.rmtree(tmp, ignore_errors=True)
        slots.release()
        return resp

    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    # Dev server. Defaults to localhost only; the Docker image uses gunicorn instead.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5055")))
