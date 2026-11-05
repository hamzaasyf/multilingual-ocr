"""Turn PDF pages into images for OCR."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def pdf_pages(path: str | Path, max_pages: int = 5, dpi: int = 150) -> tuple[list[np.ndarray], int]:
    """Render up to `max_pages` pages as BGR images. Returns (images, total page count)."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(path))
    try:
        total = len(doc)
        images = []
        for i in range(min(total, max_pages)):
            pil = doc[i].render(scale=dpi / 72).to_pil().convert("RGB")
            images.append(cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR))
        return images, total
    finally:
        doc.close()


def load_any(path: str | Path, max_pages: int = 5) -> tuple[list[np.ndarray], int]:
    """Load an image or a PDF as a list of BGR pages. Returns (pages, total pages in the file)."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return pdf_pages(path, max_pages)
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        try:  # formats OpenCV can't open, such as HEIC or some WebP files
            from PIL import Image

            img = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception as exc:
            raise ValueError(f"Could not open {path.name} as an image or PDF.") from exc
    return [img], 1
