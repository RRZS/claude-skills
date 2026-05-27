#!/usr/bin/env python3
"""Build a single PDF from the Wind & Water book material.

Reads OUTLINE.md and the three sample-chapter files in feng-shui-book/,
strips the dev top-notes from the chapters and the redundant H1 from the
outline, assembles a book-layout HTML (title page + note page + chapters
+ outline appendix) and renders to PDF via WeasyPrint.

Run:    python3 build_pdf.py
Output: /tmp/wind-and-water.pdf  (also writes the intermediate HTML)
"""

from __future__ import annotations

from pathlib import Path

import markdown
from weasyprint import CSS, HTML

ROOT = Path(__file__).resolve().parent
OUTLINE = ROOT / "OUTLINE.md"
CHAPTERS = [
    ROOT / "sample-chapter-5-qi.md",
    ROOT / "sample-chapter-18-flying-stars.md",
    ROOT / "sample-chapter-31-bedroom.md",
]
OUT_PDF = Path("/tmp/wind-and-water.pdf")
OUT_HTML = Path("/tmp/wind-and-water.html")


def strip_dev_note(text: str) -> str:
    """Drop the leading *Sample chapter draft for...* paragraph + the
    following horizontal rule from a chapter file."""
    lines = text.splitlines()
    if not lines or not lines[0].lstrip().startswith("*Sample chapter draft for*"):
        return text
    idx = 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx < len(lines) and lines[idx].strip() == "---":
        idx += 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    return "\n".join(lines[idx:])


def strip_outline_header(text: str) -> str:
    """Drop the OUTLINE.md H1 + 'comprehensive book outline...' tagline so it
    does not duplicate the part-break announcement."""
    lines = text.splitlines()
    idx = 0
    # skip leading blanks
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    # drop H1
    if idx < len(lines) and lines[idx].lstrip().startswith("# "):
        idx += 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    # drop bold tagline line
    if idx < len(lines) and lines[idx].lstrip().startswith("**A comprehensive"):
        idx += 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    # drop a single '---' separator if next
    if idx < len(lines) and lines[idx].strip() == "---":
        idx += 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    return "\n".join(lines[idx:])


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["extra", "tables", "sane_lists"],
        output_format="html5",
    )


TITLE_PAGE = """
<section class="title-page">
  <div class="imprint">CINNABAR PRESS &nbsp;·&nbsp; EST. MMXXVI</div>
  <h1 class="book-title">Wind &amp; Water</h1>
  <div class="ornament">— 風水 —</div>
  <h2 class="book-subtitle">THE COMPLETE FENG SHUI COMPENDIUM</h2>
  <p class="strapline"><em>Principles, Practice, and the Soulful Art of Living in Balance</em></p>
  <div class="author">Mei Lin Tsao</div>
  <div class="foreword-by">FOREWORD BY MASTER CHEN YAN-HUI</div>
  <div class="title-footer">CINNABAR PRESS<br/><span class="small">an imprint of the House of Wind &amp; Water</span></div>
</section>
"""

NOTE_PAGE = """
<section class="note-page">
  <h2>About this draft</h2>
  <p>This is an early compilation from the <em>Wind &amp; Water</em> book project. It contains, in order:</p>
  <ol>
    <li><strong>Three sample chapters</strong> — Chapter 5 (<em>Qi: The Breath of the Dragon</em>), Chapter 18 (<em>Xuan Kong Flying Stars: Feng Shui in Motion</em>), and Chapter 31 (<em>The Bedroom: Rest, Love, and Restoration</em>) — drafted to demonstrate the book's range across foundational, advanced, and practical chapters.</li>
    <li><strong>The full outline and development plan</strong> — the structure of the planned 47-chapter, nine-part book, with positioning, voice guidance, and production specifications.</li>
  </ol>
  <p>Chapter numbers reflect each chapter's place in the planned structure rather than the order of writing.</p>
</section>
"""


