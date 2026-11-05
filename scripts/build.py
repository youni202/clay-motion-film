#!/usr/bin/env python3
"""Build a self-contained motion film HTML from films/<slug>/film.json + assets.

Usage:
  python scripts/build.py films/<slug>            # -> dist/<slug>/index.html (+ light copy)

Expects in films/<slug>/:
  film.json
  assets/<name>.png   one per character key + hero.png (transparent or white background)
  assets/bgm.mp3      background music (any length; trimmed to the film length)
"""
import base64, io, json, os, re, shutil, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clean(im: Image.Image) -> Image.Image:
    """Make the background transparent and crop to the subject.

    Works for real transparent PNGs and for flat white/near-white backgrounds:
    any background-coloured region touching the border is removed.
    """
    a = np.array(im.convert("RGBA")).astype(np.int16)
    rgb, al = a[..., :3], a[..., 3]
    if (al < 250).mean() < 0.05:  # no real alpha -> key out the border colour
        corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
                                  rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
        bg = np.median(corners, axis=0)
        bgmask = np.abs(rgb - bg).max(axis=2) < 26
    else:
        bgmask = al < 120
    lab, _ = ndimage.label(bgmask)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    kill = np.isin(lab, list(border))
    soft = ndimage.binary_dilation(kill, iterations=2) & ~kill  # feather the edge a little
    out = a.copy()
    out[..., 3] = np.where(kill, 0, np.where(soft, np.minimum(al, 140), al))
    o = Image.fromarray(out.astype(np.uint8))
    box = o.split()[3].point(lambda v: 255 if v > 20 else 0).getbbox()
    return o.crop(box) if box else o


def film_length(f):
    d = f.get("timing", {})
    return (d.get("intro", 4) + d.get("history", 6) + len(f["scenes"]) * d.get("scene", 5.5)
            + d.get("products", 8.5) + d.get("finale", 8))


def prepare_audio(src, seconds, outdir):
    """Trim to the film length with a fade-out, then encode opus + aac."""
    fade = 2.5
    af = f"afade=t=in:d=0.4,afade=t=out:st={max(0, seconds - fade):.2f}:d={fade}"
    trimmed = os.path.join(outdir, "bgm.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{seconds:.2f}", "-af", af,
                    "-c:a", "libmp3lame", "-b:a", "160k", trimmed], check=True)
    webm, m4a = os.path.join(outdir, "_bgm.webm"), os.path.join(outdir, "_bgm.m4a")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", trimmed, "-c:a", "libopus", "-b:a", "64k", webm], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", trimmed, "-c:a", "aac", "-b:a", "96k", m4a], check=True)
    b = lambda p: base64.b64encode(open(p, "rb").read()).decode()
    tag = ('<source src="data:audio/webm;base64,%s" type="audio/webm; codecs=opus">'
           '<source src="data:audio/mp4;base64,%s" type="audio/mp4">') % (b(webm), b(m4a))
    os.remove(webm); os.remove(m4a)
    return tag


def main(film_dir):
    film_dir = film_dir.rstrip("/")
    f = json.load(open(os.path.join(film_dir, "film.json"), encoding="utf-8"))
    slug = f.get("slug") or os.path.basename(film_dir)
    out = os.path.join(ROOT, "dist", slug)
    os.makedirs(os.path.join(out, "img"), exist_ok=True)
    adir = os.path.join(film_dir, "assets")

    names = list(f.get("characters", {}).keys()) + (["hero"] if f.get("hero") else [])
    embedded, linked = {}, {}
    for n in names:
        p = os.path.join(adir, n + ".png")
        if not os.path.exists(p):
            print(f"  ! missing asset {p} — scene will render without it")
            continue
        im = clean(Image.open(p))
        im.save(os.path.join(out, "img", n + ".png"))
        t = im.copy(); t.thumbnail((620, 720), Image.LANCZOS)
        buf = io.BytesIO(); t.save(buf, "WEBP", quality=82, method=6)
        embedded[n] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
        linked[n] = "img/" + n + ".png"

    secs = film_length(f)
    bgm = os.path.join(adir, "bgm.mp3")
    audio_embedded = audio_linked = ""
    if os.path.exists(bgm):
        audio_embedded = prepare_audio(bgm, secs, out)
        audio_linked = '<source src="bgm.mp3" type="audio/mpeg">'
    else:
        print("  ! no assets/bgm.mp3 — film will be silent")

    tpl = open(os.path.join(ROOT, "engine", "template.html"), encoding="utf-8").read()
    film_js = json.dumps(f, ensure_ascii=False).replace("</", "<\\/")
    title = re.sub(r"[<>]", "", f.get("title") or f["brand"])

    def render(imgs, audio):
        return (tpl.replace("__TITLE__", title).replace("__FILM__", film_js)
                .replace("__IMGS__", json.dumps(imgs)).replace("__AUDIO__", audio))

    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(render(embedded, audio_embedded))
    open(os.path.join(out, "light.html"), "w", encoding="utf-8").write(render(linked, audio_linked))
    shutil.copy(os.path.join(film_dir, "film.json"), os.path.join(out, "film.json"))
    size = os.path.getsize(os.path.join(out, "index.html")) / 1e6
    print(f"✓ dist/{slug}/index.html  ({size:.1f} MB, {secs:.1f}s, {len(embedded)} images)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
