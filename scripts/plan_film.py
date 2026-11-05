#!/usr/bin/env python3
"""Research a company with Gemini (Google Search grounding) and draft films/<slug>/film.json.

Usage:
  python scripts/plan_film.py "아트라스콥코 코리아" [slug] [--notes "강조할 점"]

Always review the draft: check every year, number and product name against the sources it lists.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemini

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = """You plan a ~50 second Korean brand intro motion film made of clay-3D animal characters.
Research the company with Google Search, using official sources first (company site, annual report, press releases).
Return ONLY one JSON object in a ```json code block, following exactly the structure of the EXAMPLE below.

Rules:
- All on-screen copy in natural Korean, short and punchy. English only for `brand`, scene `name` (ONE short uppercase word, max 10 letters), `cat`, tags may mix.
- `since` = founding year (or year the company entered Korea if the film is about the Korean entity — say which in intro.sub).
- history.items: 6–8 milestones [year, short Korean label (max 14 chars), optional 1 to highlight]. Only facts you found.
- scenes: 4–5 business areas / strengths. `tip` = one or two factual sentences (max 70 Korean chars) with a concrete number or name when available.
- characters: one key per animal (lowercase english), described in English: which animal, outfit in brand colors, holding/doing something that shows the scene. Add a `guide` character (company mascot-like expert) used for history and products. Each scene's `img` must be one of the character keys. Never draw real people, logos or text.
- palette: derive from the brand colors (primary, deep, light, accent, stage=very light background). Scene `bg`/`blob` light tints, `ac` a readable darker accent.
- products.groups: 3–4 groups, 7–12 items total, real product or brand names, caption max 10 Korean chars.
- hero: one object that symbolizes the company (for the intro).
- music.prompt: English, instrumental mood that fits the brand. No company names in the music prompt.
- Do not invent facts. If unsure, leave it out.
"""


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "film"


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    notes = ""
    if "--notes" in a:
        i = a.index("--notes"); notes = a[i + 1]; del a[i:i + 2]
    company = a[0]
    example = open(os.path.join(ROOT, "films", "_sample", "film.json"), encoding="utf-8").read()
    prompt = f"{RULES}\nCompany: {company}\nExtra notes from the requester: {notes or '-'}\n\nEXAMPLE:\n```json\n{example}\n```"
    out, sources, model = gemini.text(prompt, search=True)
    m = re.search(r"```json\s*(\{.*\})\s*```", out, re.S) or re.search(r"(\{.*\})", out, re.S)
    if not m:
        sys.exit("Could not find JSON in the model output:\n" + out[:2000])
    f = json.loads(m.group(1))
    slug = a[1] if len(a) > 1 else (f.get("slug") if f.get("slug") not in (None, "", "_sample") else slugify(f.get("brand", company)))
    f["slug"] = slug
    f["sources"] = sources or f.get("sources", [])
    f.setdefault("timing", {"intro": 4, "history": 6, "scene": 5.5, "products": 8.5, "finale": 8})
    d = os.path.join(ROOT, "films", slug); os.makedirs(d, exist_ok=True)
    json.dump(f, open(os.path.join(d, "film.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✓ films/{slug}/film.json  (model {model}, {len(f['sources'])} sources)")
    print("  review the facts, then: python scripts/gen_assets.py films/" + slug)


if __name__ == "__main__":
    main()
