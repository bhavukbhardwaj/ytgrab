# ytgrab

A small, self-hosted YouTube downloader. Paste a link, pick **MP4** (144p to 4K) or **audio** (MP3, M4A, Opus, WAV), and download. It runs on your own machine, in Docker or plain Python.

![CI](https://github.com/bhavukbhardwaj/ytgrab/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)

## Why this exists

"YouTube to MP3/MP4" websites are a well-known hazard. Many of them:

- redirect you through pop-ups, fake "Your device is infected" pages and forced notification prompts;
- serve **fake download buttons** that deliver installers, browser extensions or malware instead of your file;
- phish for logins, or harvest your IP, cookies and browsing data;
- re-encode in low quality, cap length and resolution, and put the good formats behind a paywall;
- vanish and re-appear on new domains every few weeks, so there is nothing to trust.

The underlying job is simple: look up a video's streams, fetch them, and convert if needed. Open-source tools already do this well. **ytgrab** puts a clean UI on [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org/) so you can run the whole thing yourself with no ads, no tracking, no third party in the middle, and code you can read.

## Features

- Title, channel, duration and thumbnail preview before downloading
- Video: MP4 at every resolution the video actually offers (144p to 2160p)
- Audio: MP3 (320/192 kbps), M4A, Opus, WAV
- Single videos only (playlists are ignored on purpose)
- YouTube-only allowlist, download concurrency cap, health endpoint
- Hardened Docker image: non-root, read-only filesystem, no capabilities, localhost-only port

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/bhavukbhardwaj/ytgrab.git && cd ytgrab
docker compose up -d --build
open http://127.0.0.1:5055      # or visit it in your browser
```

### Without Docker

```bash
brew install ffmpeg             # or: apt install ffmpeg
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py         # http://127.0.0.1:5055
```

Needs Python 3.10+ (current yt-dlp no longer supports 3.9).

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOST` | `127.0.0.1` (`0.0.0.0` in the image) | Bind address for the dev server |
| `PORT` | `5055` | Port |
| `MAX_CONCURRENT` | `2` | Simultaneous downloads; extra requests get HTTP 429 |
| `ALLOWED_HOSTS` | YouTube hosts | Comma-separated hostnames the server will accept |

## Technology

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | HTML, CSS, vanilla JavaScript (`fetch`, `Blob`) | Single page, no build step |
| Backend | Python 3.12, [Flask](https://flask.palletsprojects.com/) | JSON API, file streaming |
| Extraction | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Talks to YouTube, lists and fetches streams |
| Media | [ffmpeg](https://ffmpeg.org/) | Merges video+audio, converts to MP3/WAV/M4A |
| Server | [gunicorn](https://gunicorn.org/) (gthread) | Production WSGI server |
| Packaging | Docker, Docker Compose | Reproducible, hardened runtime |
| Quality | pytest, ruff, GitHub Actions, Dependabot | Tests, lint, CI, dependency updates |

## How it works (short version)

1. The browser sends the link to `POST /api/info`. The server validates the host, asks yt-dlp for metadata (no download) and returns title, thumbnail and the formats available.
2. You click a format. The browser calls `GET /api/download`.
3. The server takes a concurrency slot, has yt-dlp fetch the streams into a private temp directory, runs ffmpeg to merge or convert, then streams the finished file back and deletes it.

For the full high-level and low-level design, the reason downloading is possible at all, and where it bottlenecks, read **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Troubleshooting

- **Suddenly fails with errors about signatures, 403 or "page needs to be reloaded":** YouTube changed something. Update yt-dlp: `pip install -U yt-dlp`, or rebuild the image with `docker compose build --no-cache`.
- **Only low resolutions listed:** some videos are not offered in higher quality, or a region/age restriction applies.
- **"Server is busy":** you hit `MAX_CONCURRENT`. Wait for a download to finish or raise the limit.

## Responsible use

Only download content you own, that is licensed for it, or that you otherwise have permission to save. Downloading from YouTube may violate its Terms of Service, and copyright law applies to what you download. You are responsible for how you use this tool. It has no authentication, so keep it on localhost or behind an authenticating proxy.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Release history is in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE). yt-dlp is released under the Unlicense; ffmpeg under LGPL/GPL.
