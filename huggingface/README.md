---
title: Multilingual OCR
emoji: 🔤
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 6.31.0
app_file: app.py
pinned: false
license: mit
short_description: Read text in 18 languages from photos, scans and PDFs
---

# Multilingual OCR

Read printed text in 18 languages from photos, scans and PDFs. You don't choose a language first: each text line is read by every model you switch on, the most trustworthy reading is kept, and the line is labelled with its language, so signs, menus and forms that mix languages come out right.

| Group | Languages |
|---|---|
| English & European | English, French, German, Spanish, Italian, Portuguese |
| Arabic · Urdu · Persian | Arabic, Urdu, Persian |
| Russian · Ukrainian · Bulgarian | Russian, Ukrainian, Bulgarian |
| Hindi · Marathi · Nepali | Hindi, Marathi, Nepali |
| East Asian | Korean, Chinese (Simplified), Japanese |

**Live demo:** [Hugging Face Space](https://huggingface.co/spaces/hamzaasyf/multilingual-ocr) · **Browser-only version:** [GitHub Pages](https://hamzaasyf.github.io/multilingual-ocr/)

![Multilingual OCR: one sign, six languages](assets/cover.png)

## Features

- **Mixed languages on one page:** each line is read by the right model, so an English heading, an Arabic address and a Chinese name in the same image all come out right
- **Language per line:** every line is labelled English, French, Urdu, Russian and so on. Within a writing system the language is told apart by its letters and common words (Urdu letters such as ٹ ڈ ے, French accents and words like "votre"), and lines with no clear clue take the main language of the page
- **Images and PDFs:** photos, screenshots and scans, plus multi-page PDFs
- **Right-to-left aware:** Arabic and Urdu lines are kept in reading order, and rows are ordered right to left when most of the row is RTL
- **Line merging:** pieces of a line that the detector splits at a word gap are joined again, while table columns stay separate
- **Numbered evidence view:** every line is outlined on the image in its script's colour and numbered to match the transcript table
- **Exports:** plain text, plus JSON with each line's text, language, script, confidence, box and reading direction
- **Command-line tool** for batch work

## The app

![The app reading a French menu](assets/app.png)

## How it works

```
image / PDF page ─▶ CRAFT text detector ─▶ line boxes
                                              │
              ┌───────────── Latin model first ┤ confident? done
              ▼                                │
   Arabic · Cyrillic · Devanagari · Korean · Chinese · Japanese models
              │
              ▼
   score each reading ─▶ best per line ─▶ merge split lines ─▶ reading order ─▶ text + JSON
```

1. **Detect:** the CRAFT detector finds text lines once per page.
2. **Read:** the Latin model reads every line first. Lines it reads with high confidence are final, which keeps documents that are mostly Latin fast. The remaining lines are read by each other script model you switch on.
3. **Pick:** each reading is scored by its confidence and by whether its characters match the model's own script. Every model also knows basic English letters, but only the Latin one knows accents and symbols like €, so Latin-looking text is trusted most from the Latin model.
4. **Order:** lines are grouped into rows, sorted left to right (or right to left for Arabic rows), and fragments of one line are merged.
5. **Name the language:** letters and common words decide the language within each writing system, for example Urdu vs Arabic or French vs English.

Recognition models come from [EasyOCR](https://github.com/JaidedAI/EasyOCR), which runs on PyTorch.

## Run locally

```bash
git clone https://github.com/hamzaasyf/multilingual-ocr.git
cd multilingual-ocr
./setup.sh          # creates .venv and installs requirements
./run.sh            # opens the web interface at http://127.0.0.1:7860
```

The models (about 570 MB in total) download the first time the app starts, and are then cached in `~/.EasyOCR`.

Command line:

```bash
python cli.py samples/1-welcome-sign.jpg
python cli.py samples/delivery-notice.pdf -o notice.txt --json notice.json
python cli.py scan.jpg --scripts latin,arabic --enhance --boxes scan-boxes.png   # latin = English & European
```

## Project structure

```
multilingual-ocr/
├── app.py           Gradio interface
├── cli.py           Command-line tool
├── ui.py            Case-file theme, CSS and HTML components
├── src/
│   ├── ocr.py       Detection, per-model reading, scoring, line merging, reading order
│   ├── lang.py      Language of each line (English vs French, Arabic vs Urdu, and so on)
│   ├── render.py    Line boxes and numbers drawn on the image
│   └── pdf.py       PDF pages to images, image loading
├── samples/         Generated sample signs and a two-page PDF
└── docs/            Browser-only version (PaddleOCR + ONNX Runtime Web), served by GitHub Pages
```

## Browser-only version

`docs/index.html` is a separate version that runs entirely in the browser with PaddleOCR models and ONNX Runtime Web, so images never leave the device. It's served at [hamzaasyf.github.io/multilingual-ocr](https://hamzaasyf.github.io/multilingual-ocr/).

## Limitations

- Built for printed text. Handwriting and decorative fonts are read poorly.
- Urdu in Nastaliq calligraphy is harder than Naskh-style print, and bold Arabic headings are sometimes split or misread.
- Hindi vowel signs are occasionally confused (for example हो read as हा).
- Language labels are a best guess. Very short lines, names and all-caps text follow the main language of the page, and Hindi, Marathi and Nepali share one alphabet, so they're only told apart by a few letters.
- On free CPU hardware an image takes about 5 to 10 seconds and a PDF page about 20 seconds, so the online demo reads the first 3 pages. Set the `MAX_PDF_PAGES` environment variable to change this.

## Use cases

Digitising multilingual forms and invoices, reading shop signs and menus for travel or mapping apps, indexing scanned archives, and pre-processing documents for search or LLM pipelines.

## About

Built by [Muhammad Hamza Asif](https://www.linkedin.com/in/hamzaasyf/), AI engineer working on computer vision, speech AI and LLM applications. Need something like this for your product or workflow? [Get in touch on LinkedIn](https://www.linkedin.com/in/hamzaasyf/).

## Licence

Code: MIT. EasyOCR and its models: Apache 2.0. The browser version uses PaddleOCR models (Apache 2.0).
