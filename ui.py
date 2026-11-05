"""Look and feel: a case-file design on carbon-blue, shared by all the demo apps."""

from __future__ import annotations

import datetime as _dt
import html

import gradio as gr

NAVY = "#1C2B4A"
PAPER = "#F1EFE8"
INK = "#1D1D1B"
MUTED = "#6B6A64"
RED = "#B3261E"
STAMP = "#FF5A4F"

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@600;700&family=Courier+Prime:wght@400;700&family=Noto+Sans:wght@400;600&family=Noto+Naskh+Arabic:wght@400;600&family=Noto+Sans+Devanagari:wght@400;600&family=Noto+Sans+KR:wght@400;600&family=Noto+Sans+SC:wght@400;600&display=swap" rel="stylesheet">
"""

_THEME_VARS = dict(
    body_background_fill=NAVY,
    body_text_color=INK,
    background_fill_primary=PAPER,
    background_fill_secondary=PAPER,
    block_background_fill=PAPER,
    block_border_color=INK,
    block_border_width="1px",
    block_label_background_fill=PAPER,
    block_label_text_color=INK,
    block_label_border_color=INK,
    block_title_text_color=MUTED,
    block_shadow="none",
    border_color_primary=INK,
    input_background_fill=PAPER,
    input_border_color=INK,
    input_placeholder_color=MUTED,
    color_accent=RED,
    color_accent_soft="#E8D9D2",
    slider_color=RED,
    checkbox_background_color=PAPER,
    checkbox_background_color_selected=INK,
    checkbox_border_color=INK,
    checkbox_border_color_selected=INK,
    button_primary_background_fill=INK,
    button_primary_background_fill_hover="#000000",
    button_primary_text_color=PAPER,
    button_secondary_background_fill=PAPER,
    button_secondary_text_color=INK,
    button_secondary_border_color=INK,
    panel_background_fill=PAPER,
    panel_border_color=INK,
)

_base = gr.themes.Base(
    font=[gr.themes.GoogleFont("Courier Prime"), gr.themes.Font("Courier New"), gr.themes.Font("monospace")],
    font_mono=[gr.themes.GoogleFont("Courier Prime"), gr.themes.Font("Courier New"), gr.themes.Font("monospace")],
    radius_size=gr.themes.sizes.radius_none,
)
# The design has one look. Use the same values in dark mode, so visitors whose
# browser or Hugging Face account is set to dark see the same page.
_dark = {f"{k}_dark": v for k, v in _THEME_VARS.items() if hasattr(_base, f"{k}_dark")}
THEME = _base.set(**_THEME_VARS, **_dark)

CSS = f"""
:root, .dark {{ color-scheme: light; }}
.gradio-container {{ max-width: 1240px !important; padding: 28px 40px 40px !important; }}
footer:not(.foot) {{ display: none !important; }}

/* ---- header ---- */
.case-head *, .case-lede, .stats *, .foot, .foot * {{ color:{PAPER} !important; }}
.case-head .stamp {{ color:{STAMP} !important; }}
.case-head .case-title .bar {{ color:transparent !important; }}
.more .label-wrap span, .more button span {{ color:{INK} !important; }}
.case-head {{ display:flex; justify-content:space-between; align-items:flex-end; gap:24px;
  border-bottom:2px solid {PAPER}; padding-bottom:16px; margin-bottom:6px; color:{PAPER}; }}
.case-eyebrow {{ font-size:12px; letter-spacing:3px; text-transform:uppercase; opacity:.85; }}
.case-title {{ font-family:'Lora', Georgia, serif; font-size:46px; font-weight:700; line-height:1.05;
  letter-spacing:-.5px; margin:6px 0 0; color:{PAPER}; }}
.case-title .bar {{ background:{PAPER}; color:transparent; padding:0 4px; user-select:none; }}
.case-meta {{ text-align:right; font-size:12px; line-height:1.8; letter-spacing:.5px; }}
.stamp {{ display:inline-block; border:2px solid {STAMP}; color:{STAMP}; padding:2px 10px; font-weight:700;
  letter-spacing:3px; transform:rotate(-4deg); margin-top:6px; transition:opacity .3s; }}
.stamp.idle {{ opacity:.35; }}
.case-lede {{ color:{PAPER}; opacity:.85; font-size:14px; max-width:780px; margin:10px 0 18px; line-height:1.6; }}

/* ---- tabs ---- */
.tabs > .tab-wrapper button, .tabs button[role="tab"] {{ color:{PAPER} !important; opacity:.6;
  letter-spacing:2px; text-transform:uppercase; font-size:13px; border:none !important; background:transparent !important; }}
