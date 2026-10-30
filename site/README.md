# KIN Campus Edition — Pitch Website

Working student-built landing-page prototype.

- [Preview source](./index.html): independent black/gold OU-inspired presentation
- Main navigation, hero, feature cards, core agent explanation, interactive ~20-second four-scene walkthrough
- Floating scripted KIN chat preview (does **not** call a live model)
- Responsive page with reduced-motion styles and accessible button labels
- Link to open-source KIN repository

**IMPORTANT:** The GitHub-hosted version is a compact single-file prototype with a scripted walkthrough. The downloadable `KIN_Pitch_Website.zip` shared in the project chat also contains a richer multi-file version, a 20-second MP4, screenshots, and a vector-style KIN app icon. The MP4 has **not** been uploaded by this pull request.

### Preview locally

Open `site/index.html` in a browser, or from repo root:

```bash
python -m http.server 8000
```

Visit http://localhost:8000/site/.

### Publish to GitHub Pages (after merging)

GitHub Pages can publish from a branch/folder but the webpage is under `site/`. For easy deployment, either move the `site/index.html` to repository root or copy it to `docs/index.html`, and in **Settings > Pages > Build and deployment** select the correct source. Alternatively upload the richer ZIP's contents into `docs/` and select `main /docs` in Pages.

Do not replace an existing working application entrypoint. Coordinate deployment choices with the team.

### Safety & branding

KIN stands for **Kinetic Intelligence Network**, tagline **Life changes. KIN moves with you.**

This is an independent hackathon project, not an OU-affiliated product. Color palette is OU-inspired; no official mascot logos or university seals have been copied. Real meteorological data and Gemma inference belong to the separate agent backend, not this scripted landing page. Do not claim these are connected until they actually are.
