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

## Episode: "Just Needy — Zombie Apocalypse, Part 3: Don't Let It Out"

| Deliverable | Path |
|---|---|
| Final video (1080×1920 vertical, 30 fps, H.264/AAC, 60.5 s) | `output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4` |
| English subtitles (separate SRT, sentence cues) | `output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.srt` |
| **Captioned version** (word-group captions burned in, mining-reference style) | `output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4` |
| Captioned SRT (same 1–3 word groups) | `output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.srt` |

Captions use word-level forced alignment against the real narration audio (`captions.py`: espeak-ng
re-synthesis + MFCC/DTW, boundaries snapped to measured pauses), Montserrat ExtraBold white with a black
outline, centred at ~70.6 % of frame height, switching instantly between groups.

Part 3 moves Cinecode from flat 2D sets to a **real 3D world** (Three.js / WebGL, rendered headless in
Chromium at native 1080×1920): a modelled farmhouse with interior, ~25k individually animated corn stalks
(GPU bend driven by the unseen thing's route), barn, tractor, fence, maintenance hatch, fog, shadows,
depth of field and a film grade. The stick-figure characters stay 2D: they are drawn with Canvas2D every
frame and placed in the world as lit, fogged, shadow-casting billboards.

```
episodes/zombie_part3/
  script.py, timeline.json     narration (verbatim) + single timing source for picture, sound, SRT
  make_voice.py                Gemini TTS: one continuous narrator take + radio whisper (cached)
  soundtrack.py                line placement, radio processing, procedural SFX + score, mix, SRT
  web/                         world.js (set), rig.js (2D characters), main.js (shots), post.js
  render.js                    headless frame renderer      assemble.sh / qa.py   mux + checks
```

```bash
(cd build/p3 && npm i three@0.170.0)          # or set P3_NODE_MODULES
python -m episodes.zombie_part3.make_voice
python -m episodes.zombie_part3.soundtrack
node episodes/zombie_part3/render.js frames build/p3/frames 0 60.5
python -m episodes.zombie_part3.captions          # word alignment -> captions.ass + SRTs
episodes/zombie_part3/assemble.sh && episodes/zombie_part3/assemble.sh captioned
python episodes/zombie_part3/qa.py output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4
```
