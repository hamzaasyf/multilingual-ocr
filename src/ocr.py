"""Multilingual OCR: one text detector, several script recognisers, best reading per line."""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field

import cv2
import numpy as np

from .lang import LANGUAGE_NAMES
from .lang import assign as assign_languages


@dataclass(frozen=True)
class Script:
    id: str                 # writing system, used internally and in the JSON report
    name: str               # language group shown in the interface
    languages: str
    easyocr_langs: tuple    # passed to easyocr.Reader
    color: tuple            # BGR, used for the line boxes
    hex: str                # same colour for HTML


SCRIPTS = {
    s.id: s
    for s in (
        Script("latin", "English & European", "English, French, German, Spanish, Italian, Portuguese",
               ("en", "fr", "de", "es", "it", "pt"), (181, 196, 83), "#53C4B5"),
        Script("arabic", "Arabic · Urdu · Persian", "Arabic, Urdu, Persian",
               ("ar", "fa", "ur", "en"), (106, 196, 233), "#E9C46A"),
        Script("cyrillic", "Russian · Ukrainian · Bulgarian", "Russian, Ukrainian, Bulgarian",
               ("ru", "uk", "bg", "en"), (240, 166, 108), "#6CA6F0"),
        Script("devanagari", "Hindi · Marathi · Nepali", "Hindi, Marathi, Nepali",
               ("hi", "mr", "ne", "en"), (60, 138, 240), "#F08A3C"),
        Script("korean", "Korean", "Korean", ("ko", "en"), (240, 140, 180), "#B48CF0"),
        Script("chinese", "Chinese (Simplified)", "Simplified Chinese", ("ch_sim", "en"), (77, 72, 229), "#E5484D"),
        Script("japanese", "Japanese", "Japanese", ("ja", "en"), (170, 120, 240), "#F078AA"),
    )
}
DEFAULT_SCRIPTS = ("latin", "arabic", "cyrillic", "devanagari", "korean", "chinese")

# Unicode ranges used to tell which script a piece of text is written in
_RANGES = {
    "arabic": r"؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿",
    "cyrillic": r"Ѐ-ӿ",
    "devanagari": r"ऀ-ॿ",
    "korean": r"가-힯ᄀ-ᇿ㄰-㆏",
    "japanese": r"぀-ヿ",
    "chinese": r"一-鿿",
    "latin": r"A-Za-zÀ-ɏ",
}
_RTL = {"arabic"}
SURE = 0.8  # a Latin reading this confident is final; the line skips the other models


def script_of(text: str) -> str | None:
    """The script most of the letters in `text` belong to (kana makes it Japanese)."""
    counts = {k: len(re.findall(f"[{r}]", text)) for k, r in _RANGES.items()}
    if counts["japanese"]:
        counts["japanese"] += counts.pop("chinese")
    best = max(counts, key=counts.get)
    return best if counts[best] else None


def _weight(text: str, reader_id: str) -> float:
    """How much to trust a reading, given which script model produced it.

    Every non-Latin model also knows basic English letters, but only the Latin
    model knows accents, € and the like, so Latin-looking text is trusted most
    from the Latin model. A model is trusted fully when it reads letters of its
    own script, and hardly at all when it outputs letters of a different script.
    """
    letters = [c for c in text if unicodedata.category(c).startswith("L")]
    found = script_of("".join(letters)) if letters else None
    if reader_id == "latin":
        return 1.0 if found in (None, "latin") else 0.3
    if found in (None, "latin"):
        return 0.75
    if found == reader_id or (reader_id == "japanese" and found == "chinese"):
        return 1.0
    return 0.3


@dataclass
class Line:
    box: list                 # four [x, y] corner points, clockwise from top-left
    text: str
    confidence: float
    script: str | None
    readings: dict = field(default_factory=dict)  # every script reader's attempt, for the report
    language: str | None = None                   # ISO 639-1 code, set by src.lang.assign

    @property
    def rect(self):
        xs = [p[0] for p in self.box]
        ys = [p[1] for p in self.box]
        return min(xs), min(ys), max(xs), max(ys)

    def as_dict(self) -> dict:
        x0, y0, x1, y1 = self.rect
        return {
            "text": self.text,
            "language": self.language,
            "language_name": LANGUAGE_NAMES.get(self.language),
            "script": self.script,
            "confidence": round(self.confidence, 3),
            "box": [round(x0), round(y0), round(x1 - x0), round(y1 - y0)],
            "direction": "rtl" if self.script in _RTL else "ltr",
        }


