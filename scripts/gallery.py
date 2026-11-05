#!/usr/bin/env python3
"""Write dist/index.html listing every built film (for GitHub Pages)."""
import html, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dist = os.path.join(ROOT, "dist"); os.makedirs(dist, exist_ok=True)
cards = []
for slug in sorted(os.listdir(dist)):
    fj = os.path.join(dist, slug, "film.json")
    if slug.startswith("_") or not os.path.exists(fj):
        continue
    f = json.load(open(fj, encoding="utf-8"))
    cards.append(f'<a class="c" href="{html.escape(slug)}/"><b>{html.escape(f.get("brand", slug))}</b><span>{html.escape(f.get("title", ""))}</span></a>')
open(os.path.join(dist, "index.html"), "w", encoding="utf-8").write(f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Clay Motion Films</title><style>
:root{{--bg:#f4f7fb;--fg:#0b1d36;--card:#fff;--sub:#4b5d78}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1220;--fg:#e8eefb;--card:#16203a;--sub:#9fb0cf}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,"Apple SD Gothic Neo",sans-serif;padding:40px 16px}}
h1{{max-width:960px;margin:0 auto 24px;font-size:32px}}.g{{max-width:960px;margin:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}}
.c{{display:block;padding:22px;border-radius:18px;background:var(--card);color:inherit;text-decoration:none;box-shadow:0 6px 24px rgba(0,0,0,.06)}}.c b{{display:block;font-size:20px}}.c span{{color:var(--sub)}}
</style><h1>Clay Motion Films</h1><div class=g>{''.join(cards) or '<p>아직 만든 필름이 없어요.</p>'}</div>""")
print(f"✓ dist/index.html ({len(cards)} films)")
