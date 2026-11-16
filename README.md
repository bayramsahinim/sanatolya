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

## Episode: "Can You Count the Jumps?" (Short, 9:16)

| Deliverable | Path |
|---|---|
| Revised video (1080×1920, 30 fps, H.264/AAC, 46.7 s, −16.5 LUFS / −2.1 dBTP) | `output/JUST_NEEDY_COUNT_THE_JUMPS_REVISED.mp4` |
| English subtitles | `output/JUST_NEEDY_COUNT_THE_JUMPS_REVISED.srt` |

Code: `episodes/count_the_jumps/` (`scene.py` deterministic 21-jump schedule, rope, penguin;
`episode.py` edit, overlays, mix, SRT; `qa.py` pixel-level jump count and delivery checks).
Narration is one TTS take with the "Umbriel" voice (`assets/audio/tts/jumps/`, chosen against the
"How Mine Salting Worked" reference by pace and pause ratio) split into lines; the penguin crosses
in the foreground at 7.2–10.5 s; captions use
word-level alignment from `cinecode/wordalign.py`.

```bash
python -m episodes.count_the_jumps.split_take          # take -> per-line clips
python -m episodes.count_the_jumps.episode all         # timeline, mix, SRT, 1080x1920 render
python -m episodes.count_the_jumps.qa output/JUST_NEEDY_COUNT_THE_JUMPS_REVISED.mp4
```