.tabs button[role="tab"][aria-selected="true"] {{ opacity:1; border-bottom:2px solid {STAMP} !important; }}
.tabs .tabitem {{ background:transparent !important; border:none !important; padding:16px 0 0 !important; }}

/* ---- control panel (paper) ---- */
.paper {{ background:{PAPER}; border:1px solid {INK}; padding:18px !important; gap:14px !important; }}
.paper .block, .paper .form {{ border:none !important; background:transparent !important; box-shadow:none !important; }}
.paper label > span, .paper .block-title, .paper [data-testid="block-info"] {{ text-transform:uppercase;
  letter-spacing:2px; font-size:11px !important; color:{MUTED} !important; }}
.drop {{ border:1px dashed {INK} !important; }}

/* segmented radios */
.seg .wrap {{ display:flex !important; gap:0 !important; border:1px solid {INK}; }}
.seg .wrap label {{ flex:1; justify-content:center; margin:0 !important; border:none !important;
  border-right:1px solid {INK} !important; background:{PAPER} !important; padding:9px 4px !important;
  box-shadow:none !important; border-radius:0 !important; }}
.seg .wrap label:last-child {{ border-right:none !important; }}
.seg .wrap label input {{ display:none; }}
.seg .wrap label.selected, .seg .wrap label:has(input:checked) {{ background:{INK} !important; color:{PAPER} !important; }}
.seg .wrap label span {{ text-transform:none !important; letter-spacing:0 !important; font-size:13px !important;
  color:inherit !important; margin:0 !important; }}

.go button, button.go {{ letter-spacing:3px; text-transform:uppercase; font-weight:700; padding:14px !important; }}
.note {{ font-size:11px; color:{MUTED}; margin:0; }}
.more {{ border:1px solid {INK} !important; }}

/* ---- input tabs inside the paper panel ---- */
.intabs button[role="tab"] {{ color:{INK} !important; opacity:.55; letter-spacing:2px; text-transform:uppercase;
  font-size:12px; background:transparent !important; border:none !important; }}
.intabs button[role="tab"][aria-selected="true"] {{ opacity:1; border-bottom:2px solid {RED} !important; }}
.intabs .tabitem {{ background:transparent !important; border:none !important; padding:10px 0 0 !important; }}

/* script picker: wrapping chips */
.chips .wrap {{ display:flex !important; flex-wrap:wrap; gap:6px !important; }}
.chips .wrap label {{ margin:0 !important; border:1px solid {INK} !important; background:{PAPER} !important;
  padding:6px 10px !important; box-shadow:none !important; border-radius:0 !important; }}
.chips .wrap label input {{ display:none; }}
.chips .wrap label.selected, .chips .wrap label:has(input:checked) {{ background:{INK} !important; color:{PAPER} !important; }}
.chips .wrap label span {{ text-transform:none !important; letter-spacing:0 !important; font-size:13px !important;
  color:inherit !important; margin:0 !important; }}
.chips [data-testid="block-info"] + div, .chips .info {{ text-transform:none !important; letter-spacing:0 !important; }}

/* examples label on the navy page */
.block.hide-container > .label, .block.hide-container > .label * {{ color:{PAPER} !important; opacity:.85; }}

/* ---- exhibit (results) ---- */
.exhibit {{ gap:12px !important; }}
.figure {{ border:1px solid {INK} !important; padding:10px !important; background:{PAPER} !important; }}
.figure img {{ object-fit:contain; }}
.stats {{ display:flex; gap:40px; color:{PAPER}; padding:4px 2px; }}
.stats b {{ font-family:'Lora', Georgia, serif; font-size:30px; display:block; line-height:1.1; }}
.stats span {{ font-size:12px; letter-spacing:.5px; opacity:.8; }}
.paperfile {{ border:1px solid {INK} !important; }}
.paperfile table, .paperfile tr, .paperfile td, .paperfile tbody, .paperfile .file-preview-holder {{ background:{PAPER} !important; color:{INK} !important; }}
.more.dark {{ background:{PAPER}; }}

/* ---- transcript: numbered lines, like an evidence log ---- */
.log {{ background:{PAPER}; border:1px solid {INK}; padding:0; max-height:420px; overflow:auto; }}
.log table {{ width:100%; border-collapse:collapse; font-size:14px; }}
.log th {{ position:sticky; top:0; background:{INK} !important; color:{PAPER} !important; text-align:left;
  font-weight:400; font-size:11px; letter-spacing:2px; text-transform:uppercase; padding:8px 10px; }}
