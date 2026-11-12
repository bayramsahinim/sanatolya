"""Gemini transcription (plain text) used for marker alignment and QA."""
import base64
import json
import time
import urllib.error
import urllib.request

MODEL = "gemini-3.5-transcribe"


def transcribe(mp3_path, retries=6):
    b = base64.b64encode(open(mp3_path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/mp3", "data": b}}]}]}
    last = None
    for i in range(retries):
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
            return "".join(p.get("audioTranscription", {}).get("text", "") or p.get("text", "")
                           for p in d["candidates"][0]["content"]["parts"])
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode()[:200]}"
            time.sleep(8 * (i + 1))
    raise RuntimeError(last)
