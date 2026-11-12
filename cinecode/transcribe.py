"""Gemini transcription (plain text) used for marker alignment and QA.

Tries the dedicated transcribe model first; if it is rate-limited or returns nothing,
falls back to general multimodal models with an explicit verbatim-transcription prompt."""
import base64
import json
import time
import urllib.error
import urllib.request

MODEL = "gemini-3.5-transcribe"
FALLBACKS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.6-flash"]
PROMPT = ("Transcribe this audio verbatim, word for word, in order. It may alternate between a robotic voice "
          "saying 'Number N' and a narrator. Include every 'Number N' marker exactly where it occurs, written "
          "as words or digits. Output only the transcript.")


def _call(model, b, prompt):
    parts = [{"inlineData": {"mimeType": "audio/mp3", "data": b}}]
    if prompt:
        parts.append({"text": prompt})
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps({"contents": [{"parts": parts}]}).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    parts = (d.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("audioTranscription", {}).get("text", "") or p.get("text", "") for p in parts)


def transcribe(mp3_path, retries=2):
    b = base64.b64encode(open(mp3_path, "rb").read()).decode()
    last = None
    for i in range(retries):
        try:
            out = _call(MODEL, b, None)
            if out:
                return out
            last = "empty response"
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode()[:200]}"
        time.sleep(20)
    for rnd in range(3):
        for m in FALLBACKS:
            try:
                out = _call(m, b, PROMPT)
                if out:
                    return out
            except urllib.error.HTTPError as e:
                last = f"{m}: {e.code}"
        time.sleep(60)
    raise RuntimeError(last)
