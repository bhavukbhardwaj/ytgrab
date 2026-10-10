import pytest

import app as ytgrab


@pytest.fixture
def client():
    ytgrab.app.config["TESTING"] = True
    return ytgrab.app.test_client()


def test_healthz(client):
    assert client.get("/healthz").get_json() == {"status": "ok"}


@pytest.mark.parametrize(
    "url",
    ["", "not a url", "ftp://youtube.com/x", "http://169.254.169.254/latest/meta-data", "https://evil.example/watch?v=1"],
)
def test_rejects_non_youtube_urls(client, url):
    r = client.post("/api/info", json={"url": url})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_info_lists_formats(client, monkeypatch):
    monkeypatch.setattr(
        ytgrab,
        "fetch_info",
        lambda url: {
            "title": "t",
            "uploader": "c",
            "duration": 10,
            "thumbnail": "x",
            "formats": [
                {"height": 1080, "vcodec": "avc1"},
                {"height": 360, "vcodec": "avc1"},
                {"height": None, "vcodec": "none"},
            ],
        },
    )
    d = client.post("/api/info", json={"url": "https://youtu.be/abc"}).get_json()
    assert d["video"][0]["id"] == "mp4-1080"
    assert "mp4-2160" not in [v["id"] for v in d["video"]]
    assert {a["id"] for a in d["audio"]} >= {"mp3-320", "m4a", "wav"}


def test_download_rejects_unknown_format(client):
    r = client.get("/api/download", query_string={"url": "https://youtu.be/abc", "format": "exe"})
    assert r.status_code == 400


def test_download_busy_returns_429(client):
    held = [ytgrab.slots.acquire(blocking=False) for _ in range(ytgrab.MAX_CONCURRENT)]
    try:
        r = client.get("/api/download", query_string={"url": "https://youtu.be/abc", "format": "mp3-192"})
        assert r.status_code == 429
    finally:
        for h in held:
            if h:
                ytgrab.slots.release()


def test_download_rejects_malformed_video_format_and_frees_slot(client):
    r = client.get("/api/download", query_string={"url": "https://youtu.be/abc", "format": "mp4-abc"})
    assert r.status_code == 400
    # the slot must have been released, so all slots are still available
    held = [ytgrab.slots.acquire(blocking=False) for _ in range(ytgrab.MAX_CONCURRENT)]
    assert all(held)
    for _ in held:
        ytgrab.slots.release()
