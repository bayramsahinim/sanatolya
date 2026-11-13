"""Gemini image generation with on-disk caching (used for 3D-look environment plates and prop sprites)."""
import base64
import json
import os
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELS = ["gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-3.1-flash-image-preview",
          "nano-banana-pro-preview", "gemini-3-pro-image-preview", "gemini-nano-banana-2.1",
          "gemini-2.5-flash-image", "gemini-3.1-flash-lite-image"]


def generate(prompt, path, aspect="9:16", size="2K", models=None, refs=()):
    if os.path.exists(path):
        return path
    parts = []
    for r in refs:
        parts.append({"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(r, "rb").read()).decode()}})
    parts.append({"text": prompt})
    last = None
    for m in (models or MODELS):
        cfg = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}
        if size and "2.5" not in m:
            cfg["imageConfig"]["imageSize"] = size
        body = {"contents": [{"parts": parts}], "generationConfig": cfg}
        for attempt in range(2):
            try:
                req = urllib.request.Request(API.format(model=m), data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json", "x-goog-api-key": "d"})
                d = json.load(urllib.request.urlopen(req, timeout=400))
                for p in d["candidates"][0]["content"]["parts"]:
                    if "inlineData" in p:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        open(path, "wb").write(base64.b64decode(p["inlineData"]["data"]))
                        open(path + ".json", "w").write(json.dumps({"model": m, "prompt": prompt}, indent=1))
                        return path
                last = f"{m}: no image " + json.dumps(d)[:200]
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:300].replace("\n", " ")
                last = f"{m}: {e.code} {msg}"
                if e.code == 429 or e.code == 400 or e.code == 404:
                    break
                time.sleep(5)
            except Exception as e:
                last = f"{m}: {e!r}"
                time.sleep(5)
        print("   ", last[:160])
    raise RuntimeError(last)
