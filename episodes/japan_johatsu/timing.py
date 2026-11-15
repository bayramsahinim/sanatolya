"""Word-level timing for the narration take.

The take is cut at every pause (cinecode.align.find_pauses, min 0.12 s); each piece was transcribed
separately with Gemini to confirm which script words it holds (PIECE_TEXT below). Inside a piece,
words are spread over its voiced span by syllable weight, with extra weight for punctuation pauses.
"""
import json
import re

import numpy as np

from cinecode import align, tts
from episodes.japan_johatsu.script import CAPTION_SUBS

TAKE = "assets/audio/tts/johatsu/narration_6e242b326e.wav"
PIECES = json.load(open("assets/audio/tts/johatsu/pieces.json"))
PIECE_TEXT = [
    "In Japan, you can pay a company to vanish overnight.",
    "The firms that do it are called yonige-ya.",
    "Night movers.",
    "Say you lost your job,",
    "the debt is choking you, and you can't face your family. You make one phone call.",
    "At midnight, a van with its headlights off pulls up to your door.",
    "A crew slips in quietly and packs your whole life into a few boxes.",
    "You cancel your phone line, too.",
    "The price? Around fifty thousand yen, and up to three hundred thousand for a complicated move.",
    "",
    "By morning, you wake up in a one-window room, in a city you've never seen.",
    "The next day, your mom runs to the police.",
    "But if an adult leaves by choice, and there's no sign of a crime, police in Japan usually won't search.",
    "The file gets closed.",
    "Your mom hires a private detective.",
    "Without access to personal records, he gets nowhere.",
    "In 2025, Japan's police received over eighty thousand missing-person reports, for all kinds of reasons.",
    "Most of them are found.",
    "But some are",
    "never heard from again.",
    "The Japanese call people who choose to vanish jōhatsu.",
    "The evaporated.",
    "The detective's report to your mom says just one sentence.",
    "Your son",
    "",
    "chose to leave.",
    "",
]


def _syl(w):
    w = w.lower()
    if re.fullmatch(r"\d+", w):
        return {"2025": 5}.get(w, 3)
    w = re.sub(r"[^a-zō]", "", w).replace("ō", "o")
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def _voiced(a, s, e):
    db = align.envelope_db(a[int(s * tts.SR):int(e * tts.SR)])
    thr = np.percentile(db, 95) - 30
    idx = np.where(db >= thr)[0]
    if not len(idx):
        return s, e
    return s + idx[0] * align.HOP / tts.SR, s + (idx[-1] + 1) * align.HOP / tts.SR


def words():
    a = tts.read_wav(TAKE)
    out = []
    for (s, e), txt in zip(PIECES, PIECE_TEXT):
        ws = txt.split()
        if not ws:
            continue
        vs, ve = _voiced(a, s, e)
        wt = []
        for i, w in enumerate(ws):
            k = _syl(w) + 0.5
            if i < len(ws) - 1 and re.search(r"[,.?]$", w):
                k += 1.6 if w.endswith((".", "?")) else 0.8
            wt.append(k)
        cum = np.concatenate([[0], np.cumsum(wt)]) / sum(wt)
        for i, w in enumerate(ws):
            ws_t = vs + cum[i] * (ve - vs)
            we_t = vs + cum[i + 1] * (ve - vs)
            if re.search(r"[,.?]$", w) and i < len(ws) - 1:
                we_t = ws_t + (we_t - ws_t) * 0.62
            out.append({"w": w, "s": round(ws_t, 3), "e": round(we_t, 3)})
    return out


def caption_groups(ws=None, max_words=3, max_chars=16):
    """1-3 word groups, broken at punctuation; number phrases collapsed to numerals."""
    ws = ws or words()
    # collapse spoken numbers
    toks = []
    i = 0
    while i < len(ws):
        hit = False
        for spoken, shown in CAPTION_SUBS.items():
            n = len(spoken.split())
            seq = " ".join(re.sub(r"[,.?]", "", x["w"]) for x in ws[i:i + n])
            if seq.lower() == spoken:
                tail = re.findall(r"[,.?]$", ws[i + n - 1]["w"])
                toks.append({"w": shown + (tail[0] if tail else ""), "s": ws[i]["s"], "e": ws[i + n - 1]["e"],
                             "solo": True})
                i += n
                hit = True
                break
        if not hit:
            toks.append(dict(ws[i]))
            i += 1
    groups, cur = [], []
    for k, t in enumerate(toks):
        if t.get("solo") and cur:
            groups.append(cur)
            cur = []
        cur.append(t)
        text = " ".join(x["w"] for x in cur)
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        brk = (re.search(r"[,.?]$", t["w"]) or len(cur) >= max_words or t.get("solo")
               or (nxt and len(text) + 1 + len(nxt["w"]) > max_chars)
               or (nxt and nxt["s"] - t["e"] > 0.35))
        if brk:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    # don't strand a function word at the end of a group
    weak = {"a", "an", "the", "to", "of", "and", "for", "your", "in", "with", "into", "by", "if", "are", "is",
            "who", "up", "one", "just", "that"}
    for i in range(len(groups) - 1):
        g = groups[i]
        while (len(g) >= 2 and g[-1]["w"].lower() in weak and not g[-1].get("solo")
               and len(groups[i + 1]) < max_words and not groups[i + 1][0].get("solo")):
            groups[i + 1].insert(0, g.pop())
    cues = []
    for g in groups:
        txt = " ".join(x["w"] for x in g)
        txt = re.sub(r"[,]$", "", txt)
        txt = re.sub(r"\.$", "", txt) if not txt.endswith("..") else txt
        cues.append({"text": txt, "s": g[0]["s"], "e": g[-1]["e"]})
    # hold each cue until the next one (max +0.5 s), min 0.25 s on screen
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["s"] if i + 1 < len(cues) else c["e"] + 0.8
        c["e"] = max(c["s"] + 0.25, min(nxt, c["e"] + 0.5))
    return cues


if __name__ == "__main__":
    for c in caption_groups():
        print(f"{c['s']:6.2f}-{c['e']:6.2f}  {c['text']}")
