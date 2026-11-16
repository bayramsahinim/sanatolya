"""Word-level forced alignment for short narration clips.

Each word of the known transcript is synthesised separately with espeak-ng and the
pieces are concatenated, so the reference word boundaries are exact. The reference is
then aligned to the real take with DTW over MFCC features, and each boundary is mapped
through the warping path. Accurate to a few tens of ms on clean single-speaker TTS,
which is what 1-3 word burned-in captions need.
"""
import re
import subprocess
import tempfile

import librosa
import numpy as np
import soundfile as sf

SR = 16000
HOP = 160


def _espeak(word, tmp):
    p = f"{tmp}/w.wav"
    subprocess.run(["espeak-ng", "-v", "en-us", "-s", "175", "-w", p, word], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a, sr = sf.read(p)
    a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
    # trim silence around the word
    idx = np.where(np.abs(a) > 0.02 * np.abs(a).max())[0]
    return a[idx[0]: idx[-1] + 1] if len(idx) else a


def _feat(a):
    m = librosa.feature.mfcc(y=a, sr=SR, n_mfcc=20, hop_length=HOP, n_fft=512)[1:]
    m = (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)
    return m


def spoken_words(text):
    return re.findall(r"[A-Za-z0-9'\-]+[.,?!]*", text)


def align_words(audio, sr, text):
    """Return [(word, t0, t1)] in seconds relative to `audio` (already trimmed to speech)."""
    y_full = librosa.resample(np.asarray(audio, np.float32), orig_sr=sr, target_sr=SR)
    # align only the speech: clips may carry silent margins, which would drag the first/last word
    rms = librosa.feature.rms(y=y_full, frame_length=320, hop_length=HOP)[0]
    db = 20 * np.log10(rms + 1e-9)
    on = np.where(db > db.max() - 40)[0]
    s0, s1 = on[0] * HOP, min(len(y_full), (on[-1] + 2) * HOP)
    y = y_full[s0:s1]
    offset = s0 / SR
    words = spoken_words(text)
    with tempfile.TemporaryDirectory() as tmp:
        pieces = [_espeak(re.sub(r"[.,?!]", "", w).replace("-", " "), tmp) for w in words]
    gap = np.zeros(int(0.05 * SR), np.float32)
    ref, bounds, pos = [], [], 0
    for k, p in enumerate(pieces):
        if k:
            ref.append(gap)
            pos += len(gap)
        bounds.append((pos, pos + len(p)))
        ref.append(p)
        pos += len(p)
    ref = np.concatenate(ref)
    F1, F2 = _feat(ref), _feat(y)
    _, wp = librosa.sequence.dtw(X=F1, Y=F2, metric="cosine")
    wp = wp[::-1]
    m = np.zeros(F1.shape[1], dtype=float)
    for i, j in wp:
        m[i] = j  # last (largest) j for each ref frame
    dur = len(y) / SR

    def map_t(sample):
        i = min(int(sample / HOP), len(m) - 1)
        return float(m[i] * HOP / SR)

    out = []
    for w, (a, b) in zip(words, bounds):
        out.append([w, map_t(a), map_t(b)])
    # monotone, contiguous, within the clip
    out[0][1] = 0.0
    for k in range(1, len(out)):
        out[k][1] = max(out[k][1], out[k - 1][1] + 0.05)
        out[k - 1][2] = out[k][1]
    out[-1][2] = dur
    return [(w, a + offset, b + offset) for w, a, b in out]


def group_words(words, max_words=3, max_chars=18):
    """Group aligned words into caption cues of 1-3 words, breaking after punctuation."""
    cues, cur = [], []
    for w, a, b in words:
        if cur and len(" ".join(x[0] for x in cur + [(w,)])) > max_chars:
            cues.append(cur)
            cur = []
        cur.append((w, a, b))
        text = " ".join(x[0] for x in cur)
        end_punct = w[-1] in ".,?!"
        if len(cur) >= max_words or end_punct:
            cues.append(cur)
            cur = []
    if cur:
        # avoid a dangling single short word: merge into previous if it fits
        if cues and len(cur) == 1 and len(cues[-1]) < max_words and cues[-1][-1][0][-1] not in ".?!":
            cues[-1] += cur
        else:
            cues.append(cur)
    return [(" ".join(x[0] for x in c), c[0][1], c[-1][2]) for c in cues]
