"""Voice timeline: stretch line clips, place them on the original 43 s structure,
and time each 1-3 word caption group by snapping to energy dips inside the clip."""
import functools
import json
import os
import re

import numpy as np

from cinecode import tts
from cinecode.align import syllables
from .script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "assets", "audio", "tts_why_awake")
BUILD = os.path.join(ROOT, "build", "why_awake")
SR = tts.SR
TEMPO = 1.12           # medium-fast delivery, fits the original 43 s cut
MIN_GAP = 0.22
END_HOLD = 0.60        # end card hold after the last word
LOOP_TAIL = 0.45       # loop frame (eye + hook) after the end card

# caption groups (1-3 words) per line, '|' separated
GROUPS = {
    "hook": "Why don't you|go to sleep|when you're|dying of|exhaustion?",
    "revenge": "This isn't|insomnia.|It's revenge.",
    "eaten": "Other people|eat up|your whole day.",
    "list": "Work,|school,|traffic,|home.",
    "yours": "When night comes,|the few|hours left|belong only|to you.",
    "brain": "Your brain|doesn't want|to let|them go.|Because|if you sleep,|tomorrow starts|someone else's|day|all over again.",
    "battery": "Plus,|at that hour,|your willpower|is in|the red,|just like|your phone battery.|Because|you spent|all of it|during the day.",
    "steal": "So you steal|hours|from your sleep,|knowing|full well|you'll pay|for it tomorrow.",
    "loop": "Sleep less,|and the|next day|your willpower|drops|even lower.|And you do|the same|thing again.",
    "ending": "So it's not|that you're|not sleepy.|You just|don't want|to give up|the only part|of the day|that's yours.",
    "share": "Send this|to the friend|who says,|“It's 3 a.m.|and I'm|still up.”",
    "follow": "Follow|Just Needy|to learn|how things work.",
}


def _env(clip, hop=240):
    n = len(clip) // hop
    fr = clip[: n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1) + 1e-12) + 1e-9)
    return np.convolve(db, np.ones(3) / 3, mode="same")


def _speech_bounds(db, hop=240):
    thr = np.percentile(db, 95) - 32
    v = np.where(db > thr)[0]
    return v[0] * hop / SR, (v[-1] + 1) * hop / SR


def _syl(txt):
    s = syllables(txt) - 1.5
    if re.search(r"3", txt):
        s += 1
    if "a.m." in txt:
        s += 1
    return max(1.0, s)


def group_times(clip, groups):
    hop = 240
    db = _env(clip)
    s, e = _speech_bounds(db)
    w = np.array([_syl(g) for g in groups])
    # punctuation at the end of a group = short pause after it
    w = w + np.array([0.6 if g[-1] in ",.?!”" else 0 for g in groups])
    cum = np.cumsum(w) / w.sum()
    bounds = [s]
    for k in range(len(groups) - 1):
        guess = s + (e - s) * cum[k]
        lo = max(bounds[-1] + 0.12, guess - 0.22)
        hi = min(e - 0.1, guess + 0.22)
        i0, i1 = int(lo * SR / hop), int(hi * SR / hop)
        if i1 <= i0:
            bounds.append(guess)
            continue
        seg = db[i0:i1]
        # prefer quiet frames near the guess
        dist = np.abs(np.arange(i0, i1) * hop / SR - guess)
        j = int(np.argmin(seg + dist * 18))
        bounds.append((i0 + j) * hop / SR)
    bounds.append(e)
    return [(bounds[k], bounds[k + 1]) for k in range(len(groups))]


def _atempo(x, tempo):
    import subprocess
    a, b = os.path.join(BUILD, "_in.wav"), os.path.join(BUILD, "_out.wav")
    tts.write_wav(a, x)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af", f"atempo={tempo}", "-ar", str(SR), b],
                   check=True)
    return tts.read_wav(b)


def _norm_words(g):
    g = g.replace("3", " three ").replace("a.m.", " a m ")
    g = g.replace("\u201c", "").replace("\u201d", "").replace("\u2019", "'")
    return [w for w in re.sub(r"[^a-z' ]", " ", g.lower()).split() if w]


