# Just Needy — Cinecode episodes

**Cinecode** is the code-driven 2D animation pipeline used to produce Just Needy episodes:
vector characters and sets drawn with Cairo, procedural sound design and music, Gemini TTS
narration, and ffmpeg assembly. Every frame and sound is reproducible from this repository.

## Episode: "I Got Stuck in Ancient Rome for 7 Days"

| Deliverable | Path |
|---|---|
| Final video (1920×1080, 30 fps, H.264/AAC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4` |
| English subtitles (YouTube CC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt` |
| Thumbnail | `output/thumbnail_1280x720.jpg`, `output/thumbnail_1920x1080.png` |

### Layout

```
cinecode/            engine
  core.py            canvas helpers, easing, keyframes, camera
  characters.py      stick-figure rig + cast (hero, Maximus, Lucia, the boy, Romans)
  props.py, sets.py  props and environments (room, Roman street, forum, bakery, square, desert)
  captions.py        on-screen text, implemented to the channel caption spec
  timeline.py        shot planning (animation timed to the real voice clips) + episode assembly
  audio.py           procedural SFX, music, ambience, mixing helpers
  tts.py / align.py  Gemini TTS client, take-to-line alignment
config/narrator_voice.json   the channel narrator voice (reuse for every episode)
episodes/rome_7_days/
  script.py          narration + dialogue
  scenes_*.py        shots for scenes 1-10
  episode.py         assemble / render / mix / SRT
  qa.py              pre-delivery checks
assets/              font (Montserrat ExtraBold, OFL) and cached TTS takes
```

### Rebuild

```bash
pip install pycairo numpy scipy soundfile pillow librosa fonttools
apt-get install -y ffmpeg rubberband-cli espeak-ng
mkdir -p ~/.fonts && cp assets/fonts/Montserrat-ExtraBold.ttf ~/.fonts && fc-cache -f

python -m episodes.rome_7_days.make_voice           # TTS (cached in assets/audio/tts)
python -m episodes.rome_7_days.align_voice          # split takes into lines
python -m episodes.rome_7_days.episode audio        # soundtrack + SRT
python -m episodes.rome_7_days.episode video        # final 1080p render
python -m episodes.rome_7_days.thumbnail
python -m episodes.rome_7_days.qa output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4
```

## Episode: Plant Poison — English adaptation of the Turkish short

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 24 fps, H.264/AAC, ~49 s, −14.9 LUFS) | `output/JUST_NEEDY_PLANT_POISON_ENGLISH.mp4` |
| English subtitles (sentence-level SRT) | `output/JUST_NEEDY_PLANT_POISON_ENGLISH.srt` |

Faithful line-by-line adaptation (`episodes/plant_poison/script.py` keeps each Turkish line next
to its English version and the source caption-block timing). Original visuals and scene order
are kept; Turkish captions are removed and the picture is reconstructed; English narration is
the channel Gemini voice (Puck) directed for a Shorts history/science read; captions are 1–3
word groups (hand-cut in `CAPS`), white Montserrat ExtraBold with a thick black outline at 70%
height. Background is a procedural ambient bed (the original music/rain can't be separated
from the Turkish voice).

```bash
pip install opencv-python-headless soundfile scipy numpy pillow
python episodes/plant_poison/decaption.py SOURCE_TR.mp4 build/clean.mp4   # remove Turkish text
python -m episodes.plant_poison.make_voice a        # TTS (cached in assets/audio/tts)
python -m episodes.plant_poison.voice               # inspect line clips / word timings
python -m episodes.plant_poison.episode build/clean.mp4 output          # full render
python -m episodes.plant_poison.episode build/clean.mp4 output audio    # re-mix audio only, picture copied
```
