"""Record the narration as one take (consistent voice), then split it into lines."""
import json
import os

from cinecode import tts
from cinecode.align import align, trim
from .script import LINES, VOICE

D = "assets/audio/tts_why_awake"


def main():
    os.makedirs(D, exist_ok=True)
    texts = [l[1] for l in LINES]
    body = "\n\n".join(texts)
    prompt = VOICE["notes"] + "\n\nTranscript:\n" + body
    h = tts.text_hash(prompt, VOICE["voice"])
    audio = None
    for m in [VOICE["model"]] + VOICE["fallback_models"]:
        try:
            audio = tts.synth(prompt, f"{D}/take_{h}.wav", m, voice=VOICE["voice"])
            print("model", m)
            break
        except Exception as e:
            print(m, "failed:", str(e)[:200])
    if audio is None:
        raise SystemExit("no TTS")
    print("take length %.2fs" % (len(audio) / tts.SR))
    segs = align(audio, texts)
    out = {}
    for (key, *_), (s, e) in zip(LINES, segs):
        clip = trim(audio, s, e)
        tts.write_wav(f"{D}/line_{key}.wav", clip)
        out[key] = round(len(clip) / tts.SR, 3)
        print(f"{key:8s} {out[key]:.2f}s")
    json.dump(out, open(f"{D}/lines.json", "w"), indent=1)




def retake(key):
    """Re-record a single line with the same voice + direction (used for 'yours')."""
    text = dict((l[0], l[1]) for l in LINES)[key]
    prompt = VOICE["notes"] + "\n\nTranscript:\n" + text
    h = tts.text_hash(prompt, VOICE["voice"])
    audio = tts.synth(prompt, f"{D}/retake_{key}_{h}.wav", VOICE["model"], voice=VOICE["voice"])
    from cinecode.align import envelope_db
    db = envelope_db(audio)
    import numpy as np
    v = np.where(db > np.percentile(db, 95) - 38)[0]
    clip = trim(audio, v[0] * 240 / tts.SR, (v[-1] + 1) * 240 / tts.SR)
    tts.write_wav(f"{D}/line_{key}.wav", clip)
    print(key, len(clip) / tts.SR)


if __name__ == "__main__":
    import sys
    retake(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "retake" else main()
