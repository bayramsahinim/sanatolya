"""Split the single narration take into per-line clips (pause-based DP alignment)."""
import functools

import numpy as np

from cinecode import align
from cinecode.audio import SR as MIX_SR
from cinecode.audio import resample
from cinecode.tts import SR as TTS_SR
from cinecode.tts import read_wav
from episodes.zombie_day_2_rebuilt import make_voice
from episodes.zombie_day_2_rebuilt.script import NARRATION, TEXT


def estimate(lid):
    return align.syllables(TEXT[lid]) * 0.165 + 0.15


@functools.lru_cache(maxsize=None)
def segments():
    p = make_voice.existing_take()
    if not p:
        return None, None
    audio = read_wav(p)
    return audio, align.align(audio, [t for _, t in NARRATION])


@functools.lru_cache(maxsize=None)
def clips():
    audio, segs = segments()
    if audio is None:
        return {}
    out = {}
    for (lid, _), (s, e) in zip(NARRATION, segs):
        c = align.trim(audio, s, e, pre=0.05, post=0.12)
        out[lid] = resample(c, TTS_SR, MIX_SR).astype(np.float32)
    return out


def durations():
    c = clips()
    return {lid: (len(c[lid]) / MIX_SR if lid in c else estimate(lid)) for lid, _ in NARRATION}
