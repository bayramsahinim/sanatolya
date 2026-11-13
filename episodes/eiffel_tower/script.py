"""Narration for "The Man Who Sold the Eiffel Tower" (Just Needy - Crazy But True)."""

LINES = [
    "This man sold the Eiffel Tower.",
    "There was just one problem.",
    "He didn't own it.",
    "Paris, 1925.",
    "Victor Lustig spotted a newspaper story about the tower's expensive maintenance.",
    "So he forged government letters and summoned scrap-metal dealers to a luxury hotel.",
    "His announcement?",
    "Paris was secretly dismantling the tower.",
    "And its seven thousand tons of iron were up for sale.",
    "The dealers were told to keep quiet.",
    "One of them, André Poisson, wanted the deal—but had doubts.",
    "So Lustig hinted that a little private payment could secure it.",
    "Poisson paid.",
    "Lustig took the money and disappeared.",
    "Only then did Poisson realize the documents were fake.",
    "He was so embarrassed, he reportedly stayed silent.",
    "And the strangest part?",
    "Lustig tried the same trick again.",
    "This time, he failed.",
    "The Eiffel Tower was never his to sell.",
]

DIRECTOR_NOTES = (
    "Narrator of a popular history explainer channel for YouTube Shorts. "
    "Voice: young adult American male, natural General American accent, bright, clear and confident. "
    "Medium-fast conversational pace with continuous storytelling momentum: sentences flow straight into "
    "each other with only natural micro-pauses, never a long pause after every sentence. "
    "Slightly witty, curious and matter-of-fact, like an experienced storyteller casually explaining an "
    "unbelievable true story to a friend. Put precise emphasis on the surprising words "
    "(sold, didn't own it, secretly, seven thousand tons, paid, disappeared, fake, again, failed, never). "
    "Take a short beat only before the reveals 'He didn't own it.' and 'This time, he failed.' "
    "Consistent volume. Not deep, not a movie-trailer voice, not slow documentary narration, "
    "not robotic, not a kids-show voice, no shouting, no fake excitement, no overacting. "
    "Pronounce 'André Poisson' the French way: ahn-DRAY pwah-SOHN. 'Lustig' is LUSS-tig. "
    "Say '1925' as 'nineteen twenty-five'.\n"
    "Speak only the transcript below, nothing else."
)


def tts_prompt():
    return "### DIRECTOR'S NOTES\n" + DIRECTOR_NOTES + "\n\n#### TRANSCRIPT\n" + " ".join(LINES)
