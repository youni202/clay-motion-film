#!/usr/bin/env python3
"""Print the exact Gemini prompts for a film, for use in the Gemini app when you have no API key.

Usage: python scripts/prompts.py films/<slug>
Save each result as films/<slug>/assets/<key>.png (and the track as assets/bgm.mp3).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_assets import STYLE, char_prompt, music_prompt

d = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
f = json.load(open(os.path.join(d, "film.json"), encoding="utf-8"))
for i, (k, desc) in enumerate(f.get("characters", {}).items()):
    print(f"\n### {k}.png  (attach the first character as a style reference after the first one)\n" + char_prompt(f, k, desc, i > 0))
if f.get("hero"):
    print(f"\n### hero.png\n{STYLE} Subject: {f['hero']} (an object, no character).")
print("\n### bgm.mp3  (Gemini app: 음악 만들기)\n" + music_prompt(f))
