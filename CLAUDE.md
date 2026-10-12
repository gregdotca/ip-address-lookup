# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A single-page Flask app that looks up geolocation and network details for an IP address using the free [ip-api.com](https://ip-api.com) JSON API. Live demo: https://ip.greg.ca.

## Commands

Everything runs through Docker Compose; there's no test suite.

```bash
docker-compose up -d --build     # build and run (prod: gunicorn, host port 8093 -> 5000)
docker-compose logs -f web       # follow app logs
```

Linting happens inside the Docker build (builder stage), so a lint failure fails the build. To run it locally with the same settings:

```bash
flake8 --ignore=E501,W503,F401 services/web
```

### Dev vs prod environments

`docker-compose.yml` and `services/web/Dockerfile` are the **active** files. `to-dev.sh` and `to-prod.sh` swap them with their `.DEV`/`.PROD` counterparts by renaming files:

- `./to-dev.sh`: moves the prod files to `*.PROD` and activates `docker-compose.DEV.yml` / `Dockerfile.DEV` (Flask debug server on port 5000, with `services/web/` bind-mounted to `/app` for live reload).
- `./to-prod.sh`: reverses it.

Only the prod versions are tracked in git; `docker-compose.DEV.yml`, `Dockerfile.DEV`, `to-dev.sh`, and `test.py` are excluded via `.git/info/exclude`. Make sure the repo is in the prod state (`docker-compose.yml` uses gunicorn) before committing, or the dev files will show up as the tracked ones.

## Architecture

All app logic is in `services/web/project/__init__.py`; `services/web/manage.py` wraps it in a `FlaskGroup` so gunicorn can load `manage:app`.

- `GET /` redirects to `/<client IP>`; `POST /` (the lookup form) redirects to `/<submitted IP>`. Every lookup is therefore a shareable URL.
- `GET /<ip_address>` sleeps 0.25s (so the loading spinner is visible), calls `http://ip-api.com/json/<ip>`, and builds the result as a raw HTML string (`page_body`). Any exception, including missing keys on a failed lookup, becomes a generic "Unable to lookup" message.
- The client IP comes from `X-Forwarded-For` (falling back to `remote_addr`), since prod runs behind a reverse proxy. When the looked-up IP matches it, the page labels it as "Your Public IP Address".
- `templates/home.html` renders `page_body` with `|safe`, so the HTML built in Python isn't escaped. Escape any new user- or API-sourced values before adding them to `page_body`.
- Styling is Tailwind (browser build) plus DaisyUI from jsDelivr; jQuery is served locally from `project/assets/` (Flask's `static_folder`), and is only used to show the spinner on submit.
- `templates/custom.headers` is optional, gitignored, and pulled into `<head>` with `{% include ... ignore missing %}`. It's the place for deployment-specific head tags (such as analytics) that shouldn't be in the repo.
