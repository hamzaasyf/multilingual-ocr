"""Tell the language of each OCR line, within the script it was read in.

The script models only know the writing system, so a line read by the
"Latin" model could be English, French or Spanish. This module looks for
letters and short common words that give a language away. Lines with no clear
signal (a name, a number, "Croque-monsieur") take the main language of the
same script on the page.
"""

from __future__ import annotations

import re
from collections import Counter

LANGUAGE_NAMES = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian", "pt": "Portuguese",
    "ar": "Arabic", "ur": "Urdu", "fa": "Persian",
    "ru": "Russian", "uk": "Ukrainian", "bg": "Bulgarian",
    "hi": "Hindi", "mr": "Marathi", "ne": "Nepali",
    "ko": "Korean", "zh": "Chinese", "ja": "Japanese",
}
# language assumed when a script has no signal anywhere on the page
SCRIPT_DEFAULT = {"latin": "en", "arabic": "ar", "cyrillic": "ru", "devanagari": "hi",
                  "korean": "ko", "chinese": "zh", "japanese": "ja"}

# letters that point to a language: (letters, weight)
_LATIN_LETTERS = {
    "fr": [("âêîôûëïœ", 3), ("çèàé", 1)],
    "de": [("äöüß", 3)],
    "es": [("ñ¿¡", 3), ("áíóú", 1)],
    "pt": [("ãõ", 3), ("çáéíóúâêô", 1)],
    "it": [("ìò", 3), ("àèéù", 1)],
}
_STOPWORDS = {
    "en": "the and of to in is for with your you are this that on at be by from or our we it as an",
    "fr": "le la les des du de et est un une pour votre vous nous dans sur au aux avec ce cette ne pas merci",
    "de": "der die das und ist mit für von zu den dem ein eine nicht auf im sie wir bitte",
    "es": "el la los las de del y en es para con por un una su que se gracias",
    "it": "il lo gli la le di del della e è per con un una che non sono grazie",
    "pt": "o os a as de do da dos das e é para com um uma não em no na seu sua obrigado",
}
_WORD_LANGS: dict[str, list[str]] = {}
for _lang, _words in _STOPWORDS.items():
    for _w in _words.split():
        _WORD_LANGS.setdefault(_w, []).append(_lang)

_URDU = "ٹڈڑںےۓھہۃ"          # letters used in Urdu but not in Arabic
_PERSIAN = "ژ"                 # Persian, not Urdu or Arabic
_PERSO = "پچگکی"              # Persian and Urdu, not Arabic
_ARABIC = "ةيكىإأؤئ"          # Arabic forms that Urdu and Persian write differently


def guess(text: str, script: str | None) -> tuple[str | None, float]:
    """Best language guess for one line and how strong the evidence is (0 = no signal)."""
    if script == "latin":
        return _guess_latin(text)
    if script == "arabic":
        ur = sum(text.count(c) for c in _URDU)
        fa = 3 * sum(text.count(c) for c in _PERSIAN)
        per = sum(text.count(c) for c in _PERSO)
        ar = sum(text.count(c) for c in _ARABIC)
        if ur and ur >= ar:
            return "ur", float(ur)
        if fa or (per > ar):
            return "fa", float(fa + per - ar)
        return ("ar", float(ar)) if ar else (None, 0.0)
    if script == "cyrillic":
        scores = {"uk": sum(text.count(c) for c in "іїєґІЇЄҐ") * 2,
                  "ru": sum(text.count(c) for c in "ыэёЫЭЁ") * 2,
                  "bg": text.count("ъ") + text.count("Ъ")}
        best = max(scores, key=scores.get)
        return (best, float(scores[best])) if scores[best] else (None, 0.0)
    if script == "devanagari":
        return ("mr", 2.0) if "ळ" in text else (None, 0.0)
    if script in SCRIPT_DEFAULT:  # Korean, Chinese, Japanese: script and language match
        return SCRIPT_DEFAULT[script], 5.0
    return None, 0.0


def _guess_latin(text: str) -> tuple[str | None, float]:
    low = text.lower()
    scores: Counter = Counter()
    for lang, groups in _LATIN_LETTERS.items():
        for letters, weight in groups:
            scores[lang] += weight * sum(low.count(c) for c in letters)
    for word in re.findall(r"[a-zà-ÿß]+", low.replace("'", " ").replace("’", " ")):
        langs = _WORD_LANGS.get(word, [])
        for lang in langs:
            scores[lang] += 2 / len(langs)  # words shared by several languages count for less
    if not scores or max(scores.values()) < 1:
        return None, 0.0
    lang, score = scores.most_common(1)[0]
    return lang, float(score)


def assign(lines) -> None:
    """Set `line.language` on every line, using the page to fill in lines with no signal."""
    guesses = [guess(l.text, l.script) for l in lines]
    page_main: dict[str, str] = {}
    for script in {l.script for l in lines if l.script}:
        votes: Counter = Counter()
        for l, (lang, strength) in zip(lines, guesses):
            if l.script == script and lang:
                votes[lang] += strength
        page_main[script] = votes.most_common(1)[0][0] if votes else SCRIPT_DEFAULT.get(script)
    for l, (lang, _) in zip(lines, guesses):
        l.language = (lang or page_main.get(l.script)) if l.script else None
