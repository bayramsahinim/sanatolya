"""Audio, SRT and final render for the source-picture version.

Sound: the ORIGINAL soundtrack with its Turkish narration removed (Demucs two-stem separation, the
"no_vocals" stem: the source's own music and effects, in sync with the source picture), plus the English
narration on top (ducked bed). The guards' laughs, which separation files under "vocals", are restored with
the channel's laugh effect at the source's laugh moments.

usage: python -m episodes.dry_peas_escape.vfx.finish audio|video|all [--draft]
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode import tts
from cinecode.align import trim
from episodes.dry_peas_escape import sound  # noqa: F401  (registers laugh_big etc.)
from episodes.dry_peas_escape.timing import (CLIP_POST, CLIP_PRE, LINES_JSON, SCHED, TEMPO, TEMPO_LINE, TOTAL)
from episodes.dry_peas_escape.vfx import compose

ROOT = compose.ROOT
WORK = compose.WORK
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_PRISON_ESCAPE_VISUAL_FIXED"
STEM = os.path.join(WORK, "source_no_vocals.wav")
LAUGHS = [(3.45, "laugh", 0.55), (22.75, "laugh_big", 0.6), (32.6, "laugh", 0.4)]


def clips():
    cache = os.path.join(WORK, "clips")
    os.makedirs(cache, exist_ok=True)
    meta = json.load(open(LINES_JSON))
    takes, out = {}, {}
    for lid, v in meta.items():
        tempo = TEMPO_LINE.get(lid, TEMPO)
        p = os.path.join(cache, f"{lid}_{tempo}_{v['start']}_{v['end']}.npy")
        if os.path.exists(p):
            out[lid] = np.load(p)
            continue
        f = os.path.join(ROOT, v["file"])
        takes.setdefault(f, tts.read_wav(f))
        raw = trim(takes[f], v["start"], v["end"], CLIP_PRE, CLIP_POST)
        a, b = os.path.join(cache, "in.wav"), os.path.join(cache, "out.wav")
        tts.write_wav(a, raw)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality,aresample=48000", "-ac", "1", b],
                       check=True)
        y, sr = sf.read(b)
        out[lid] = y.astype(np.float32)
        np.save(p, out[lid])
    return out


def mix():
    n = int(TOTAL * A.SR) + A.SR
    voice = np.zeros(n)
    for lid, x in clips().items():
        v = x[np.abs(x) > 0.02]
        x = x * (0.16 / (np.sqrt((v ** 2).mean()) + 1e-9))
        A.add(voice, x, SCHED[lid][0])
    bed, sr = sf.read(STEM)
    if bed.ndim > 1:
        bed = bed.mean(axis=1)
    if sr != A.SR:
        bed = A.resample(bed, sr, A.SR)
    stem = np.zeros(n)
    A.add(stem, bed, 0.0)
    # level the source's music/effects bed to sit ~15 dB under the narration
    v_rms = np.sqrt((voice[np.abs(voice) > 0.01] ** 2).mean())
    b_rms = np.sqrt((stem[: int(68 * A.SR)] ** 2).mean()) + 1e-9
    stem *= (v_rms * 10 ** (-15 / 20)) / b_rms
    fx = np.zeros(n)
    for t, name, vol in LAUGHS:
        A.add(fx, A.get_sfx(name) * vol, t)
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.45 * np.clip(env / 0.08, 0, 1)
    voice = A.hp(voice, 90) + A.bp(voice, 2500, 5000) * 0.12
    total = voice + stem * duck + fx * 10 ** (-13 / 20) * duck
    e = np.ones(n)
    k0, k1 = int((TOTAL - 0.6) * A.SR), int(TOTAL * A.SR)
    e[k0:k1] = np.linspace(1, 0.0, k1 - k0)
    e[k1:] = 0
    total = np.tanh(total * e * 0.95) / 0.95
    raw = os.path.join(WORK, "mix_raw.wav")
    sf.write(raw, total[: int(TOTAL * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    sf.write(os.path.join(WORK, "stem_voice.wav"), voice[: int(TOTAL * A.SR)].astype(np.float32), A.SR)
    sf.write(os.path.join(WORK, "stem_bed.wav"), (stem * duck)[: int(TOTAL * A.SR)].astype(np.float32), A.SR)
    return out


def write_srt(path):
    from episodes.dry_peas_escape.episode import _wrap, fmt
    out = []
    for i, c in enumerate(compose.chunks()):
        out.append(f"{i + 1}\n{fmt(c['t0'])} --> {fmt(c['t1'])}\n{_wrap(c['text'], compose.SUB_SIZE)}\n")
    open(path, "w").write("\n".join(out))
    return path


def video(draft=False):
    nf = int(round(TOTAL * compose.FPS))
    silent = os.path.join(WORK, "video_silent.mp4")
    compose.render(nf, silent, draft=draft)
    final = os.path.join(OUT if not draft else WORK, (NAME if not draft else "draft") + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", os.path.join(WORK, "mix.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-ac", "2", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    "-metadata", "title=The Prisoner Who Escaped With Dry Peas", final], check=True)
    print("wrote", final)
    return final


if __name__ == "__main__":
    cmd = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    if cmd in ("audio", "all"):
        print(mix())
        print(write_srt(os.path.join(OUT, NAME + "_ENGLISH.srt")))
    if cmd in ("video", "all"):
        video("--draft" in sys.argv)
