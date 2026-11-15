"""Gemini image generation for static textures/backdrops (cached on disk; files are committed)."""
import base64
import json
import os
import time
import urllib.error
import urllib.request

MODELS = ["gemini-3-pro-image", "gemini-3.1-flash-image", "gemini-2.5-flash-image"]


def generate(prompt, path, aspect="1:1", models=MODELS):
    if os.path.exists(path):
        return path
    last = None
    for m in models:
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
            for p in d["candidates"][0]["content"]["parts"]:
                if "inlineData" in p:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    open(path, "wb").write(base64.b64decode(p["inlineData"]["data"]))
                    return path
            last = f"{m}: no image"
        except urllib.error.HTTPError as e:
            last = f"{m}: {e.code} {e.read().decode()[:200]}"
        except Exception as e:
            last = f"{m}: {e!r}"
        time.sleep(2)
    raise RuntimeError(last)
