# 🎬 Clay Motion Film

**▶ 만든 필름 보기: https://youni202.github.io/clay-motion-film/**  (현대지성 · GEA 코리아 · 아트라스콥코 코리아 · 한국마이크로소프트 · BNP파리바 카디프생명 · 옵투스제약 · 보령 · F&F)

Turn a company's information into a **1-minute intro motion film with clay 3D characters**.
**Gemini** generates the images and music; an HTML motion engine assembles them into a single file you can play anywhere.

```
회사 정보 ──▶ film.json ──▶ Gemini (characters·hero image + Lyria music) ──▶ build ──▶ index.html (single file) / GitHub Pages
```

## 3 ways to make one

### 1) Give an AI agent just the link
Tell Claude (or another coding agent):
> "Make a motion film for <company> with https://github.com/youni202/clay-motion-film"

The agent follows [`AGENTS.md`](AGENTS.md): research → film.json → Gemini generation → build → screen check → delivery.

### 2) One button in GitHub Actions
1. Fork (or copy) this repo
2. **Settings → Secrets → Actions** → add `GEMINI_API_KEY` ([get one](https://aistudio.google.com/apikey))
3. **Settings → Pages → Source: GitHub Actions**
4. **Actions → 🎬 Make film → Run workflow** → enter a company name and slug

When it finishes, the film plays at `https://<id>.github.io/<repo>/<slug>/`.
The facts are drafted by Gemini with Google Search, so it's safer to run it the first time with **"stop_after_plan"** checked, review `films/<slug>/film.json`, then run again.

### 3) Locally
```bash
pip install -r requirements.txt            # requires ffmpeg
export GEMINI_API_KEY=...
python scripts/plan_film.py "아트라스콥코 코리아" atlas-copco-korea   # research + draft plan
python scripts/gen_assets.py films/atlas-copco-korea                   # Gemini images + music
python scripts/build.py films/atlas-copco-korea                        # → dist/atlas-copco-korea/index.html
node scripts/preview.js dist/atlas-copco-korea/index.html              # per-scene screenshots (Playwright)
```
No API key? `python scripts/prompts.py films/<slug>` prints prompts you can paste straight into the Gemini app.
Save the results in `films/<slug>/assets/` and run `build.py`.

## Film structure (~50 seconds, adjustable)
| Scene | Content |
|---|---|
| Intro | Hero object + year counting up + characters peek in |
| 01 History | Timeline of 6–8 milestones |
| 02–06 Strengths | One clay character per business area, with headline, typed explanation, hashtags |
| Lineup | Products/brands as boxes, grouped |
| Finale | All characters + closing line |

You can change the copy, colors, characters, music mood and timing in `film.json` → [field reference](docs/FILM_SCHEMA.md)

## Folders
```
engine/template.html   motion engine (1920×1080 stage, responsive scaling)
scripts/               plan_film · gen_assets · build · preview · prompts · gallery · gemini (API client)
films/<slug>/          film.json + assets/ (png, bgm.mp3)  ← one folder per film
films/_sample/         fictional company example
dist/                  build output (not committed, deployed to Pages)
```

## Notes
- Model names change, so `scripts/gemini.py` tries several candidates in order. You can pin one with the `GEMINI_IMAGE_MODEL`, `GEMINI_MUSIC_MODEL` and `GEMINI_TEXT_MODEL` environment variables.
- Gemini API image and music generation is billed. Roughly 7 images plus 1 track per film.
- Company logos and trademarks are **not generated**. The brand name is displayed as text only. To use an official logo, follow the company's brand guidelines.
- Make sure the facts in the film (years, figures, product names) match the `sources`. For insurance, pharma, finance and other industries where ads are reviewed, check before public use.