class MultiScriptOCR:
    """Find text lines once, read each line with every chosen script model, keep the best reading.

    Models are loaded on first use and cached, so a script that is never
    switched on is never downloaded.
    """

    def __init__(self, gpu: bool = False, max_side: int = 1600):
        self.gpu = gpu
        self.max_side = max_side
        self._readers: dict = {}

    def reader(self, script_id: str):
        if script_id not in self._readers:
            import easyocr  # imported here so the rest of the module works without it

            self._readers[script_id] = easyocr.Reader(
                list(SCRIPTS[script_id].easyocr_langs), gpu=self.gpu, verbose=False
            )
        return self._readers[script_id]

    def warm_up(self, scripts=DEFAULT_SCRIPTS) -> None:
        for s in scripts:
            self.reader(s)

    def read(self, image: np.ndarray, scripts=DEFAULT_SCRIPTS, min_confidence: float = 0.2,
             text_threshold: float = 0.7, enhance: bool = False) -> dict:
        """Read a BGR image. Returns {"lines": [Line], "scale": float, "timings": {...}}."""
        scripts = [s for s in scripts if s in SCRIPTS] or ["latin"]
        h, w = image.shape[:2]
        scale = min(1.0, self.max_side / max(h, w))
        work = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else image
        if enhance:
            work = _enhance(work)

        t0 = time.time()
        # width_ths joins words into lines; a little wider than EasyOCR's default suits Arabic word gaps
        horizontal, free = self.reader(scripts[0]).detect(work, text_threshold=text_threshold, width_ths=0.8)
        horizontal, free = horizontal[0], free[0]
        t_det = time.time() - t0

        boxes = [[[x0, y0], [x1, y0], [x1, y1], [x0, y1]] for x0, x1, y0, y1 in horizontal]
        boxes += [[list(map(float, p)) for p in quad] for quad in free]
        if not boxes:
            return {"lines": [], "scale": scale, "timings": {"detection": t_det, "recognition": 0.0}}

        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        candidates: dict[int, dict] = {i: {} for i in range(len(boxes))}

        def best(i):
            return max(candidates[i].items(), key=lambda kv: kv[1][1] * _weight(kv[1][0], kv[0]))

        t1 = time.time()
        # Latin first: most documents are mostly Latin, and lines it reads with
        # near certainty are not sent to the slower script models.
        open_ids = list(range(len(boxes)))
        for sid in sorted(scripts, key=lambda s: s != "latin"):
            if not open_ids:
                break
            todo = [boxes[i] for i in open_ids]
            results = self.reader(sid).recognize(
                gray, horizontal_list=[_hbox(b) for b in todo if _is_axis_aligned(b)],
                free_list=[b for b in todo if not _is_axis_aligned(b)], detail=1,
            )
            # results are matched back to their box by position, whatever order EasyOCR returns them in
            for box, text, conf in results:
                i = _match(box, boxes)
                if i is not None and text.strip():
                    candidates[i][sid] = (text.strip(), float(conf))
            if sid == "latin":
                open_ids = [i for i in open_ids
                            if not candidates[i] or best(i)[1][1] * _weight(best(i)[1][0], "latin") < SURE]
        t_rec = time.time() - t1

        lines = []
        for i, box in enumerate(boxes):
            if not candidates[i]:
                continue
            sid, (text, conf) = best(i)
            if conf < min_confidence:
                continue
            pts = [[p[0] / scale, p[1] / scale] for p in box]
            lines.append(Line(pts, text, conf, script_of(text),
                              {k: {"text": t, "confidence": round(c, 3)} for k, (t, c) in candidates[i].items()}))
        lines = reading_order(lines)
        assign_languages(lines)
        return {"lines": lines, "scale": scale, "timings": {"detection": t_det, "recognition": t_rec}}


