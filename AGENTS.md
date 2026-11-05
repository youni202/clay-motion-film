# Agent guide — make a clay motion film from this repo

You were given this repository's link and asked to make a brand/company intro motion film.
Follow these steps in order. Everything you need is in this repo.

## 0. Setup
```bash
git clone <this repo> && cd clay-motion-film
pip install -r requirements.txt          # numpy, pillow, scipy  (+ ffmpeg on PATH)
npm i playwright                         # only for previews, if not already available
```

## 1. Decide the brief
Company name, and anything the requester wants emphasized (products, history, AI, ESG…).
Pick a lowercase slug, e.g. `atlas-copco-korea`. Ask the requester only if the company is unclear.

## 2. Write `films/<slug>/film.json`
Copy `films/_sample/film.json` and replace every field. Schema: `docs/FILM_SCHEMA.md`.
- Research it yourself with web search (official site, annual report, press releases), **or** run
  `python scripts/plan_film.py "<company>" <slug>` (needs `GEMINI_API_KEY`; Gemini + Google Search).
- Check every year, number and product name against a source. Put the URLs in `sources`.
- No logos, no real people, no unverified claims. Characters are original clay animals.
- Regulated industries (insurance, pharma, finance): keep claims general and note that ads may need review.

## 3. Generate images + music with Gemini
**With an API key** (`export GEMINI_API_KEY=...`, from https://aistudio.google.com/apikey):
```bash
python scripts/gen_assets.py films/<slug>                 # makes assets/<key>.png, hero.png, bgm.mp3
python scripts/gen_assets.py films/<slug> --only owl --force   # redo one image
```
**Without a key** (use the Gemini app in a browser): `python scripts/prompts.py films/<slug>` prints
one prompt per file. Generate each in Gemini, attaching the first character as a style reference for
the others, and save them as `films/<slug>/assets/<key>.png`; make the music with Gemini's music tool
and save it as `assets/bgm.mp3`. White or transparent backgrounds both work.

Look at every image before building: one subject, full body, no text/logos, consistent style.

## 4. Build and check
```bash
python scripts/build.py films/<slug>          # -> dist/<slug>/index.html (single self-contained file)
node scripts/preview.js dist/<slug>/index.html # -> dist/<slug>/shots/NN.jpg, one per scene
```
Open the shots: text must not overflow or overlap, characters must be visible, brand name correct.
Fix `film.json` (shorter copy) or regenerate an image, then rebuild.

## 5. Deliver
- Send/publish `dist/<slug>/index.html` (works offline, music and images embedded; ~2 MB).
- Or commit `films/<slug>/` to `main`: the GitHub Action builds every film and publishes it on GitHub Pages
  at `https://<owner>.github.io/<repo>/<slug>/`.
- Tell the requester which facts came from which sources.

Never commit API keys.
