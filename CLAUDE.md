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

- `./to-dev.sh`: moves the prod files to `*.PROD` and activates `docker-compose.DEV.yml` / `Dockerfile.DEV` (Flask debug server on port 5000, with `services/web/` bind-mounted to `/app` for live reload). Alongside it, `tailwindcss --watch=always` rebuilds `project/assets/app.css` into the mounted directory, so the file on the host ends up owned by root. `--watch=always` is needed because the container's stdin is closed.
- `./to-prod.sh`: reverses it.

Only the prod versions are tracked in git; `docker-compose.DEV.yml`, `Dockerfile.DEV`, `to-dev.sh`, `to-prod.sh`, and `test.py` are excluded via `.git/info/exclude`. Make sure the repo is in the prod state (`docker-compose.yml` uses gunicorn) before committing, or the dev files will show up as the tracked ones.

## Architecture

All app logic is in `services/web/project/__init__.py`; `services/web/manage.py` wraps it in a `FlaskGroup` so gunicorn can load `manage:app`. The gunicorn command has `--no-control-socket` because the app doesn't use gunicorn's `gunicornc` control tool, and the `app` user can't create its default socket in `/home/app/.gunicorn`.

- `GET /` redirects to `/<client IP>`; `POST /` (the lookup form) redirects to `/<submitted IP>`, with surrounding whitespace stripped, or back to `/` if nothing is left. Every lookup is therefore a shareable URL. The redirect is built with `url_for`, which encodes the value, so a typed address like `//evil.com` (or a forged `X-Forwarded-For`) can't send the visitor to another site; don't build it by string concatenation.
- `GET /<ip_address>` sleeps 0.25s (so the loading spinner is visible), then `lookup_ip_address` calls `http://ip-api.com/json/<ip>` (the address percent-encoded with `quote(..., safe="")` so it can't add a path or query string, and an `API_TIMEOUT` of 5 seconds, applied by requests to connecting and to each wait for data rather than the whole request, so a hung connection or response from ip-api is cut off; it doesn't cover the DNS lookup of `ip-api.com`) and returns the JSON as a dict, or `None` when the lookup fails (`status` isn't `success`), is missing any of `RESULT_FIELDS` (the fields `home.html` shows), or raises (including a timeout). `home.html` renders the dict's fields, or a generic "Unable to lookup" message for `None`.
- The client IP is `request.remote_addr`. Prod runs behind one reverse proxy (Caddy), so the app is wrapped in Werkzeug's `ProxyFix` with `x_for=1`, which sets `remote_addr` from the last `X-Forwarded-For` entry, the one Caddy adds. Don't read the header directly: a visitor can send their own, and with more than one entry it's a comma-separated list. If another proxy is ever added in front (such as a CDN), raise `x_for` to match. When the looked-up IP matches it, the page labels it as "Your Public IP Address".
- **Output is autoescaped: never add `|safe` or build HTML in Python.** ip-api echoes the requested address back in `query`, even for a failed lookup, so anything in the URL reaches the page; an unescaped `/<img src=x onerror=...>` link would run script on the site.
- **CSS is built at Docker build time, not loaded from a CDN.** The Tailwind 4 standalone CLI (version and per-architecture SHA-256s pinned as `ARG`s in the Dockerfile builder stage) compiles `project/styles/app.css` into `project/assets/app.css`, which is gitignored and copied into the final stage. `app.css` uses `source(none)` plus `@source "../templates"`, so Tailwind scans only the templates: a class used only from Python or JS won't be in the build unless it also appears in a template. daisyUI 5 is the vendored plugin `project/styles/daisyui-<version>.mjs`, with only the `bumblebee` (light) and `business` (dark) themes enabled. To upgrade either one, update the Dockerfile `ARG`s (and `Dockerfile.DEV`), or replace the `.mjs` file and its reference in `app.css`.
- **Dark mode** is automatic only, with no toggle, JavaScript, or `data-theme` attribute. `bumblebee --default, business --prefersdark` in `project/styles/app.css` puts `business` inside `@media (prefers-color-scheme: dark)` on `:root:not([data-theme])`, so adding `data-theme` to `<html>` would lock the page to one theme. A `color-scheme` meta tag in `home.html` tells the browser about both modes before the CSS loads. Use daisyUI theme colours (`base-content`, `base-200`, and so on), not hard-coded colour classes (`text-gray-*`, `bg-white`), so both modes keep working. Tailwind's `dark:` variant uses the same media query, so per-mode tweaks go there (the Lookup button is `btn-accent dark:btn-primary`). Dark-mode overrides of theme variables live in an unlayered rule at the end of `app.css`: a darker `--color-primary` for the button, and `bumblebee`'s `--radius-*` corner sizes so both modes match. Being unlayered, it beats daisyUI's layered theme.
- Static files are served from `project/assets/` at `/assets/...` (Flask's `static_folder`; use `url_for('static', ...)`). The favicon is vendored there. There's no JavaScript library: the Lookup button's `onclick` shows the spinner with one line of plain JavaScript.
- `templates/custom.headers` is optional, gitignored, and pulled into `<head>` with `{% include ... ignore missing %}`. It's the place for deployment-specific head tags (such as analytics) that shouldn't be in the repo.
