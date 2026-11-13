"""Generate the narration as ONE continuous take (consistent voice, one request) plus the radio
whisper, via Gemini TTS. Cached in assets/audio/tts/zombie_p3. Split into lines by align_voice.py.

usage: python -m episodes.zombie_part3.make_voice [narration] [radio]
"""
import json, os, sys
from cinecode import tts
from episodes.zombie_part3.script import NARRATION, RADIO, NARRATOR_NOTES, RADIO_NOTES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "zombie_p3")
RADIO_VOICE = "Enceladus"
MODELS = os.environ.get("P3_TTS_MODELS", "gemini-2.5-pro-preview-tts,gemini-2.5-flash-preview-tts,"
                        + ",".join([CFG["model"]] + CFG["fallback_models"])).split(",")


def narration_prompt():
    return ("### DIRECTOR'S NOTES\n" + NARRATOR_NOTES +
            "\nRead each line as its own sentence. Leave a clear pause of about one second between lines. "
            "Build tension gradually toward the end. The last line, 'A voice whispered...', is hushed and "
            "trails off.\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in NARRATION))


def radio_prompt():
    return "### DIRECTOR'S NOTES\n" + RADIO_NOTES + "\n\n#### TRANSCRIPT\n" + RADIO[1]


def take_path(kind, prompt, voice, model):
    return os.path.join(OUT, f"{kind}_{tts.text_hash(prompt, voice, model)}.wav")


def existing(kind):
    fs = sorted(f for f in os.listdir(OUT) if f.startswith(kind + "_") and f.endswith(".wav"))
    return os.path.join(OUT, fs[-1]) if fs else None


def make(kind, prompt, voice):
    os.makedirs(OUT, exist_ok=True)
    for model in MODELS:
        p = take_path(kind, prompt, voice, model)
        try:
            a = tts.synth(prompt, p, model, voice=voice)
            print(kind, f"{len(a)/tts.SR:.2f}s", model, "->", p, flush=True)
            return p
        except RuntimeError as e:
            print(kind, model, str(e)[:100].replace("\n", " "), flush=True)
    raise SystemExit("all TTS models exhausted")


if __name__ == "__main__":
    which = sys.argv[1:] or ["narration", "radio"]
    if "narration" in which:
        make("narration", narration_prompt(), CFG["voice"])
    if "radio" in which:
        make("radio", radio_prompt(), RADIO_VOICE)
