# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's [private vulnerability reporting](https://github.com/bhavukbhardwaj/ytgrab/security/advisories/new) and include what you found, how to reproduce it, and the impact. Expect an acknowledgement within 7 days.

## Design notes and scope

- **Localhost by default.** The dev server binds `127.0.0.1` and Compose publishes `127.0.0.1:5055`. There is **no authentication**. If you expose it beyond your machine, put an authenticating reverse proxy in front of it.
- **No generic fetcher.** URLs are checked against a host allowlist (YouTube only by default) so the server can't be pointed at internal addresses (SSRF).
- **Format values are validated** before use; user input never reaches a shell. yt-dlp is called as a library, not through `subprocess` with string building.
- **Container hardening:** non-root user, read-only root filesystem, `cap_drop: ALL`, `no-new-privileges`, and a size-limited tmpfs for downloads.
- **Resource abuse:** concurrent downloads are capped (`MAX_CONCURRENT`, default 2); extra requests receive HTTP 429.
- Relevant report areas: allowlist bypasses, path handling for downloaded files, and the Docker image.
