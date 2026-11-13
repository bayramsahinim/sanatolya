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

## Episode: "Just Needy — Zombie Apocalypse, Day 1 (Remastered)"

Day 1 rebuilt to match the zombie series' look: a cold, overcast, foggy morning, a lit and shaded hoodie hero,
an asymmetric infected rig, a restrained science motion graphic and a dark sound design.

| Deliverable | Path |
|---|---|
| Final video (1080×1920 native, 30 fps, H.264/AAC) | `output/JUST_NEEDY_ZOMBIE_DAY_1_REMASTERED.mp4` |
| English subtitles (separate, not burned in) | `output/JUST_NEEDY_ZOMBIE_DAY_1_REMASTERED.srt` |

```
episodes/zombie_day_1/
  script.py      approved narration + delivery notes
  make_voice.py  one Gemini TTS take (channel narrator voice "Puck"), cached
  world.py       portrait sets, props, lighting, fog, infected rig, typography
  shots.py       shot list / timeline (26 shots) + on-screen accents
  render.py      frame render (+ film grain) -> H.264
  mix.py         narration placement, procedural SFX, drone, ducking, SRT
  finalize.py    mux + loudness (-14 LUFS) -> output/
```

```bash
python -m episodes.zombie_day_1.make_voice
python -m episodes.zombie_day_1.render          # or: --still 1.0,30.0 for preview stills
python -m episodes.zombie_day_1.mix
python -m episodes.zombie_day_1.finalize
```
