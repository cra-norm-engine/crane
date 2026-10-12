# Deploying the CRANE docs to GitHub Pages

This folder is a self-contained static documentation site — plain HTML/CSS/JS, no build step.

## Files
- `index.html` … `contributing.html` — the ten documentation pages
- `assets/docs.css` — design system (light + dark)
- `assets/docs.js` — sidebar, topbar, theme toggle, search, on-page TOC
- Current dashboard, product inventory, product workspace, and vulnerability screenshots live in `screenshots/` and are shared with the repository README. Include that folder when deploying the site.
- Older feature screenshots are referenced directly from the repo's `raw.githubusercontent.com` URLs.

## Option A — publish from a `/docs` folder (recommended, keeps it separate from the app)
1. Create a `docs/` folder on your default branch and drop these files into it
   (so you have `docs/index.html`, `docs/assets/…`, etc.).
2. In the repo: **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **Deploy from a branch**.
4. Select branch `main` and folder `/docs`, then **Save**.
5. The site appears at `https://cra-norm-engine.github.io/crane/` within a minute or two.

## Option B — publish from a `gh-pages` branch
1. Push these files to the root of a `gh-pages` branch.
2. **Settings → Pages → Source → Deploy from a branch → `gh-pages` / `(root)`**.

## Notes
- The repo already has a root `index.html`. Putting the docs in `docs/` (Option A) avoids any clash with it.
- All links between pages are relative, so the site works at any base path.
- No Jekyll processing is needed; if you ever see assets being stripped, add an empty `.nojekyll` file next to `index.html`.
- A custom domain can be set under **Settings → Pages → Custom domain**.
