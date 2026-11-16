"""Report voiced span per take and transcribe it (verifies the TTS said exactly the line)."""
import os, subprocess, sys, tempfile
import numpy as np
from cinecode import tts
from cinecode.align import envelope_db
from cinecode.transcribe import _call
from episodes.count_the_jumps.make_voice import path
from episodes.count_the_jumps.script import LINES
import base64, time


def voiced(a):
    db = envelope_db(a)
    thr = np.percentile(db, 95) - 35
    v = np.where(db > thr)[0]
    return v[0] * 0.01, (v[-1] + 1) * 0.01


if __name__ == "__main__":
    only = sys.argv[1:]
    for lid, text in LINES:
        if only and lid not in only:
            continue
        p = path(lid, text)
        a = tts.read_wav(p)
        s, e = voiced(a)
        with tempfile.TemporaryDirectory() as d:
            w = os.path.join(d, "a.wav"); m = os.path.join(d, "a.mp3")
            tts.write_wav(w, a[int(s * 24000):int(e * 24000)])
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", w, m], check=True)
            b = base64.b64encode(open(m, "rb").read()).decode()
            try:
                tr = _call("gemini-3.6-flash", b, "Transcribe verbatim. Output only the transcript.").strip()
            except Exception as ex:
                tr = f"ERR {ex}"
        time.sleep(4)
        print(f"{lid:9s} total {len(a)/24000:5.2f}  voiced {s:5.2f}-{e:5.2f} ({e-s:4.2f}s) | {tr}")
