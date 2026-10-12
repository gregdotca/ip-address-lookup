# Changelog

## 2026-10-11

- Fix an open redirect in the lookup form. `POST /` redirected to `"/" + ip_address`, so submitting `/evil.com` sent the visitor to `//evil.com`, another site (the same went for a forged `X-Forwarded-For` on `GET /`). The redirect is now built with `url_for`, which encodes the value and keeps it on this site. The submitted address is now stripped of surrounding whitespace, so a pasted ` 1.1.1.1` works, and an empty or whitespace-only field redirects to `/`.
- Fix cross-site scripting in the lookup results. The result was built as an HTML string in Python and rendered with `|safe`, and ip-api echoes the requested address back in `query` even for a failed lookup, so a link like `/<img src=x onerror=alert(1)>` ran script on the page. `lookup_ip_address` now returns the API's data, and `home.html` renders it with autoescaping. A failed lookup (`status` not `success`, or a response missing any field the page shows) gets the error message, without the echoed address it used to show above it.
- Add `ACR.md` with the project's [AI Code Rating](https://aicoderating.com/) (B1b), and its badge in `README.md`, to disclose how much of the code AI wrote and how it was checked.
- Add an `aria-label` to the IP Address input, matching its placeholder, so screen readers announce the field. A placeholder alone isn't a reliable accessible name.
- Add automatic dark mode that follows the system colour scheme, using daisyUI's `business` theme alongside `bumblebee`, with no toggle or JavaScript. Remove `data-theme` from `<html>`, since it would lock the page to one theme, and add a `color-scheme` meta tag. In dark mode the Lookup button uses a darker navy primary instead of the orange accent, and the corners use `bumblebee`'s rounder radii so both modes match.
- Build the page's CSS locally instead of loading Tailwind and daisyUI from jsDelivr. The Docker builder stage downloads the Tailwind 4.3.3 standalone CLI (checked against pinned SHA-256s for amd64 and arm64) and compiles `services/web/project/styles/app.css` into `project/assets/app.css`, which is gitignored. daisyUI 5.7.46 is vendored as a plugin, with only the `bumblebee` theme enabled. This removes the runtime dependency on a third-party CDN and ships only the CSS the template uses.
- Add a doctype, `lang="en"`, and a viewport meta tag to `home.html`, and drop classes that did nothing (`form`, `justify-left`, and `loading-circle`, which aren't Tailwind or daisyUI 5 classes).
- Update `CLAUDE.md` with the CSS build and dark mode.
- Add `CLAUDE.md` with the project's commands, how the dev and prod environment switch works, and an overview of the architecture, so future Claude Code sessions can get up to speed quickly.
- Update the copyright notices in `LICENSE` and `README.md` to `Copyright (c) 2024-2026 Greg Chetcuti <greg@chetcuti.com>`, adding the current year and contact email.
- Fix the installation URL in `README.md` to use `http://` rather than `https://`, since gunicorn serves plain HTTP on port 8093 (HTTPS needs a reverse proxy in front).
- Add this changelog.
