"""Tiny Gemini API client (stdlib only) for text, image and music generation.

Set GEMINI_API_KEY (get one at https://aistudio.google.com/apikey).
Model ids change over time, so each call tries a list of candidates; override with
GEMINI_TEXT_MODEL / GEMINI_IMAGE_MODEL / GEMINI_MUSIC_MODEL.
"""
import base64, json, os, time, urllib.error, urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
TEXT_MODELS = ["gemini-flash-latest", "gemini-3-flash-preview", "gemini-2.5-flash"]
IMAGE_MODELS = ["gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview", "gemini-2.5-flash-image"]
MUSIC_MODELS = ["lyria-3.5", "lyria-3-pro-preview", "lyria-3-clip-preview"]


class GeminiError(RuntimeError):
    pass


def _key():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k:
        raise GeminiError("GEMINI_API_KEY is not set. Create one at https://aistudio.google.com/apikey")
    return k


def _post(path, body, timeout=600):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": _key()})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:600]
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(8 * (attempt + 1)); continue
            raise GeminiError(f"HTTP {e.code} on {path}: {msg}") from None


def _models(env, defaults):
    v = os.environ.get(env)
    return [v] if v else defaults


def _try(models, fn):
    errors = []
    for m in models:
        try:
            return fn(m), m
        except GeminiError as e:
            errors.append(f"{m}: {e}")
            if "HTTP 404" in str(e) or "not found" in str(e).lower() or "not supported" in str(e).lower():
                continue
            raise
    raise GeminiError("No model worked:\n  " + "\n  ".join(errors))


def text(prompt, search=False):
    """Returns (text, sources[list of {title,url}], model)."""
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if search:
        body["tools"] = [{"google_search": {}}]

    def call(m):
        r = _post(f"/models/{m}:generateContent", body)
        c = (r.get("candidates") or [{}])[0]
        out = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
        if not out:
            raise GeminiError(f"empty response: {json.dumps(r)[:400]}")
        src = [{"title": g["web"].get("title", ""), "url": g["web"]["uri"]}
               for g in c.get("groundingMetadata", {}).get("groundingChunks", []) if "web" in g]
        return out, src

    (out, src), m = _try(_models("GEMINI_TEXT_MODEL", TEXT_MODELS), call)
    return out, src, m


def image(prompt, ref_png=None, aspect="1:1"):
    """Returns (png_bytes, model). ref_png: optional bytes of a style reference image."""
    parts = [{"text": prompt}]
    if ref_png:
        parts.insert(0, {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(ref_png).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}

    def call(m):
        r = _post(f"/models/{m}:generateContent", body)
        for c in r.get("candidates", []):
            for p in c.get("content", {}).get("parts", []):
                d = p.get("inlineData") or p.get("inline_data")
                if d and d.get("data"):
                    return base64.b64decode(d["data"])
        raise GeminiError(f"no image in response: {json.dumps(r)[:400]}")

    return _try(_models("GEMINI_IMAGE_MODEL", IMAGE_MODELS), call)


def _find_audio(obj):
    """Search any response shape for base64 audio."""
    if isinstance(obj, dict):
        mt = (obj.get("mimeType") or obj.get("mime_type") or "")
        if obj.get("type") == "audio" or mt.startswith("audio/"):
            d = obj.get("data")
            if isinstance(d, str) and len(d) > 1000:
                return d
        for v in obj.values():
            f = _find_audio(v)
            if f:
                return f
    elif isinstance(obj, list):
        for v in obj:
            f = _find_audio(v)
            if f:
                return f
    return None


def music(prompt):
    """Returns (mp3_bytes, model). Uses the Interactions API (Lyria), falls back to generateContent."""
    def call(m):
        try:
            r = _post("/interactions", {"model": m, "input": prompt}, timeout=900)
        except GeminiError as e:
            if "HTTP 404" not in str(e):
                raise
            r = _post(f"/models/{m}:generateContent",
                      {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}, timeout=900)
        a = _find_audio(r)
        if not a:
            raise GeminiError(f"no audio in response: {json.dumps(r)[:400]}")
        return base64.b64decode(a)

    return _try(_models("GEMINI_MUSIC_MODEL", MUSIC_MODELS), call)
