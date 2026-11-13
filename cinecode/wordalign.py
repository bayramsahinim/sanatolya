"""Word-level forced alignment of a narration take against its known transcript (pocketsphinx).

Returns [{"w": spoken_word, "t0": s, "t1": s}] in take time. Used to burn captions and write
the SRT from the real audio rather than from estimates."""
import re

import librosa
import numpy as np
from pocketsphinx import Decoder

EXTRA_DICT = {
    "okene": "OW K EH N EY",
    "jascon": "JH AE S K AH N",
    "tugboat": "T AH G B OW T",
}

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(tok):
    n = int(tok)
    if 1900 < n < 2100:  # years: 2013 -> twenty thirteen
        return num_words(str(n // 100)) + num_words(str(n % 100))
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        return [_TENS[n // 10]] + ([_ONES[n % 10]] if n % 10 else [])
    raise ValueError(tok)


def spoken_tokens(text):
    """'Jascon-4 ... 2013' -> list of (spoken_word, display_index) pairs."""
    out = []
    for i, raw in enumerate(text.split()):
        core = re.sub(r"[^A-Za-z0-9'\-]", "", raw).lower()
        for part in [p for p in core.split("-") if p]:
            if part.isdigit():
                out += [(w, i) for w in num_words(part)]
            else:
                out.append((part, i))
    return out


def align(wav_path, text, sr=16000):
    y, _ = librosa.load(wav_path, sr=sr)
    pcm = (np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()
    toks = spoken_tokens(text)
    d = Decoder(samprate=sr, bestpath=False, loglevel="ERROR")
    for w, ph in EXTRA_DICT.items():
        if d.lookup_word(w) is None:
            d.add_word(w, ph, True)
    d.set_align_text(" ".join(w for w, _ in toks))
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    d.set_alignment()
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    words = []
    for seg in d.get_alignment():
        if seg.name in ("<s>", "</s>", "<sil>", "[NOISE]") or seg.name.startswith("+"):
            continue
        words.append({"w": re.sub(r"\(\d+\)$", "", seg.name), "t0": seg.start / 100.0,
                      "t1": (seg.start + seg.duration) / 100.0})
    if len(words) != len(toks):
        raise RuntimeError(f"alignment returned {len(words)} words, expected {len(toks)}")
    for wd, (w, idx) in zip(words, toks):
        wd["idx"] = idx
    return words