.log td {{ border-top:1px solid #CFCBBF; padding:7px 10px; vertical-align:top; color:{INK} !important;
  background:{PAPER} !important; }}
.log td.n {{ width:34px; color:{MUTED} !important; }}
.log td.t {{ font-family:'Noto Sans','Noto Naskh Arabic','Noto Sans Devanagari','Noto Sans KR','Noto Sans SC',
  system-ui, sans-serif; font-size:16px; unicode-bidi:plaintext; }}
.log td.c {{ width:70px; text-align:right; font-variant-numeric:tabular-nums; }}
.log td.c.low {{ color:{RED} !important; }}
.chip {{ display:inline-block; width:9px; height:9px; margin-right:7px; vertical-align:middle; }}
.log .s {{ width:130px; white-space:nowrap; font-size:12px; }}
.log .empty {{ padding:22px; color:{MUTED} !important; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; color:{PAPER}; }}
.legend span {{ color:{PAPER} !important; }}
.page-note {{ color:{PAPER} !important; font-size:12px; opacity:.8; margin:0; }}
.transcript textarea {{ font-family:'Noto Sans','Noto Naskh Arabic','Noto Sans Devanagari','Noto Sans KR',
  'Noto Sans SC', system-ui, sans-serif !important; font-size:15px !important; unicode-bidi:plaintext;
  line-height:1.6 !important; }}

.foot {{ color:{PAPER}; opacity:.75; font-size:12px; margin-top:22px; text-align:center; }}
.foot a {{ color:{PAPER}; text-decoration:underline; }}

@media (max-width: 760px) {{
  .gradio-container {{ padding:16px !important; }}
  .case-head {{ flex-direction:column; align-items:flex-start; }}
  .case-meta {{ text-align:left; }}
  .case-title {{ font-size:34px; }}
  .stats {{ gap:20px; flex-wrap:wrap; }}
}}
"""


def header_html(file_info: str = "awaiting upload", stamped: bool = False) -> str:
    case_no = "OCR-" + _dt.date.today().strftime("%Y-%m%d")
    stamp_cls = "stamp" if stamped else "stamp idle"
    return f"""
<div class="case-head">
  <div>
    <div class="case-eyebrow">Exhibit 02 · Document AI</div>
    <h1 class="case-title">Multilingual OCR</h1>
  </div>
  <div class="case-meta">CASE NO. {case_no}<br>FILE: {html.escape(file_info)}<br><span class="{stamp_cls}">TRANSCRIBED</span></div>
</div>
<p class="case-lede">Read printed text in 18 languages, from English and French to Arabic, Urdu, Hindi, Russian,
Korean and Chinese, in photos, scans and PDFs, with no language chosen in advance. Each line is read by every
model you switch on, the most trustworthy reading is kept, and its language is named.</p>
"""


def stats_html(lines="—", scripts="—", confidence="—", time_taken="—",
               labels=("text lines", "languages found", "avg. confidence", "read time")) -> str:
    values = (lines, scripts, confidence, time_taken)
    cells = "".join(f"<div><b>{v}</b><span>{l}</span></div>" for v, l in zip(values, labels))
    return f'<div class="stats">{cells}</div>'


def legend_html(scripts: dict) -> str:
    items = "".join(f'<span><i class="chip" style="background:{s.hex}"></i>{s.name}</span>' for s in scripts.values())
    return f'<div class="legend">{items}</div>'


def lines_html(rows: list[dict] | None = None, scripts: dict | None = None) -> str:
    """Numbered transcript table. rows: line dicts with text, language_name, script, confidence (and page)."""
    if not rows:
        return '<div class="log"><div class="empty">Transcribed lines appear here, numbered as on the image.</div></div>'
    multi_page = len({r.get("page", 1) for r in rows}) > 1
    head = "<tr><th>#</th>" + ("<th>Page</th>" if multi_page else "") + "<th>Language</th><th>Text</th><th>Conf.</th></tr>"
    body = []
    for r in rows:
        s = (scripts or {}).get(r["script"])
        color = s.hex if s else "#969696"
        name = r.get("language_name") or "Numbers"
        low = " low" if r["confidence"] < 0.5 else ""
        page = f'<td class="n">{r["page"]}</td>' if multi_page else ""
        body.append(
            f'<tr><td class="n">{r["n"]}</td>{page}<td class="s"><i class="chip" style="background:{color}"></i>{name}</td>'
            f'<td class="t" dir="auto">{html.escape(r["text"])}</td><td class="c{low}">{r["confidence"]:.2f}</td></tr>'
        )
    return f'<div class="log"><table>{head}{"".join(body)}</table></div>'
