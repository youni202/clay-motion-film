#!/usr/bin/env python3
"""Generate characters, hero object and background music for a film with Gemini.

Usage:
  python scripts/gen_assets.py films/<slug>            # generate whatever is missing
  python scripts/gen_assets.py films/<slug> --force    # regenerate everything
  python scripts/gen_assets.py films/<slug> --only owl,bgm

Reads film.json -> writes films/<slug>/assets/<key>.png and assets/bgm.mp3
"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemini
from build import film_length

STYLE = ("Soft clay 3D figure style, like a cute designer art toy: big head, glossy sparkling eyes, "
         "rounded plush shapes, gentle pastel studio lighting, no cast shadow. "
         "Exactly one subject, centered, full body visible with margin on every side. "
         "Plain solid pure white background (#FFFFFF), no floor, no scenery, no frame. "
         "Absolutely no text, letters, numbers, logos or watermarks anywhere.")


def char_prompt(f, key, desc, is_ref):
    pal = f.get("palette", {})
    tone = f.get("art_direction", "")
    colors = ", ".join(v for k, v in pal.items() if k in ("primary", "deep", "accent"))
    p = f"{STYLE} Color accents: {colors}. {tone} Subject: {desc}"
    if is_ref:
        p = ("Use the attached image only as the style reference (same clay material, rendering, lighting "
             "and proportions) and create a NEW, different character. " + p)
    return p


def music_prompt(f):
    secs = int(round(film_length(f))) + 4
    m = f.get("music", {})
    base = m.get("prompt") or "Bright, warm, uplifting corporate brand film background music."
    return (f"{base} Instrumental only, no vocals, no lyrics. Total length about {secs} seconds. "
            f"Structure: [0:00-0:06] light intro, [0:06-0:{min(59, secs - 12):02d}] steady main groove that slowly builds, "
            f"final 10 seconds a confident, satisfying ending that resolves cleanly (no fade-out needed). "
            f"Tempo around {m.get('bpm', 110)} BPM.")


def loop_to(src, dst, seconds):
    """For short clip models: loop with a crossfade until long enough."""
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                             capture_output=True, text=True).stdout or 0)
    if d >= seconds or d <= 0:
        os.replace(src, dst); return
    n = int(seconds // (d - 2)) + 1
    inputs = sum([["-i", src] for _ in range(n)], [])
    chain, last = [], "[0:a]"
    for i in range(1, n):
        out = f"[x{i}]"; chain.append(f"{last}[{i}:a]acrossfade=d=2{out}"); last = out
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", last, "-c:a", "libmp3lame", "-b:a", "160k", dst], check=True)
    os.remove(src)


def main(film_dir, force=False, only=None):
    f = json.load(open(os.path.join(film_dir, "film.json"), encoding="utf-8"))
    adir = os.path.join(film_dir, "assets"); os.makedirs(adir, exist_ok=True)
    want = lambda k: (only is None or k in only)
    chars = f.get("characters", {})
    keys = list(chars)
    ref = None
    for i, k in enumerate(keys):
        p = os.path.join(adir, k + ".png")
        if os.path.exists(p) and not force:
            ref = ref or open(p, "rb").read(); continue
        if not want(k):
            continue
        print(f"→ image {k} …", flush=True)
        png, m = gemini.image(char_prompt(f, k, chars[k], ref is not None), ref_png=ref)
        open(p, "wb").write(png); print(f"  ✓ {p} ({m})")
        ref = ref or png  # first character becomes the style reference for the cast
    if f.get("hero") and want("hero"):
        p = os.path.join(adir, "hero.png")
        if force or not os.path.exists(p):
            print("→ image hero …", flush=True)
            png, m = gemini.image(f"{STYLE} Subject: {f['hero']} (an object, no character).", ref_png=ref)
            open(p, "wb").write(png); print(f"  ✓ {p} ({m})")
    p = os.path.join(adir, "bgm.mp3")
    if want("bgm") and (force or not os.path.exists(p)):
        print("→ music …", flush=True)
        audio, m = gemini.music(music_prompt(f))
        tmp = tempfile.mktemp(suffix=".audio", dir=adir); open(tmp, "wb").write(audio)
        loop_to(tmp, p, film_length(f) + 1)
        print(f"  ✓ {p} ({m})")
    print("done. next: python scripts/build.py", film_dir)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    only = None
    if "--only" in a:
        only = set(a[a.index("--only") + 1].split(","))
    main(a[0], force="--force" in a, only=only)