def align_groups(clip, groups):
    """Forced-align the known text with pocketsphinx; return (start, end) per group."""
    import scipy.signal as sg
    from pocketsphinx import Decoder
    words, owner = [], []
    for gi, g in enumerate(groups):
        for w_ in _norm_words(g):
            words.append(w_)
            owner.append(gi)
    pad = 0.25
    x = np.concatenate([np.zeros(int(pad * SR)), clip, np.zeros(int(pad * SR))])
    x = sg.resample_poly(x, 2, 3)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    segs = None
    for beam in (None, 1e-80, 1e-120):
        kw = {} if beam is None else {"beam": beam, "wbeam": beam, "pbeam": beam}
        d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL", **kw)
        d.set_align_text(" ".join(words))
        d.start_utt()
        d.process_raw(pcm, full_utt=True)
        d.end_utt()
        try:
            segs = [(s.word, s.start_frame / 100 - pad, s.end_frame / 100 - pad) for s in d.seg()]
            break
        except TypeError:
            continue
    if segs is None:
        raise RuntimeError("alignment failed")
    segs = [s for s in segs if not s[0].startswith("<") and s[0] not in ("[NOISE]",)]
    if len(segs) != len(words):
        raise RuntimeError(f"alignment mismatch {len(segs)} vs {len(words)}: {segs}")
    out = []
    for gi in range(len(groups)):
        idx = [i for i, o in enumerate(owner) if o == gi]
        out.append((segs[idx[0]][1], segs[idx[-1]][2]))
    return out


@functools.lru_cache(None)
def build():
    os.makedirs(BUILD, exist_ok=True)
    out = {"lines": [], "caps": []}
    t_prev_end = 0.0
    for key, text, slot, _tr in LINES:
        cache = os.path.join(BUILD, f"st_{key}_{TEMPO}.wav")
        if os.path.exists(cache):
            clip = tts.read_wav(cache)
        else:
            raw = tts.read_wav(os.path.join(D, f"line_{key}.wav"))
            clip = _atempo(raw, TEMPO)
            tts.write_wav(cache, clip)
        groups = GROUPS[key].split("|")
        try:
            gt = align_groups(clip, groups)
        except Exception as ex:  # fall back to energy-dip snapping
            print("align fallback", key, str(ex)[:120])
            gt = group_times(clip, groups)
        # trim to the aligned speech (drops leading/trailing silence of a retake)
        a_ = max(0.0, gt[0][0] - 0.05)
        b_ = min(len(clip) / SR, gt[-1][1] + 0.15)
        clip = clip[int(a_ * SR):int(b_ * SR)]
        tts.write_wav(cache.replace(".wav", "_trim.wav"), clip)
        cache = cache.replace(".wav", "_trim.wav")
        gt = [(x - a_, y - a_) for x, y in gt]
        start = t_prev_end + MIN_GAP if t_prev_end else 0.08
        dur = len(clip) / SR
        out["lines"].append({"key": key, "t0": start, "t1": start + dur, "clip": cache,
                             "words": [(g, start + a, start + b) for g, (a, b) in zip(groups, gt)]})
        for g, (a, b) in zip(groups, gt):
            out["caps"].append({"text": g, "t0": start + a, "t1": start + b, "line": key})
        t_prev_end = start + dur
    # captions persist until the next group starts (no flicker in short gaps)
    caps = out["caps"]
    for i in range(len(caps) - 1):
        nxt = caps[i + 1]["t0"]
        if nxt - caps[i]["t1"] < 0.45:
            caps[i]["t1"] = nxt - 0.02
        else:
            caps[i]["t1"] += 0.25
    out["speech_end"] = t_prev_end
    out["end"] = t_prev_end + END_HOLD + LOOP_TAIL
    return out


def T():
    """Map key -> line dict, plus 'cap(key, i)' helper times."""
    b = build()
    return {l["key"]: l for l in b["lines"]}


def w(key, i):
    """start time of caption group i of a line."""
    return T()[key]["words"][i][1]


if __name__ == "__main__":
    b = build()
    for l in b["lines"]:
        print(f"{l['key']:8s} {l['t0']:6.2f} - {l['t1']:6.2f}")
        for g, a, e in l["words"]:
            print(f"      {a:6.2f} {e:6.2f}  {g}")
    print("end", round(b["end"], 2))
    json.dump(b, open(os.path.join(BUILD, "timing.json"), "w"), indent=1)
