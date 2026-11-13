"""English SRT from the word-aligned final narration (same timings as the burned-in captions)."""
import os

from episodes.eiffel_tower.compose import CUES, ROOT, WORDS


def ts(t):
    t = max(0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def phrase_cues(max_chars=42):
    """Readable subtitle cues: whole sentences, long ones split in balanced halves; word-accurate timing."""
    from episodes.eiffel_tower.compose import split_balanced
    lines = {}
    for w in WORDS:
        lines.setdefault(w["line"], []).append(w)
    cues = []
    for li in sorted(lines):
        ws = lines[li]
        txt = " ".join(x["w"] for x in ws)
        cues += [ws] if len(txt) <= max_chars else split_balanced(ws, max_chars, 12, len(txt) / 2)
    out = []
    for k, c in enumerate(cues):
        st = c[0]["start"] - 0.05
        en = c[-1]["end"] + 0.25
        if k + 1 < len(cues):
            en = min(en, cues[k + 1][0]["start"] - 0.06)
        out.append((st, en, " ".join(x["w"] for x in c).replace("\u2014 ", "\u2014")))
    return out


def write(path, cues):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    p = os.path.join(ROOT, "output", "JUST_NEEDY_EIFFEL_TOWER_FINAL.srt")
    write(p, phrase_cues())
    print(open(p).read()[:1500])
    print(len(CUES), "burned-in caption cues")
