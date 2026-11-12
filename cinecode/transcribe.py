"""Gemini transcription (plain text) used for marker alignment and QA."""
import base64
import json
import time
import urllib.error
import urllib.request

MODEL = "gemini-3.5-transcribe"


def transcribe(mp3_path, retries=10):
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
            parts = (d.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            out = "".join(p.get("audioTranscription", {}).get("text", "") or p.get("text", "") for p in parts)
            if out:
                return out
            last = "empty response"
            time.sleep(30)
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode()[:200]}"
            time.sleep(65 if e.code == 429 else 10 * (i + 1))
    raise RuntimeError(last)