def part_break(title: str) -> str:
    return f'<section class="part-break"><div class="part-title">{title}</div></section>'


def build_html() -> str:
    parts: list[str] = [TITLE_PAGE, NOTE_PAGE, part_break("Sample Chapters")]
    for path in CHAPTERS:
        md_text = strip_dev_note(path.read_text(encoding="utf-8"))
        parts.append(f'<section class="chapter">{md_to_html(md_text)}</section>')
    parts.append(part_break("Outline &amp; Development Plan"))
    outline_text = strip_outline_header(OUTLINE.read_text(encoding="utf-8"))
    parts.append(f'<section class="outline">{md_to_html(outline_text)}</section>')

    body = "\n".join(parts)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        "<title>Wind &amp; Water — The Complete Feng Shui Compendium</title>"
        f"</head><body>\n{body}\n</body></html>"
    )


CSS_TEXT = """
@page {
    size: 6in 9in;
    margin: 0.85in 0.7in 0.95in;
    @bottom-center {
        content: counter(page);
        font-family: "Noto Serif", "Noto Serif CJK SC", serif;
        font-size: 9pt;
        color: #6b5b40;
    }
    @top-center {
        content: "Wind & Water";
        font-family: "Noto Serif", "Noto Serif CJK SC", serif;
        font-style: italic;
        font-size: 9pt;
        color: #b09060;
    }
}
@page title-page  { margin: 0; @top-center { content: none; } @bottom-center { content: none; } background: #1b1408; }
@page note-page   { @top-center { content: none; } @bottom-center { content: none; } }
@page part-break  { margin: 0; @top-center { content: none; } @bottom-center { content: none; } background: #f5ecd9; }
@page outline-page{ @top-center { content: "Wind & Water · Outline & Development Plan"; } }

html, body {
    font-family: "Noto Serif", "Noto Serif CJK SC", "DejaVu Serif", serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #2b2620;
    text-align: justify;
    hyphens: auto;
}

/* TITLE PAGE -------------------------------------------------------------- */
.title-page {
    page: title-page;
    page-break-after: always;
    color: #f5ecd9;
    text-align: center;
    height: 9in;
    width: 6in;
    box-sizing: border-box;
    padding: 1.3in 0.7in 1in;
    margin: 0;
    background: #1b1408;
}
.title-page .imprint {
    font-size: 9pt;
    letter-spacing: 0.22em;
    color: #b09060;
}
.title-page .book-title {
    font-size: 64pt;
    font-weight: 400;
    margin: 0.9in 0 0.15in;
    color: #f5ecd9;
    line-height: 1;
}
.title-page .ornament {
    color: #b09060;
    font-size: 16pt;
    letter-spacing: 0.18em;
    margin: 0.1in 0 0.4in;
}
.title-page .book-subtitle {
    font-size: 12pt;
    font-weight: 400;
    letter-spacing: 0.22em;
    color: #b09060;
    margin: 0 0 0.25in;
}
.title-page .strapline {
    font-size: 11pt;
    color: #d9c79d;
    font-style: italic;
    margin: 0;
}
.title-page .author {
    font-size: 20pt;
    color: #f5ecd9;
    font-style: italic;
    margin-top: 1.1in;
}
.title-page .foreword-by {
    font-size: 9pt;
    letter-spacing: 0.22em;
    color: #b09060;
    margin-top: 0.12in;
}
.title-page .title-footer {
    position: absolute;
    bottom: 0.75in;
    left: 0; right: 0;
    color: #b09060;
    font-size: 9pt;
    letter-spacing: 0.22em;
}
.title-page .title-footer .small { font-size: 7.5pt; letter-spacing: 0.18em; color: #8a6e3b; font-style: italic; text-transform: none; }

/* NOTE PAGE --------------------------------------------------------------- */
.note-page { page: note-page; page-break-after: always; }
.note-page h2 {
    font-weight: 400;
    font-style: italic;
    text-align: center;
    margin: 0.6in 0 0.4in;
    font-size: 20pt;
    color: #6b4a1a;
}
.note-page p { text-align: justify; }
.note-page ol { padding-left: 0.3in; }
.note-page li { margin-bottom: 0.12in; text-align: justify; }

/* PART BREAK PAGE --------------------------------------------------------- */
.part-break {
    page: part-break;
    page-break-after: always;
    height: 9in;
    box-sizing: border-box;
    padding-top: 3.6in;
    text-align: center;
    background: #f5ecd9;
}
.part-title {
    font-style: italic;
    font-size: 30pt;
    color: #6b4a1a;
    letter-spacing: 0.05em;
}

/* CHAPTERS ---------------------------------------------------------------- */
.chapter { page-break-before: always; }
.chapter h1 {
    font-weight: 400;
    font-size: 22pt;
    color: #6b4a1a;
    margin: 0.5in 0 0.1in;
    text-align: left;
    page-break-after: avoid;
    line-height: 1.2;
}
.chapter > p:first-of-type {
    font-style: italic;
    color: #8a6e3b;
    margin: 0 0 0.35in;
}
.chapter h3 {
    font-weight: 600;
    font-style: italic;
    font-size: 13pt;
    color: #6b4a1a;
    margin: 0.32in 0 0.08in;
    page-break-after: avoid;
}
.chapter p { margin: 0.08in 0; }
.chapter blockquote {
    margin: 0.25in 0.25in;
    padding: 0.05in 0 0.05in 0.2in;
    border-left: 2px solid #b09060;
    font-style: italic;
    color: #4a3920;
}
.chapter blockquote h3 {
    font-style: normal;
    color: #6b4a1a;
    margin-top: 0;
    font-size: 12pt;
}
.chapter blockquote p { margin: 0.06in 0; }
.chapter blockquote ol { padding-left: 0.25in; }
.chapter strong { color: #1b1408; font-weight: 600; }
.chapter hr { border: none; border-top: 1px solid #d9c79d; margin: 0.3in 0; }

/* OUTLINE ----------------------------------------------------------------- */
.outline { page: outline-page; page-break-before: always; }
.outline h1 {
    font-weight: 400;
    font-size: 20pt;
    color: #6b4a1a;
    text-align: center;
    margin: 0.3in 0 0.35in;
}
.outline h2 {
    font-weight: 600;
    font-size: 14pt;
    color: #6b4a1a;
    margin-top: 0.32in;
    page-break-after: avoid;
}
.outline h3 {
    font-weight: 600;
    font-size: 11.5pt;
    color: #4a3920;
    margin-top: 0.22in;
    page-break-after: avoid;
}
.outline p, .outline li { font-size: 10pt; }
.outline ul, .outline ol { padding-left: 0.28in; }
.outline table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    margin: 0.12in 0;
}
.outline th, .outline td {
    border: 1px solid #d9c79d;
    padding: 4pt 6pt;
    vertical-align: top;
    text-align: left;
}
.outline th { background: #f5ecd9; font-weight: 600; color: #4a3920; }
.outline blockquote {
    margin: 0.15in 0.2in;
    padding-left: 0.15in;
    border-left: 2px solid #b09060;
    color: #4a3920;
    font-style: italic;
    font-size: 10pt;
}
.outline strong { color: #1b1408; }
.outline em { color: inherit; }
.outline hr { border: none; border-top: 1px solid #d9c79d; margin: 0.22in 0; }

/* GENERAL ----------------------------------------------------------------- */
em { color: inherit; }
strong { color: inherit; }
"""


def main() -> None:
    html = build_html()
    OUT_HTML.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(ROOT)).write_pdf(
        str(OUT_PDF),
        stylesheets=[CSS(string=CSS_TEXT)],
    )
    print(f"wrote HTML: {OUT_HTML}  ({OUT_HTML.stat().st_size:,} bytes)")
    print(f"wrote PDF:  {OUT_PDF}  ({OUT_PDF.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
