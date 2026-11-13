"""Gemini image generation for background plates / prop sprites (cached on disk)."""
import base64
import json
import os
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELS = ["gemini-3-pro-image", "gemini-3-pro-image-preview", "nano-banana-pro-preview",
          "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-2.5-flash-image"]


def generate(prompt, path, aspect="9:16", size="2K", models=None, refs=()):
    if os.path.exists(path):
        return path, "cache"
    parts = [{"text": prompt}]
    for r in refs:
        parts.append({"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(r, "rb").read()).decode()}})
    last = None
    for m in models or MODELS:
        cfg = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}
        if size and "2.5" not in m:
            cfg["imageConfig"]["imageSize"] = size
        body = {"contents": [{"parts": parts}], "generationConfig": cfg}
        for attempt in range(2):
            try:
                req = urllib.request.Request(API.format(model=m), data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
                d = json.load(urllib.request.urlopen(req, timeout=600))
                for p in d["candidates"][0]["content"]["parts"]:
                    if "inlineData" in p:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        open(path, "wb").write(base64.b64decode(p["inlineData"]["data"]))
                        return path, m
                last = f"{m}: no image: {json.dumps(d)[:300]}"
                break
            except urllib.error.HTTPError as e:
                last = f"{m}: {e.code} {e.read().decode()[:200]}"
                if e.code in (429, 400, 404, 403):
                    break
                time.sleep(15)
            except Exception as e:
                last = f"{m}: {e!r}"
                time.sleep(10)
    raise RuntimeError(last)
