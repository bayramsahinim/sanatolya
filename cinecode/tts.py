"""Gemini TTS client with on-disk caching (cache files are committed to the repo,
so re-rendering an episode never spends API quota)."""
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

import numpy as np

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
SR = 24000


def _post(model, body, timeout=600):
    req = urllib.request.Request(
        API.format(model=model),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 # proxy injects the real key
                 "x-goog-api-key": os.environ.get("GEMINI_API_KEY", "dummy")})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _pcm_from_response(d):
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            raw = base64.b64decode(p["inlineData"]["data"])
            return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    raise RuntimeError("no audio in response: %s" % json.dumps(d)[:500])


def synth(text, cache_path, model, voice=None, speakers=None, retries=4):
    """Return float32 mono @24k. `speakers` = {name: voice} for multi-speaker."""
    if os.path.exists(cache_path):
        return read_wav(cache_path)
    if speakers:
        speech = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": n, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": v}}}
            for n, v in speakers.items()]}}
    else:
        speech = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": speech}}
    last = None
    for i in range(retries):
        try:
            audio = _pcm_from_response(_post(model, body))
            write_wav(cache_path, audio)
            return audio
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:600]
            last = f"{e.code}: {msg}"
            if e.code == 429 and "per day" in msg and "per minute" not in msg:
                raise RuntimeError("daily quota exhausted: " + msg)
            time.sleep(35 * (i + 1))
        except Exception as e:  # network hiccup / bad payload
            last = repr(e)
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"TTS failed after {retries} tries: {last}")


def write_wav(path, audio, sr=SR):
    import wave
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def read_wav(path):
    import wave
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        ch = w.getnchannels()
        data = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data


def text_hash(*parts):
    return hashlib.sha1("\n".join(parts).encode()).hexdigest()[:10]
