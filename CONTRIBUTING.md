# Contributing to ytgrab

Thanks for helping. By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

You need Python 3.10+ (3.12 recommended) and ffmpeg, or just Docker.

```bash
git clone https://github.com/bhavukbhardwaj/ytgrab.git && cd ytgrab
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt ruff
.venv/bin/python app.py          # http://127.0.0.1:5055
# or
docker compose up -d --build
```

## Layout

```
app.py              Flask app: validation, yt-dlp calls, streaming the file back
templates/          the single-page UI (no build step)
tests/              pytest unit tests (yt-dlp is mocked; no network needed)
Dockerfile          python:3.12-slim + ffmpeg + gunicorn, non-root
docs/ARCHITECTURE.md  HLD, LLD, internals and bottlenecks
```

## Checks (CI runs these on every PR)

```bash
ruff check .
pytest -q
docker build -t ytgrab:test . && docker run --rm ytgrab:test yt-dlp --version
```

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`. Mark breaking changes with `!` and a `BREAKING CHANGE:` footer.

## Pull requests

- `main` is protected: changes land through a pull request with passing CI and a review.
- Keep each PR to one change, fill in the template, and add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
- If YouTube changes break downloads, the fix is usually bumping `yt-dlp`; say so in the PR.

## Releases (maintainers)

SemVer. Move `Unreleased` entries under a new version in `CHANGELOG.md`; bump `VERSION` and the `org.opencontainers.image.version` label in the `Dockerfile` (CI fails if they disagree); commit `chore(release): X.Y.Z`; create an annotated tag `vX.Y.Z`; push with tags; publish a GitHub Release with the changelog section.

## License

Contributions are licensed under the [MIT License](LICENSE).
