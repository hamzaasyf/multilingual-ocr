"""Command-line OCR: read an image or PDF and print or save the text.

Examples:
    python cli.py sign.jpg
    python cli.py scan.pdf --scripts latin,arabic -o scan.txt --json scan.json
    python cli.py menu.jpg --boxes menu-boxes.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from src.ocr import DEFAULT_SCRIPTS, SCRIPTS, MultiScriptOCR, plain_text
from src.pdf import load_any
from src.render import draw_lines


def main() -> None:
    ap = argparse.ArgumentParser(description="Read text in several scripts from an image or PDF.")
    ap.add_argument("file", help="image (jpg, png, webp...) or PDF")
    ap.add_argument("-o", "--output", help="save the plain text here (default: print it)")
    ap.add_argument("--json", help="save lines, scripts, confidences and boxes as JSON")
    ap.add_argument("--boxes", help="save an image with the line boxes drawn (first page)")
    ap.add_argument("--scripts", default=",".join(DEFAULT_SCRIPTS),
                    help=f"comma-separated, from: {', '.join(SCRIPTS)}")
    ap.add_argument("--pages", type=int, default=20, help="maximum PDF pages to read")
    ap.add_argument("--min-confidence", type=float, default=0.2)
    ap.add_argument("--enhance", action="store_true", help="clean up faint scans and phone photos")
    ap.add_argument("--gpu", action="store_true", help="use a CUDA GPU if available")
    args = ap.parse_args()

    scripts = [s.strip() for s in args.scripts.split(",") if s.strip()]
    unknown = [s for s in scripts if s not in SCRIPTS]
    if unknown:
        ap.error(f"unknown script(s): {', '.join(unknown)}. Choose from {', '.join(SCRIPTS)}.")

    ocr = MultiScriptOCR(gpu=args.gpu)
    pages, _ = load_any(args.file, args.pages)
    texts, report = [], []
    for p, page in enumerate(pages, start=1):
        result = ocr.read(page, scripts, min_confidence=args.min_confidence, enhance=args.enhance)
        texts.append(plain_text(result["lines"]))
        report.append({"page": p, "lines": [l.as_dict() for l in result["lines"]]})
        if args.boxes and p == 1:
            cv2.imwrite(args.boxes, draw_lines(page, result["lines"]))

    text = "\n\n".join(texts)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    if args.json:
        Path(args.json).write_text(json.dumps({"file": Path(args.file).name, "pages": report},
                                              ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
