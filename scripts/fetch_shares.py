#!/usr/bin/env python3
"""Download Gemini-generated assets from public Gemini share links.

films/<slug>/assets/shares.json:
  {"guide": "https://share.gemini.google/XXXX", ..., "bgm": "https://share.gemini.google/YYYY"}

Images are saved as <key>.png, the key "bgm" as bgm.mp3. Used by the GitHub Action when
files can't be downloaded from the Gemini app directly.
"""
import html, io, json, os, re, sys, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
      "Accept-Language": "ko,en;q=0.8"}


def get(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    return urllib.request.urlopen(req, timeout=60)


def candidates(page):
    page = page.replace("\\u002F", "/").replace("\\/", "/").replace("\\u003d", "=").replace("\\u0026", "&")
    page = html.unescape(page)
    urls = set(re.findall(r'https://[A-Za-z0-9.\-]+\.(?:googleusercontent|gstatic|ggpht)\.com/[^\s"\'<>\\)]+', page))
    og = re.findall(r'<meta[^>]+property="og:(?:image|audio|video)(?::url)?"[^>]+content="([^"]+)"', page)
    return og, sorted(urls)


def fetch_image(urls):
    from PIL import Image
    best = None
    for u in urls:
        for v in (re.sub(r"=[a-zA-Z0-9\-_]+$", "", u) + "=s0", u):
            try:
                data = get(v).read()
                im = Image.open(io.BytesIO(data))
                score = im.size[0] * im.size[1]
                if best is None or score > best[0]:
                    best = (score, data, v[:60])
                break
            except Exception:
                continue
    return best


def fetch_audio(urls):
    best = None
    for u in urls:
        for v in (u, re.sub(r"=[a-zA-Z0-9\-_]+$", "", u)):
            try:
                r = get(v)
                ct = r.headers.get("Content-Type", "")
                if not (ct.startswith("audio/") or ct.startswith("video/") or "mpeg" in ct):
                    continue
                data = r.read()
                if best is None or len(data) > len(best[0]):
                    best = (data, ct, v[:60])
                break
            except Exception:
                continue
    return best


def main(film_dir):
    adir = os.path.join(film_dir, "assets")
    shares = json.load(open(os.path.join(adir, "shares.json")))
    ok = True
    for key, link in shares.items():
        page = get(link).read().decode("utf-8", "replace")
        og, urls = candidates(page)
        ordered = og + [u for u in urls if u not in og]
        print(f"{key}: {len(og)} og, {len(urls)} candidate urls")
        if key == "bgm":
            got = fetch_audio(ordered)
            if got:
                open(os.path.join(adir, "bgm.mp3"), "wb").write(got[0])
                print(f"  ✓ bgm.mp3 {len(got[0])} bytes {got[1]} from {got[2]}…")
            else:
                ok = False
                print("  ✗ no audio found; candidates:", [u[:70] for u in ordered[:12]])
        else:
            got = fetch_image(ordered)
            if got:
                open(os.path.join(adir, key + ".png"), "wb").write(got[1])
                print(f"  ✓ {key}.png {got[0]} px² from {got[2]}…")
            else:
                ok = False
                print("  ✗ no image found; candidates:", [u[:70] for u in ordered[:12]])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1])
