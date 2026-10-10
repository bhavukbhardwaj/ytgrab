# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-10-11

### Added
- Web UI: paste a YouTube link, see title and thumbnail, pick a format.
- Video downloads as MP4 from 144p up to 4K (where the video offers it).
- Audio downloads as MP3 (320/192 kbps), M4A, Opus and WAV.
- YouTube-only host allowlist, concurrency cap with HTTP 429 when busy, `/healthz` endpoint.
- Docker image (non-root, read-only filesystem, healthcheck) and Compose file bound to localhost.
- Unit tests, GitHub Actions CI, Dependabot, and architecture documentation.
