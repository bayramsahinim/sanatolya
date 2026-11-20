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

## Episode: "What If Every Human Is Related?" (English adaptation, vertical)

English adaptation of the Turkish shared-ancestry short, rebuilt shot for shot in Cinecode with
Just Needy as the person at the root of every family tree.

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, H.264/AAC, ~85 s) | `output/Just_Needy_What_If_Every_Human_Is_Related_EN.mp4` |
| English subtitles | `output/Just_Needy_What_If_Every_Human_Is_Related_EN.en.srt` |

```
episodes/ancestry_en/
  script.py   narration lines, on-screen captions (*highlight*, | = caption break), TTS takes
  voice.py    Gemini TTS (Puck) -> line clips -> timed voice track (build/ancestry_en/timing.json)
  people.py   ancestor portrait badges + Just Needy (badge and full body, per the character sheet)
  geo.py      orthographic globe, Africa map, flat world map (assets/geo, Natural Earth via world-atlas)
  ui.py       header block (label / value / sub) and word-timed captions with yellow highlights
  render.py   scenes A-H + frame renderer (stills / full render)
  mix.py      ambient score, ducking, loudness, SRT, final mux
  qa.py       pre-delivery checks
```

```bash
python -m episodes.ancestry_en.voice            # TTS (cached in assets/audio/tts_ancestry) + timing
python -m episodes.ancestry_en.render video     # silent 1080x1920 render
python -m episodes.ancestry_en.mix audio        # score + mix + SRT
python -m episodes.ancestry_en.mix final        # mux -> output/
python -m episodes.ancestry_en.qa output/Just_Needy_What_If_Every_Human_Is_Related_EN.mp4
```