def reading_order(lines: list[Line]) -> list[Line]:
    """Sort lines top to bottom; lines whose vertical centres are close count as one row."""
    if not lines:
        return lines
    heights = sorted(l.rect[3] - l.rect[1] for l in lines)
    tol = heights[len(heights) // 2] * 0.5
    rows: list[list[Line]] = []
    for line in sorted(lines, key=lambda l: (l.rect[1] + l.rect[3]) / 2):
        cy = (line.rect[1] + line.rect[3]) / 2
        if rows and abs(cy - np.mean([(l.rect[1] + l.rect[3]) / 2 for l in rows[-1]])) <= tol:
            rows[-1].append(line)
        else:
            rows.append([line])
    ordered = []
    for row in rows:
        rtl = sum(1 for l in row if l.script in _RTL) > len(row) / 2
        ordered += _merge_row(sorted(row, key=lambda l: l.rect[0], reverse=rtl), rtl)
    return ordered


def _merge_row(row: list[Line], rtl: bool) -> list[Line]:
    """Join pieces of one line that the detector split at a word gap (common in Arabic and Urdu).

    Pieces merge when they are in the same script (or one is just numbers) and
    the gap between them is less than about one text height, so separate table
    cells stay separate.
    """
    out: list[Line] = []
    for line in row:
        if out:
            prev = out[-1]
            h = max(prev.rect[3] - prev.rect[1], line.rect[3] - line.rect[1])
            gap = prev.rect[0] - line.rect[2] if rtl else line.rect[0] - prev.rect[2]
            same = prev.script == line.script or None in (prev.script, line.script)
            if same and -0.3 * h < gap < 0.9 * h:
                x0, y0 = min(prev.rect[0], line.rect[0]), min(prev.rect[1], line.rect[1])
                x1, y1 = max(prev.rect[2], line.rect[2]), max(prev.rect[3], line.rect[3])
                n0, n1 = len(prev.text), len(line.text)
                out[-1] = Line(
                    [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                    f"{prev.text} {line.text}",
                    (prev.confidence * n0 + line.confidence * n1) / (n0 + n1),
                    prev.script or line.script,
                    {"merged": [prev.readings, line.readings]},
                )
                continue
        out.append(line)
    return out


def plain_text(lines: list[Line]) -> str:
    """Lines joined into text, with lines on the same row separated by spaces."""
    if not lines:
        return ""
    out, prev = [], None
    heights = sorted(l.rect[3] - l.rect[1] for l in lines)
    tol = heights[len(heights) // 2] * 0.5
    for line in lines:
        cy = (line.rect[1] + line.rect[3]) / 2
        if prev is not None and abs(cy - prev) <= tol:
            out[-1] += "    " + line.text  # separate columns stay visibly apart
        else:
            out.append(line.text)
        prev = cy
    return "\n".join(out)


def _enhance(image: np.ndarray) -> np.ndarray:
    """For faint scans and phone photos: contrast boost on lightness, light denoise."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(l)
    out = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    return cv2.fastNlMeansDenoisingColored(out, None, 5, 5, 7, 21)


def _is_axis_aligned(box) -> bool:
    return box[0][1] == box[1][1] and box[0][0] == box[3][0]


def _hbox(box):
    return [int(box[0][0]), int(box[1][0]), int(box[0][1]), int(box[2][1])]


def _match(result_box, boxes, tol: float = 3.0):
    """Index of the detected box that a recognition result belongs to."""
    rx, ry = float(result_box[0][0]), float(result_box[0][1])
    best, best_d = None, tol
    for i, b in enumerate(boxes):
        d = abs(b[0][0] - rx) + abs(b[0][1] - ry)
        if d <= best_d:
            best, best_d = i, d
    if best is None:  # rotated boxes can come back with corners in another order
        cx = np.mean([float(p[0]) for p in result_box])
        cy = np.mean([float(p[1]) for p in result_box])
        dists = [abs(np.mean([p[0] for p in b]) - cx) + abs(np.mean([p[1] for p in b]) - cy) for b in boxes]
        i = int(np.argmin(dists))
        best = i if dists[i] < 10 else None
    return best
