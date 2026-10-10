FROM python:3.12-slim

LABEL org.opencontainers.image.title="ytgrab" \
      org.opencontainers.image.description="Self-hosted YouTube downloader (MP4 / MP3 / M4A / WAV) over yt-dlp" \
      org.opencontainers.image.source="https://github.com/bhavukbhardwaj/ytgrab" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5055

# ffmpeg: merges video+audio streams and converts to MP3/WAV/M4A
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chmod=644 app.py .
COPY --chmod=755 templates ./templates

# Run as an unprivileged user
RUN useradd --system --uid 10001 --no-create-home ytgrab
USER ytgrab

EXPOSE 5055
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5055/healthz',timeout=2)" || exit 1

# gthread: downloads are I/O bound and long-lived, so use threads, not many processes.
# --timeout is high because a 4K download + merge can take minutes.
CMD ["gunicorn", "--bind", "0.0.0.0:5055", "--workers", "1", "--threads", "8", "--timeout", "900", "app:app"]
