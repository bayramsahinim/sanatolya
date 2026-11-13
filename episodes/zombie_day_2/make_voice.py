"""Generate the Day 2 narration with Gemini TTS in two takes (the free tier allows ~10
requests per model per day, so never one request per line):

  take A  narrator (channel voice, config/narrator_voice.json), lines n01..n17
  take B  narrator + stranger, multi-speaker, the whispered ending n18..s02

Takes are cached in assets/audio/tts/zombie_day_2 and split into per-line clips by
episodes.zombie_day_2.voice.

usage: python -m episodes.zombie_day_2.make_voice [A|B ...] [--model MODEL]
"""
import json
import os
import sys

from cinecode import tts
from episodes.zombie_day_2.script import LINES, STRANGER_NOTES, STRANGER_VOICE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "zombie_day_2")

TAKE_A = [l for l in LINES if l[0] <= "n17" and l[0].startswith("n")]
TAKE_B = [l for l in LINES if l not in TAKE_A]

PERFORMANCE_A = (
    "This is episode 2 of a zombie survival comedy, told in first person by the same narrator as episode 1. "
    "Keep the same voice through every line, medium-fast and natural, never rushed. Sarcastic lines are dry and "
    "understated, never shouted. Give the strongest comic emphasis to \"Five stars for commitment.\" and to "
    "\"Survival expert. Obviously.\" (a beat before \"Obviously.\"). Lean on the word LEFT in \"what was "
    "LEFT of him\". In the item list, leave a short beat before \"And one sock.\" The survival tip is brisk "
    "and clear. From \"I opened the hatch\" on, get quieter and more careful; \"Finally. Quiet.\" is a "
    "relieved, soft exhale.")


def take_a_text():
    notes = CFG["director_notes"].replace("Speak only", PERFORMANCE_A + "\nSpeak only")
    return "### DIRECTOR'S NOTES\n" + notes + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, _, t, _ in TAKE_A)


def take_b_text():
    who = {"narrator": "Narrator", "stranger": "Stranger"}
    body = "\n".join(f"{who[s]}: {t}" for _, s, t, _ in TAKE_B)
    return ("### DIRECTOR'S NOTES\nThe ending of a zombie survival comedy short, now dark and suspenseful. "
            "Narrator: a young adult American man, the same narrator as before, now hushed and frightened, "
            "almost whispering. Stranger: " + STRANGER_NOTES + " The Stranger whispers both lines, with a "
            "tense pause of about a second and a half between them. Leave about one second between all lines."
            "\nSpeak only the transcript below, nothing else.\n\n#### TRANSCRIPT\n" + body)


def take_path(name, model=None):
    model = model or CFG["model"]
    text = take_a_text() if name == "A" else take_b_text()
    return os.path.join(OUT, f"take{name}_{tts.text_hash(text, CFG['voice'], STRANGER_VOICE, model)}.wav")


def existing_take(name):
    """Cached take for this script, from whichever model made it (primary model first)."""
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        p = take_path(name, model)
        if os.path.exists(p):
            return p
    return None


def make(name, models):
    if existing_take(name):
        print(name, "cached", existing_take(name))
        return
    for model in models:
        p = take_path(name, model)
        try:
            if name == "A":
                a = tts.synth(take_a_text(), p, model, voice=CFG["voice"])
            else:
                a = tts.synth(take_b_text(), p, model,
                              speakers={"Narrator": CFG["voice"], "Stranger": STRANGER_VOICE})
            print(name, f"{len(a) / tts.SR:.1f}s", model, p)
            return
        except RuntimeError as e:
            print(name, model, str(e)[:200])
    raise SystemExit(f"take {name}: all TTS models refused")


if __name__ == "__main__":
    args = sys.argv[1:]
    models = [CFG["model"]] + CFG.get("fallback_models", [])
    if "--model" in args:
        i = args.index("--model")
        models = [args[i + 1]]
        del args[i:i + 2]
    for name in args or ["A", "B"]:
        make(name, models)
