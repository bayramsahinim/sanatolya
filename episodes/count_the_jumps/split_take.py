"""Split the single narration take into per-line clips and verify each by transcription.

usage: python -m episodes.count_the_jumps.split_take [--verify]
writes assets/audio/tts/jumps/lines/<id>.wav and lines.json
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time

from cinecode import align, tts
from cinecode.transcribe import _call
from episodes.count_the_jumps.make_voice import OUT, TAKE_MODELS, take_path
from episodes.count_the_jumps.script import LINES

LINES_DIR = os.path.join(OUT, "lines")


def take_file():
    for m in TAKE_MODELS:
        if os.path.exists(take_path(m)):
            return take_path(m)
    raise FileNotFoundError("run make_voice.make_take() first")


def split(verify=False):
    f = take_file()
    a = tts.read_wav(f)
    segs = align.align(a, [t for _, t in LINES])
    os.makedirs(LINES_DIR, exist_ok=True)
    meta = {}
    for (lid, text), (s, e) in zip(LINES, segs):
        clip = align.trim(a, s, e, pre=0.04, post=0.10)
        tts.write_wav(os.path.join(LINES_DIR, f"{lid}.wav"), clip)
        meta[lid] = {"take": os.path.relpath(f, OUT), "start": round(s, 3), "end": round(e, 3), "text": text}
        if verify:
            with tempfile.TemporaryDirectory() as d:
                w, m = os.path.join(d, "a.wav"), os.path.join(d, "a.mp3")
                tts.write_wav(w, clip)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", w, m], check=True)
                b = base64.b64encode(open(m, "rb").read()).decode()
                heard = None
                for model in ("gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"):
                    try:
                        heard = _call(model, b, "Transcribe verbatim. Output only the transcript.").strip()
                        break
                    except Exception as ex:
                        heard = f"ERR {ex}"
                meta[lid]["heard"] = heard
                print(f"{lid:8s} {e - s:5.2f}s | {heard}", flush=True)
                time.sleep(3)
    json.dump(meta, open(os.path.join(LINES_DIR, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    split("--verify" in sys.argv)
