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

## Episode (Short): "The Prisoner Who Escaped With Dry Peas"

Strict visual adaptation of the Turkish short *"Bu Mahkum Kuru Bezelyeyle Hapisten Kaçtı"*: same hook,
scene order, humour and ending; Just Needy plays the prisoner in an orange prison uniform; narration
translated line-for-line (`episodes/dry_peas_escape/script.py` keeps the Turkish next to each English line).

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, H.264/AAC stereo, 69.9 s) | `output/JUST_NEEDY_DRY_PEAS_PRISON_ESCAPE_FINAL.mp4` |
| English subtitles (SRT) | `output/JUST_NEEDY_DRY_PEAS_PRISON_ESCAPE_ENGLISH.srt` |
| QA sheet (reference above, ours below, same beats) | `output/JUST_NEEDY_DRY_PEAS_QA_reference_vs_final.png` |

Every English line starts at its Turkish line's timestamp (or right after the previous line), so the comic
beats land where the source puts them. Rebuild:

```bash
python -m episodes.dry_peas_escape.make_voice      # Gemini TTS, channel narrator (cached)
python -m episodes.dry_peas_escape.align_voice     # lines + word timing
python -m episodes.dry_peas_escape.episode all     # mix, SRT, 1080x1920 render
```

### Visual-fix version (source picture, new main character)

Per the director's correction, this version keeps the **original reference video's picture**: backgrounds,
guards, warden, camera, effects and timing are the source frames themselves. Only the main prisoner changes.

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, H.264/AAC stereo, 68.8 s) | `output/JUST_NEEDY_PRISON_ESCAPE_VISUAL_FIXED.mp4` |
| English subtitles (SRT) | `output/JUST_NEEDY_PRISON_ESCAPE_VISUAL_FIXED_ENGLISH.srt` |
| QA sheet (source above, fixed below) | `output/JUST_NEEDY_PRISON_ESCAPE_VISUAL_FIXED_QA_source_vs_fixed.png` |

Pipeline (`episodes/dry_peas_escape/vfx/`): Gemini finds the prisoner's head/body/arms on keyframes
(`detect.py`, `detect_arms.py`; results in `assets/vfx/dry_peas/*.json`), SAM 2.1 tracks them through every
shot (`track.py`; masks in `assets/vfx/dry_peas/masks/`), `compose.py` swaps the egg head + cap for Just Needy's
round white head (lit to match each shot), recolours the striped uniform orange using the source's own
shading, removes the burned-in Turkish text and sets English captions; `finish.py` lays the English narration
over the source's own music/effects (Turkish voice removed with Demucs).

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install sam2 opencv-python-headless demucs
# frames: ffmpeg -i SOURCE.mp4 -q:v 2 -start_number 0 build/dry_peas_vfx/jpg/%05d.jpg ; masks -> build/dry_peas_vfx/masks
python -m episodes.dry_peas_escape.vfx.compose geom
python -m episodes.dry_peas_escape.vfx.finish all
```
