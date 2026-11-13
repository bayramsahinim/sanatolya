"""Narration for 'He Survived 60 Hours Underwater' (Harrison Okene, Jascon-4, 2013).

Each entry is one narration beat. The whole script is recorded as ONE continuous take
(consistent voice), then force-aligned word by word (pocketsphinx) and cut at the
beat boundaries so the picture can be timed against real speech.
"""
BEATS = [
    ("hook",    "This diver was searching for dead bodies... when someone grabbed his hand."),
    ("name",    "The man was Harrison Okene."),
    ("hours",   "His ship had already been underwater for nearly sixty hours."),
    ("capsize", "Back in 2013, the tugboat Jascon-4 capsized off the coast of Nigeria."),
    ("pocket",  "As the vessel filled with water, Harrison made it into a small trapped air pocket inside the wreck."),
    ("reason",  "And that air pocket is the reason he didn't die immediately."),
    ("science", "Here's the important part: a trapped pocket of air can keep someone alive for a while... but only temporarily."),
    ("o2",      "Oxygen gets used up."),
    ("co2",     "Carbon dioxide builds up."),
    ("shrink",  "And the safe space can shrink as water rises."),
    ("odds",    "So every hour inside that wreck made survival less likely."),
    ("wait",    "He waited there in darkness... until rescue divers finally entered the ship."),
    ("expect",  "They were expecting to recover bodies."),
    ("found",   "Instead... they found a survivor."),
    ("final",   "Harrison Okene had stayed alive underwater for nearly sixty hours."),
]

# Captions/SRT spelling (what viewers read) for words the TTS text spells out.
DISPLAY = {"sixty": "60", "Jascon-4": "Jascon-4"}

DIRECTOR_NOTES = (
    "You are the narrator of a hugely popular 'crazy but true' animated YouTube Shorts channel. "
    "Voice: young adult American male, clear and confident, natural and conversational, like an experienced "
    "YouTube storyteller telling a friend a gripping true story. Medium-fast pace with real momentum, clean "
    "consonants, smooth flow between sentences, tiny pauses only. Punch the key nouns and verbs naturally. "
    "Not deep, not a movie-trailer voice, not a documentary professor, not robotic, never shouting, no fake excitement.\n"
    "Delivery by section:\n"
    "- First sentence (hook): immediately engaging, slightly urgent, lean on 'dead bodies' and 'grabbed his hand', with a short beat at the ellipsis.\n"
    "- Story setup: keep it moving, fluid, no long pauses.\n"
    "- 'Here's the important part' through 'water rises': curious, knowledgeable, conversational, crisp short sentences.\n"
    "- 'So every hour' and 'He waited there in darkness': slightly slower, quieter tension, without losing momentum.\n"
    "- Ending: build anticipation; take a short pause after 'Instead...' before 'they found a survivor'; "
    "deliver the final sentence with controlled surprise and emotional weight.\n"
    "Speak only the transcript below, nothing else.\n\nTranscript:\n"
)
