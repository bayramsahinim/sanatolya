"""Split narration takes into per-line clips -> assets/audio/tts/the_button_en/lines/NN.wav + lines.json"""
import json
import os

from cinecode import align as A
from cinecode import tts
from episodes.the_button_en.make_voice import OUT, TAKES, take_path
from episodes.the_button_en.script import LINES


# Hand-checked boundaries where the automatic split was wrong (verified by re-transcribing each clip).
OVERRIDE = {
    3: [(0.0, 2.48), (3.04, 5.23), (5.34, 6.92), (7.74, 9.43), (10.18, 11.7), (12.05, 14.38), (15.1, 23.96)],
}


def main():
    os.makedirs(os.path.join(OUT, "lines"), exist_ok=True)
    meta = {}
    for i, idx in enumerate(TAKES):
        audio = tts.read_wav(take_path(i))
        segs = OVERRIDE.get(i) or A.align(audio, [LINES[k][1] for k in idx])
        for k, (s, e) in zip(idx, segs):
            clip = A.trim(audio, s, e)
            p = os.path.join(OUT, "lines", f"{k:02d}.wav")
            tts.write_wav(p, clip)
            meta[k] = {"take": i, "start": round(s, 3), "end": round(e, 3), "dur": round(len(clip) / tts.SR, 3)}
            print(f"{k:2d} {len(clip) / tts.SR:5.2f}s  {LINES[k][1]}")
    json.dump(meta, open(os.path.join(OUT, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
