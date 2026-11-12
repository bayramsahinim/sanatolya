"""Per-line narration clips for Day 2: split the two cached takes at their pauses.
Without takes (TTS quota), durations are estimated so picture work can go on."""
import functools

import numpy as np

from cinecode import align
from cinecode.audio import SR as MIX_SR
from cinecode.audio import resample
from cinecode.tts import SR as TTS_SR
from cinecode.tts import read_wav
from episodes.zombie_day_2 import make_voice
from episodes.zombie_day_2.script import LINES, TEXT


def estimate(lid):
    return align.syllables(TEXT[lid]) * 0.19 + 0.2


@functools.lru_cache(maxsize=None)
def clips():
    """lid -> float32 mono clip at the mix rate (48 kHz). Empty if the takes are not made yet."""
    out = {}
    for name, lines in (("A", make_voice.TAKE_A), ("B", make_voice.TAKE_B)):
        p = make_voice.existing_take(name)
        if not p:
            continue
        audio = read_wav(p)
        texts = [t for _, _, t, _ in lines]
        segs = align.align(audio, texts)
        for (lid, _, _, _), (s, e) in zip(lines, segs):
            c = align.trim(audio, s, e, pre=0.05, post=0.10)
            out[lid] = resample(c, TTS_SR, MIX_SR).astype(np.float32)
    return out


def durations():
    c = clips()
    return {lid: (len(c[lid]) / MIX_SR if lid in c else estimate(lid)) for lid, _, _, _ in LINES}


def inner_beats(lid, n, fallback):
    """Start times (relative to the clip) of the n spoken parts of a line, from its internal pauses."""
    c = clips()
    if lid not in c:
        return [f * durations()[lid] for f in fallback]
    a = c[lid]
    a24 = resample(a, MIX_SR, TTS_SR) if MIX_SR != TTS_SR else a
    pauses, _, _ = align.find_pauses(a24, min_len=0.09)
    d = len(a) / MIX_SR
    inner = [p for p in pauses if 0.2 < p[0] < d - 0.25]
    inner.sort(key=lambda p: p[1] - p[0], reverse=True)
    inner = sorted(inner[: n - 1])
    if len(inner) < n - 1:
        return [f * d for f in fallback]
    return [0.0] + [p[1] for p in inner]
