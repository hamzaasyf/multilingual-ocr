"""Draw the detected text lines on the image, coloured by script."""

from __future__ import annotations

import cv2
import numpy as np

from .ocr import SCRIPTS, Line

OTHER = (150, 150, 150)  # numbers and symbols


def draw_lines(image: np.ndarray, lines: list[Line], numbers: bool = True, fill: bool = True) -> np.ndarray:
    """Outline every line in its script colour, with a small number tag matching the results table.

    Small images are enlarged first so lines and tags stay crisp on screen.
    """
    up = max(1.0, 1600 / max(image.shape[:2]))
    out = cv2.resize(image, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC) if up > 1 else image.copy()
    scale = max(out.shape[:2]) / 900
    thickness = max(1, round(1.2 * scale))
    font_scale = max(0.35, 0.4 * scale)

    if fill:  # light tint inside each box so the lines read at a glance
        tint = out.copy()
        for line in lines:
            pts = (np.array(line.box) * up).astype(np.int32)
            cv2.fillPoly(tint, [pts], _color(line))
        out = cv2.addWeighted(tint, 0.16, out, 0.84, 0)

    for n, line in enumerate(lines, start=1):
        pts = (np.array(line.box) * up).astype(np.int32)
        c = _color(line)
        cv2.polylines(out, [pts], True, c, thickness, cv2.LINE_AA)
        if not numbers:
            continue
        text = str(n)
        (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        x0, y0 = int(pts[:, 0].min()), int(pts[:, 1].min())
        tx = max(0, x0 - tw - 8) if x0 - tw - 8 >= 0 else x0
        ty = max(th + base + 2, y0 + th + base + 2)
        cv2.rectangle(out, (tx, ty - th - base - 2), (tx + tw + 6, ty + 2), c, -1)
        cv2.putText(out, text, (tx + 3, ty - base + 1), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                    (20, 20, 20), 1, cv2.LINE_AA)
    return out


def _color(line: Line):
    return SCRIPTS[line.script].color if line.script in SCRIPTS else OTHER
