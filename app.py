"""Gradio demo: read text in 18 languages from photos, scans and PDFs."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path

import cv2
import gradio as gr

from src.ocr import DEFAULT_SCRIPTS, SCRIPTS, MultiScriptOCR, plain_text
from src.pdf import load_any
from src.render import draw_lines
from ui import CSS, HEAD, THEME, header_html, legend_html, lines_html, stats_html

# This app runs on CPU. If the Hugging Face Space is set to ZeroGPU hardware,
# ZeroGPU refuses to start unless at least one function is marked with
# @spaces.GPU, so register a no-op one. Outside Hugging Face this does nothing.
try:
    import spaces

    @spaces.GPU
    def _zerogpu_check():
        return None
except ImportError:
    pass

MAX_PDF_PAGES = int(os.environ.get("MAX_PDF_PAGES", "3"))
SAMPLES = Path(__file__).parent / "samples"
NAME_TO_ID = {f"{s.name}": s.id for s in SCRIPTS.values()}

ocr = MultiScriptOCR()
# Load the default models in the background so the first visitor doesn't wait for downloads
threading.Thread(target=ocr.warm_up, daemon=True).start()


def run_ocr(image_path, pdf_path, source, script_names, min_conf, sensitivity, enhance, numbers,
            progress=gr.Progress()):
    path = pdf_path if source == "PDF" else image_path
    if not path:
        raise gr.Error("Add a PDF first." if source == "PDF" else "Add an image first.")
    scripts = [NAME_TO_ID[n] for n in script_names] or ["latin"]

    try:
        pages, total_pages = load_any(path, MAX_PDF_PAGES)
    except ValueError as exc:
        raise gr.Error(str(exc))

    out_dir = Path(tempfile.mkdtemp())
    started = time.time()
    rows, page_texts, figures, report_pages = [], [], [], []
    n = 0
    for p, page in enumerate(pages, start=1):
        progress((p - 1) / len(pages), desc=f"Reading page {p} of {len(pages)}")
        result = ocr.read(page, scripts, min_confidence=min_conf, text_threshold=sensitivity, enhance=enhance)
        lines = result["lines"]
        fig = out_dir / f"page-{p}.png"
        cv2.imwrite(str(fig), draw_lines(page, lines, numbers=numbers))
        figures.append(str(fig))
        page_texts.append(plain_text(lines))
        for line in lines:
            n += 1
            rows.append({"n": n, "page": p, **line.as_dict()})
        report_pages.append({
            "page": p,
            "size": [page.shape[1], page.shape[0]],
            "timings_s": {k: round(v, 2) for k, v in result["timings"].items()},
            "lines": [{"n": r["n"], **{k: v for k, v in r.items() if k not in ("n", "page")}}
                      for r in rows if r["page"] == p],
        })
    seconds = time.time() - started

    text = "\n\n".join(f"--- Page {i} ---\n{t}" if len(pages) > 1 else t for i, t in enumerate(page_texts, 1))
    found = sorted({r["script"] for r in rows if r["script"]}, key=list(SCRIPTS).index)
    languages = sorted({r["language_name"] for r in rows if r["language_name"]})
    avg = sum(r["confidence"] for r in rows) / len(rows) if rows else 0
    report = {
        "file": Path(path).name,
        "pages_read": len(pages),
        "pages_in_file": total_pages,
        "scripts_enabled": scripts,
        "scripts_found": found,
        "languages_found": languages,
        "lines": len(rows),
        "average_confidence": round(avg, 3),
        "processing_seconds": round(seconds, 1),
        "pages": report_pages,
    }
    txt_path, json_path = out_dir / "transcript.txt", out_dir / "transcript.json"
    txt_path.write_text(text, encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    note = ""
    if total_pages > len(pages):
        note = f"This demo reads the first {len(pages)} of {total_pages} pages."
    choices = [f"Page {i}" for i in range(1, len(figures) + 1)]
    h, w = pages[0].shape[:2]
    file_info = f"{Path(path).name[:28]} · {len(pages)} pages" if len(pages) > 1 else f"{w}×{h}"
    return (
        figures[0],
        gr.update(choices=choices, value=choices[0], visible=len(figures) > 1),
        figures,
        stats_html(len(rows), len(languages), f"{avg:.2f}" if rows else "—", f"{seconds:.1f} s"),
        lines_html(rows, SCRIPTS),
        text,
        [str(txt_path), str(json_path)],
        report,
        header_html(file_info, stamped=True),
        note,
    )


def show_page(choice, figures):
    if not figures or not choice:
        return gr.update()
    return figures[int(choice.split()[-1]) - 1]


with gr.Blocks(title="Multilingual OCR") as demo:
    header = gr.HTML(header_html())
    source = gr.State("Image")
    figures_state = gr.State([])

    with gr.Row(equal_height=False):
        with gr.Column(scale=4, min_width=300, elem_classes="paper"):
            with gr.Tabs(elem_classes="intabs") as in_tabs:
                with gr.Tab("Image", id="Image") as tab_img:
                    image_in = gr.Image(type="filepath", label="Photo or scan", height=220, elem_classes="drop")
                with gr.Tab("PDF", id="PDF") as tab_pdf:
                    pdf_in = gr.File(label=f"PDF (first {MAX_PDF_PAGES} pages)", file_types=[".pdf"],
                                     elem_classes="drop paperfile")
            scripts_in = gr.CheckboxGroup(
                [s.name for s in SCRIPTS.values()],
                value=[SCRIPTS[s].name for s in DEFAULT_SCRIPTS],
                label="Languages to look for", elem_classes="chips",
                info="English & European covers English, French, German, Spanish, Italian and Portuguese. "
                     "Each line is read by every model ticked here and the best reading wins. Fewer is faster.",
            )
            min_conf = gr.Slider(0.0, 0.8, value=0.2, step=0.05, label="Drop lines below confidence")
            with gr.Accordion("More settings", open=False, elem_classes="more"):
                sensitivity = gr.Slider(0.4, 0.9, value=0.7, step=0.05, label="Text detection threshold",
                                        info="Lower finds fainter text, and more noise.")
                enhance = gr.Checkbox(value=False, label="Clean up faint scans and phone photos")
                numbers = gr.Checkbox(value=True, label="Number the lines on the image")
            go = gr.Button("Read text", variant="primary", elem_classes="go")
            gr.HTML('<p class="note">Files are processed for this request only and are not stored.</p>')

        with gr.Column(scale=8, elem_classes="exhibit"):
            figure = gr.Image(label="Fig. A — text lines found", interactive=False, height=520,
                              elem_classes="figure", buttons=["fullscreen"])
            page_pick = gr.Radio([], label="Page", visible=False, elem_classes="seg")
            gr.HTML(legend_html(SCRIPTS))
            stats = gr.HTML(stats_html())
            page_note = gr.Markdown("", elem_classes="page-note")
            table = gr.HTML(lines_html())
            transcript = gr.Textbox(label="Transcript", lines=8, max_lines=20, buttons=["copy"],
                                    elem_classes="transcript", rtl=False)
            files = gr.File(label="Download transcript (TXT and JSON)", file_count="multiple",
                            elem_classes="paperfile")
            with gr.Accordion("Report (JSON)", open=False, elem_classes="more dark"):
                report = gr.JSON(show_label=False)

    examples = sorted(str(p) for p in SAMPLES.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if examples:
        gr.Examples(examples=examples, inputs=image_in, label="Sample exhibits")

    tab_img.select(lambda: "Image", None, source)
    tab_pdf.select(lambda: "PDF", None, source)
    go.click(
        run_ocr,
        [image_in, pdf_in, source, scripts_in, min_conf, sensitivity, enhance, numbers],
        [figure, page_pick, figures_state, stats, table, transcript, files, report, header, page_note],
    )
    page_pick.change(show_page, [page_pick, figures_state], figure)

    gr.HTML(
        '<footer class="foot">Built by <a href="https://www.linkedin.com/in/hamzaasyf/">Muhammad Hamza Asif</a>'
        ' · <a href="https://github.com/hamzaasyf/multilingual-ocr">Source on GitHub</a>'
        ' · CRAFT text detector and recognisers from EasyOCR</footer>'
    )

if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS, head=HEAD, show_error=True)
