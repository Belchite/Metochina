"""Export metadata to JSON, CSV, and self-contained HTML reports."""

from __future__ import annotations

import csv
import html as html_mod
import json
import logging
from typing import List, Union

from metochina.analysis.analyzer import (
    PrivacyRisk,
    assess_batch_patterns,
    assess_privacy_risks,
    compute_privacy_score,
)
from metochina.models.metadata import BatchReport, ImageMetadata

logger = logging.getLogger(__name__)


# ── JSON ────────────────────────────────────────────────────────────────────


def export_json(data: Union[ImageMetadata, BatchReport], path: str) -> None:
    """Export metadata or batch report to a JSON file."""
    if isinstance(data, ImageMetadata):
        payload = data.to_dict()
        risks = assess_privacy_risks(data)
        payload["privacy_risks"] = [r.to_dict() for r in risks]
        payload["privacy_score"] = compute_privacy_score(risks)
    elif isinstance(data, BatchReport):
        payload = {
            "summary": data.summary(),
            "patterns": assess_batch_patterns(data),
            "images": [],
        }
        for img in data.images:
            img_dict = img.to_dict()
            risks = assess_privacy_risks(img)
            img_dict["privacy_risks"] = [r.to_dict() for r in risks]
            img_dict["privacy_score"] = compute_privacy_score(risks)
            payload["images"].append(img_dict)
    else:
        payload = {}

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    logger.info("JSON exported to %s", path)


# ── CSV ─────────────────────────────────────────────────────────────────────


def export_csv(report: BatchReport, path: str) -> None:
    """Export a batch report to CSV (one row per image)."""
    if not report.images:
        logger.warning("No images to export to CSV")
        return

    rows = [img.to_row() for img in report.images]
    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("CSV exported to %s", path)


# ── HTML ────────────────────────────────────────────────────────────────────

_CSS = """
/* ── Reset & Base ───────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html {
    scroll-behavior: smooth;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
    background: linear-gradient(145deg, #0a0e17 0%, #131a2b 50%, #0a0e17 100%);
    background-attachment: fixed;
    color: #c9d1d9;
    margin: 0;
    padding: 24px 16px;
    line-height: 1.7;
    min-height: 100vh;
}

/* ── Container ──────────────────────────────────────────────────── */
.container {
    max-width: 1080px;
    margin: 0 auto;
}

/* ── Fade-in animation ──────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 6px currentColor; }
    50%      { box-shadow: 0 0 18px currentColor; }
}

@keyframes subtleGlow {
    0%, 100% { text-shadow: 0 0 4px rgba(88,166,255,0.3); }
    50%      { text-shadow: 0 0 12px rgba(88,166,255,0.6); }
}

@keyframes donutFill {
    from { stroke-dashoffset: 314.16; }
}

.fade-section {
    animation: fadeInUp 0.6s ease-out both;
}
.fade-section:nth-child(2) { animation-delay: 0.1s; }
.fade-section:nth-child(3) { animation-delay: 0.2s; }
.fade-section:nth-child(4) { animation-delay: 0.3s; }
.fade-section:nth-child(5) { animation-delay: 0.4s; }
.fade-section:nth-child(6) { animation-delay: 0.5s; }

/* ── Cards (glassmorphism) ──────────────────────────────────────── */
.card {
    background: rgba(22, 27, 34, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(88, 166, 255, 0.12);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(88, 166, 255, 0.06);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
    border-color: rgba(88, 166, 255, 0.25);
    box-shadow: 0 4px 40px rgba(0, 0, 0, 0.4),
                0 0 20px rgba(88, 166, 255, 0.05),
                inset 0 1px 0 rgba(88, 166, 255, 0.1);
}

/* ── Typography ─────────────────────────────────────────────────── */
h1 {
    color: #58a6ff;
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
    line-height: 1.2;
}
.report-subtitle {
    color: #8b949e;
    font-size: 15px;
    margin-bottom: 32px;
}
h2 {
    color: #79c0ff;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}
h2 .section-icon {
    font-size: 20px;
}
h3 {
    color: #d2a8ff;
    font-size: 17px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 12px;
}

/* ── Donut Score Gauge ──────────────────────────────────────────── */
.donut-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 20px 0;
}
.donut-wrapper {
    position: relative;
    width: 180px;
    height: 180px;
}
.donut-svg {
    transform: rotate(-90deg);
    width: 180px;
    height: 180px;
}
.donut-track {
    fill: none;
    stroke: #21262d;
    stroke-width: 14;
}
.donut-fill {
    fill: none;
    stroke-width: 14;
    stroke-linecap: round;
    stroke-dasharray: 314.16;
    animation: donutFill 1.5s ease-out forwards;
}
.donut-fill-low    { stroke: #3fb950; }
.donut-fill-medium { stroke: #d29922; }
.donut-fill-high   { stroke: #f85149; }
.donut-label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
}
.donut-score {
    font-size: 42px;
    font-weight: 800;
    line-height: 1;
}
.donut-score-low    { color: #3fb950; }
.donut-score-medium { color: #d29922; }
.donut-score-high   { color: #f85149; }
.donut-max {
    font-size: 13px;
    color: #484f58;
    display: block;
    margin-top: 2px;
}
.donut-caption {
    font-size: 14px;
    color: #8b949e;
    margin-top: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Mini donut (batch per-image) ───────────────────────────────── */
.donut-mini-wrapper {
    position: relative;
    width: 72px;
    height: 72px;
    display: inline-block;
    vertical-align: middle;
    margin-right: 12px;
}
.donut-mini-svg {
    transform: rotate(-90deg);
    width: 72px;
    height: 72px;
}
.donut-mini-track {
    fill: none;
    stroke: #21262d;
    stroke-width: 6;
}
.donut-mini-fill {
    fill: none;
    stroke-width: 6;
    stroke-linecap: round;
    stroke-dasharray: 138.23;
    animation: donutFillMini 1.2s ease-out forwards;
}
@keyframes donutFillMini {
    from { stroke-dashoffset: 138.23; }
}
.donut-mini-label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 16px;
    font-weight: 800;
}

/* ── Tables ─────────────────────────────────────────────────────── */
.table-wrap {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid rgba(88, 166, 255, 0.1);
}
table {
    width: 100%;
    border-collapse: collapse;
}
th {
    background: rgba(22, 27, 34, 0.9);
    color: #58a6ff;
    text-align: left;
    padding: 14px 16px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 2px solid #30363d;
    position: sticky;
    top: 0;
}
td {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(48, 54, 61, 0.5);
    font-size: 14px;
}
tr:nth-child(even) td { background: rgba(22, 27, 34, 0.3); }
tr:hover td { background: rgba(88, 166, 255, 0.06); }
tr { transition: background 0.2s ease; }

/* ── Risk badges (pill + glow) ──────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    white-space: nowrap;
}
.badge-high {
    background: rgba(248, 81, 73, 0.15);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.4);
    animation: pulseGlow 2s ease-in-out infinite;
}
.badge-medium {
    background: rgba(210, 153, 34, 0.15);
    color: #d29922;
    border: 1px solid rgba(210, 153, 34, 0.35);
    box-shadow: 0 0 8px rgba(210, 153, 34, 0.2);
}
.badge-low {
    background: rgba(63, 185, 80, 0.12);
    color: #3fb950;
    border: 1px solid rgba(63, 185, 80, 0.3);
    box-shadow: 0 0 6px rgba(63, 185, 80, 0.15);
}

/* ── GPS Section ────────────────────────────────────────────────── */
.gps-coords {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}
.coord-card {
    background: rgba(13, 17, 23, 0.7);
    border: 1px solid rgba(88, 166, 255, 0.15);
    border-radius: 12px;
    padding: 16px 20px;
    flex: 1;
    min-width: 200px;
}
.coord-label {
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 4px;
}
.coord-value {
    font-size: 22px;
    font-weight: 700;
    font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
    animation: subtleGlow 3s ease-in-out infinite;
    color: #58a6ff;
}
.copy-btn {
    background: rgba(88, 166, 255, 0.1);
    border: 1px solid rgba(88, 166, 255, 0.25);
    color: #58a6ff;
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 11px;
    margin-top: 8px;
    display: inline-block;
    transition: all 0.2s ease;
}
.copy-btn:hover {
    background: rgba(88, 166, 255, 0.2);
    border-color: #58a6ff;
}
.map-frame {
    width: 100%;
    height: 400px;
    border: 1px solid rgba(88, 166, 255, 0.15);
    border-radius: 12px;
    margin: 16px 0;
}
.map-frame-batch {
    width: 100%;
    height: 450px;
    border: 1px solid rgba(88, 166, 255, 0.15);
    border-radius: 12px;
    margin: 16px 0;
}
.map-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 12px;
}
.map-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.25s ease;
    border: 1px solid;
}
.map-btn-google {
    background: rgba(66, 133, 244, 0.12);
    color: #79b8ff;
    border-color: rgba(66, 133, 244, 0.3);
}
.map-btn-google:hover {
    background: rgba(66, 133, 244, 0.25);
    border-color: rgba(66, 133, 244, 0.5);
    text-decoration: none;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
}
.map-btn-osm {
    background: rgba(63, 185, 80, 0.12);
    color: #56d364;
    border-color: rgba(63, 185, 80, 0.3);
}
.map-btn-osm:hover {
    background: rgba(63, 185, 80, 0.25);
    border-color: rgba(63, 185, 80, 0.5);
    text-decoration: none;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(63, 185, 80, 0.2);
}

/* ── Metadata grid ──────────────────────────────────────────────── */
.meta-grid {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1px;
    margin: 8px 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(88, 166, 255, 0.1);
}
.meta-key {
    background: rgba(22, 27, 34, 0.7);
    color: #8b949e;
    font-weight: 600;
    font-size: 13px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(48, 54, 61, 0.4);
}
.meta-val {
    background: rgba(13, 17, 23, 0.4);
    color: #c9d1d9;
    font-size: 13px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(48, 54, 61, 0.4);
    word-break: break-all;
}

/* ── Stat cards (batch dashboard) ───────────────────────────────── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 8px;
}
.stat-card {
    background: rgba(22, 27, 34, 0.55);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(88, 166, 255, 0.1);
    border-radius: 14px;
    padding: 22px 18px;
    text-align: center;
    transition: all 0.25s ease;
}
.stat-card:hover {
    border-color: rgba(88, 166, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.stat-icon {
    font-size: 24px;
    margin-bottom: 8px;
    display: block;
}
.stat-number {
    font-size: 36px;
    font-weight: 800;
    color: #e6edf3;
    line-height: 1;
    display: block;
}
.stat-label {
    font-size: 12px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-top: 6px;
    display: block;
}

/* ── Image gallery (batch) ──────────────────────────────────────── */
.image-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 12px 0;
}
.image-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(13, 17, 23, 0.5);
    border: 1px solid rgba(48, 54, 61, 0.4);
    border-radius: 10px;
    transition: all 0.2s ease;
}
.image-item:hover {
    border-color: rgba(88, 166, 255, 0.2);
    background: rgba(13, 17, 23, 0.7);
}
.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-gps      { background: #f85149; box-shadow: 0 0 8px rgba(248, 81, 73, 0.5); }
.dot-edited   { background: #d29922; box-shadow: 0 0 8px rgba(210, 153, 34, 0.5); }
.dot-no-exif  { background: #3fb950; box-shadow: 0 0 8px rgba(63, 185, 80, 0.5); }
.dot-has-exif { background: #8b949e; box-shadow: 0 0 6px rgba(139, 148, 158, 0.3); }
.image-item-name {
    flex: 1;
    font-weight: 600;
    font-size: 14px;
}
.image-item-tag {
    font-size: 11px;
    color: #8b949e;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(139, 148, 158, 0.1);
    border: 1px solid rgba(139, 148, 158, 0.15);
}

/* ── Warnings ───────────────────────────────────────────────────── */
.warning-list {
    list-style: none;
    padding: 0;
}
.warning-list li {
    padding: 10px 16px;
    margin-bottom: 6px;
    background: rgba(210, 153, 34, 0.08);
    border-left: 3px solid #d29922;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
}

/* ── Patterns list ──────────────────────────────────────────────── */
.pattern-list {
    list-style: none;
    padding: 0;
}
.pattern-list li {
    padding: 10px 16px;
    margin-bottom: 6px;
    background: rgba(88, 166, 255, 0.06);
    border-left: 3px solid #58a6ff;
    border-radius: 0 8px 8px 0;
    font-size: 14px;
}

/* ── Legend ──────────────────────────────────────────────────────── */
.legend {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin: 12px 0 4px 0;
    font-size: 12px;
    color: #8b949e;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Footer ─────────────────────────────────────────────────────── */
.footer {
    margin-top: 48px;
    padding: 24px 0;
    border-top: 1px solid rgba(48, 54, 61, 0.5);
    color: #484f58;
    font-size: 13px;
    text-align: center;
    line-height: 1.8;
}
.footer-brand {
    color: #58a6ff;
    font-weight: 700;
}

/* ── Links ──────────────────────────────────────────────────────── */
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Responsive ─────────────────────────────────────────────────── */
@media (max-width: 700px) {
    body { padding: 12px 8px; }
    .card { padding: 18px 16px; border-radius: 12px; }
    h1 { font-size: 26px; }
    .meta-grid { grid-template-columns: 1fr; }
    .stat-grid { grid-template-columns: repeat(2, 1fr); }
    .gps-coords { flex-direction: column; }
    .coord-value { font-size: 17px; }
    .map-frame, .map-frame-batch { height: 260px; }
    .donut-wrapper { width: 140px; height: 140px; }
    .donut-svg { width: 140px; height: 140px; }
    .donut-score { font-size: 32px; }
    table { font-size: 13px; }
    th, td { padding: 8px 10px; }
}

/* ── Print ──────────────────────────────────────────────────────── */
@media print {
    body {
        background: #fff !important;
        color: #1a1a1a !important;
        padding: 0;
    }
    .card {
        background: #fff !important;
        border: 1px solid #ddd !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        break-inside: avoid;
    }
    h1, h2, h3 { color: #1a1a1a !important; }
    .badge { border: 1px solid #999 !important; }
    .badge-high { color: #c00 !important; background: #fee !important; }
    .badge-medium { color: #a60 !important; background: #ffd !important; }
    .badge-low { color: #060 !important; background: #efe !important; }
    .stat-card {
        background: #f8f8f8 !important;
        border: 1px solid #ddd !important;
    }
    .stat-number { color: #1a1a1a !important; }
    .coord-value { color: #1a1a1a !important; animation: none !important; text-shadow: none !important; }
    .donut-fill { animation: none !important; }
    .donut-score { color: #1a1a1a !important; }
    .meta-key { background: #f0f0f0 !important; color: #555 !important; }
    .meta-val { background: #fff !important; color: #1a1a1a !important; }
    th { background: #f0f0f0 !important; color: #1a1a1a !important; }
    td { color: #1a1a1a !important; }
    tr:nth-child(even) td { background: #f8f8f8 !important; }
    .copy-btn { display: none !important; }
    .map-frame, .map-frame-batch { display: none; }
    .footer { color: #999 !important; }
}
"""

_JS_COPY = """
function copyCoord(text, btn) {
    navigator.clipboard.writeText(text).then(function() {
        var orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = 'rgba(63,185,80,0.2)';
        btn.style.borderColor = '#3fb950';
        btn.style.color = '#3fb950';
        setTimeout(function() {
            btn.textContent = orig;
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }, 1500);
    });
}
"""


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html_mod.escape(str(text)) if text else "\u2014"


def _osm_embed_url(lat: float, lon: float) -> str:
    """Generate OpenStreetMap embed iframe URL."""
    bbox = f"{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}"
    return (
        f"https://www.openstreetmap.org/export/embed.html"
        f"?bbox={bbox}&layer=mapnik&marker={lat},{lon}"
    )


def _render_donut(score: int, mini: bool = False) -> str:
    """Render a CSS-only circular gauge for the privacy score."""
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    if mini:
        # Small donut for batch per-image sections
        circumference = 138.23  # 2 * pi * 22
        offset = circumference - (circumference * score / 100)
        return (
            f'<div class="donut-mini-wrapper">'
            f'  <svg class="donut-mini-svg" viewBox="0 0 52 52">'
            f'    <circle class="donut-mini-track" cx="26" cy="26" r="22"/>'
            f'    <circle class="donut-mini-fill donut-fill-{level}" cx="26" cy="26" r="22"'
            f'      style="stroke-dashoffset:{offset}"/>'
            f'  </svg>'
            f'  <div class="donut-mini-label donut-score-{level}">{score}</div>'
            f'</div>'
        )

    # Full-size donut
    circumference = 314.16  # 2 * pi * 50
    offset = circumference - (circumference * score / 100)
    return (
        f'<div class="donut-container">'
        f'  <div class="donut-wrapper">'
        f'    <svg class="donut-svg" viewBox="0 0 120 120">'
        f'      <circle class="donut-track" cx="60" cy="60" r="50"/>'
        f'      <circle class="donut-fill donut-fill-{level}" cx="60" cy="60" r="50"'
        f'        style="stroke-dashoffset:{offset}"/>'
        f'    </svg>'
        f'    <div class="donut-label">'
        f'      <span class="donut-score donut-score-{level}">{score}</span>'
        f'      <span class="donut-max">/ 100</span>'
        f'    </div>'
        f'  </div>'
        f'  <div class="donut-caption">Privacy Exposure Score</div>'
        f'</div>'
    )


def _render_risks_table(risks: List[PrivacyRisk]) -> str:
    """Render risks as an HTML table with pill badges and icons."""
    if not risks:
        return '<p style="color:#3fb950;padding:12px 0;">No significant privacy risks detected.</p>'

    icons = {"HIGH": "\U0001f534", "MEDIUM": "\U0001f7e1", "LOW": "\U0001f7e2"}
    rows = ""
    for r in risks:
        badge_cls = f"badge-{r.level.lower()}"
        icon = icons.get(r.level.upper(), "")
        rows += (
            f"<tr>"
            f'<td><span class="badge {badge_cls}">{icon} {r.level}</span></td>'
            f"<td>{_esc(r.category)}</td>"
            f"<td>{_esc(r.description)}</td>"
            f"<td>{_esc(r.recommendation)}</td>"
            f"</tr>"
        )

    return (
        f'<div class="table-wrap"><table>'
        f"<tr><th>Level</th><th>Category</th><th>Description</th><th>Recommendation</th></tr>"
        f"{rows}"
        f"</table></div>"
    )


def _render_metadata_grid(meta: ImageMetadata) -> str:
    """Render key metadata as an HTML grid."""
    items = [
        ("Filename", meta.filename),
        ("Size", meta.file_size_human),
        ("Format", meta.file_format),
        ("Resolution", meta.resolution),
        ("Megapixels", meta.megapixels),
        ("MD5", meta.md5),
        ("SHA-256", meta.sha256),
        ("Date Taken", meta.date_taken),
        ("Date Modified", meta.date_modified),
    ]

    cam = meta.camera.to_dict()
    for key, val in cam.items():
        items.append((key.replace("_", " ").title(), val))

    sw = meta.software.to_dict()
    for key, val in sw.items():
        items.append((key.replace("_", " ").title(), val))

    grid = '<div class="meta-grid">'
    for key, val in items:
        display = _esc(str(val) if val is not None else "\u2014")
        grid += f'<div class="meta-key">{_esc(key)}</div><div class="meta-val">{display}</div>'
    grid += "</div>"
    return grid


def _render_gps_section(meta: ImageMetadata) -> str:
    """Render the GPS section with coordinate cards, map, and styled buttons."""
    if not meta.has_gps:
        return ""

    lat = meta.gps.latitude
    lon = meta.gps.longitude
    embed = _osm_embed_url(lat, lon)

    html = (
        f'<div class="card fade-section">'
        f'<h2><span class="section-icon">\U0001f4cd</span> GPS Location</h2>'
        f'<div class="gps-coords">'
        # Latitude card
        f'  <div class="coord-card">'
        f'    <div class="coord-label">Latitude</div>'
        f'    <div class="coord-value">{lat}</div>'
        f'    <button class="copy-btn" onclick="copyCoord(\'{lat}\', this)">\U0001f4cb Copy</button>'
        f'  </div>'
        # Longitude card
        f'  <div class="coord-card">'
        f'    <div class="coord-label">Longitude</div>'
        f'    <div class="coord-value">{lon}</div>'
        f'    <button class="copy-btn" onclick="copyCoord(\'{lon}\', this)">\U0001f4cb Copy</button>'
        f'  </div>'
        f'</div>'
        f'<iframe class="map-frame" src="{_esc(embed)}" frameborder="0" loading="lazy"></iframe>'
        f'<div class="map-buttons">'
    )

    if meta.gps.google_maps_url:
        html += (
            f'<a class="map-btn map-btn-google" href="{_esc(meta.gps.google_maps_url)}" '
            f'target="_blank">\U0001f30d Open in Google Maps</a>'
        )
    if meta.gps.osm_url:
        html += (
            f'<a class="map-btn map-btn-osm" href="{_esc(meta.gps.osm_url)}" '
            f'target="_blank">\U0001f5fa Open in OpenStreetMap</a>'
        )

    html += "</div></div>"
    return html


def _get_timestamp() -> str:
    """Return current timestamp string for reports."""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _render_footer() -> str:
    """Render the branded footer with timestamp."""
    ts = _get_timestamp()
    return (
        f'<div class="footer">'
        f'<span class="footer-brand">Metochina</span> &mdash; '
        f'OSINT Image Metadata Analyzer<br>'
        f'Report generated on {ts}'
        f'</div>'
    )


def _render_single_html(meta: ImageMetadata) -> str:
    """Render HTML report for a single image."""
    risks = assess_privacy_risks(meta)
    score = compute_privacy_score(risks)

    body = (
        f'<div class="card fade-section">'
        f'<h1>\U0001f50d Metochina Report</h1>'
        f'<div class="report-subtitle">{_esc(meta.filename)}</div>'
        f'</div>'
    )

    # GPS section (renders its own card)
    body += _render_gps_section(meta)

    # Score section
    body += (
        f'<div class="card fade-section">'
        f'<h2><span class="section-icon">\U0001f6e1</span> Privacy Risk Assessment</h2>'
        f'{_render_donut(score)}'
        f'{_render_risks_table(risks)}'
        f'</div>'
    )

    # Metadata section
    body += (
        f'<div class="card fade-section">'
        f'<h2><span class="section-icon">\U0001f4c4</span> Metadata</h2>'
        f'{_render_metadata_grid(meta)}'
        f'</div>'
    )

    # Warnings
    if meta.warnings:
        items = "".join(f"<li>{_esc(w)}</li>" for w in meta.warnings)
        body += (
            f'<div class="card fade-section">'
            f'<h2><span class="section-icon">\u26a0\ufe0f</span> Warnings</h2>'
            f'<ul class="warning-list">{items}</ul>'
            f'</div>'
        )

    body += _render_footer()
    return body


def _render_batch_html(report: BatchReport) -> str:
    """Render HTML report for a batch of images."""
    body = (
        f'<div class="card fade-section">'
        f'<h1>\U0001f50d Metochina Batch Report</h1>'
        f'<div class="report-subtitle">{report.total_files} images analyzed</div>'
        f'</div>'
    )

    # Summary stat cards
    cameras_str = _esc(", ".join(report.unique_cameras) or "\u2014")
    body += (
        f'<div class="card fade-section">'
        f'<h2><span class="section-icon">\U0001f4ca</span> Summary</h2>'
        f'<div class="stat-grid">'
        # Total files
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\U0001f4c1</span>'
        f'    <span class="stat-number">{report.total_files}</span>'
        f'    <span class="stat-label">Total Files</span>'
        f'  </div>'
        # EXIF
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\U0001f4f7</span>'
        f'    <span class="stat-number">{report.files_with_exif}</span>'
        f'    <span class="stat-label">With EXIF</span>'
        f'  </div>'
        # GPS
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\U0001f4cd</span>'
        f'    <span class="stat-number">{report.files_with_gps}</span>'
        f'    <span class="stat-label">With GPS</span>'
        f'  </div>'
        # Edited
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\u270f\ufe0f</span>'
        f'    <span class="stat-number">{report.files_edited}</span>'
        f'    <span class="stat-label">Edited</span>'
        f'  </div>'
        # Cameras
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\U0001f4f9</span>'
        f'    <span class="stat-number">{len(report.unique_cameras)}</span>'
        f'    <span class="stat-label">Unique Cameras</span>'
        f'  </div>'
        # Elapsed
        f'  <div class="stat-card">'
        f'    <span class="stat-icon">\u23f1\ufe0f</span>'
        f'    <span class="stat-number">{report.elapsed_seconds:.1f}s</span>'
        f'    <span class="stat-label">Elapsed</span>'
        f'  </div>'
        f'</div>'
    )
    if report.unique_cameras:
        body += f'<p style="margin-top:12px;color:#8b949e;font-size:13px;"><strong>Cameras:</strong> {cameras_str}</p>'
    body += '</div>'

    # Patterns
    patterns = assess_batch_patterns(report)
    if patterns:
        items = "".join(f"<li>{_esc(p)}</li>" for p in patterns)
        body += (
            f'<div class="card fade-section">'
            f'<h2><span class="section-icon">\U0001f9e9</span> Patterns Detected</h2>'
            f'<ul class="pattern-list">{items}</ul>'
            f'</div>'
        )

    # GPS Map
    gps_images = report.gps_images
    if gps_images:
        body += f'<div class="card fade-section">'
        body += f'<h2><span class="section-icon">\U0001f5fa</span> GPS Locations</h2>'

        if len(gps_images) == 1:
            img = gps_images[0]
            embed = _osm_embed_url(img.gps.latitude, img.gps.longitude)
            body += f'<iframe class="map-frame-batch" src="{_esc(embed)}" frameborder="0" loading="lazy"></iframe>'
        else:
            lats = [img.gps.latitude for img in gps_images]
            lons = [img.gps.longitude for img in gps_images]
            min_lat, max_lat = min(lats) - 0.01, max(lats) + 0.01
            min_lon, max_lon = min(lons) - 0.01, max(lons) + 0.01
            bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            embed_url = (
                f"https://www.openstreetmap.org/export/embed.html"
                f"?bbox={bbox}&layer=mapnik&marker={center_lat},{center_lon}"
            )
            body += f'<iframe class="map-frame-batch" src="{_esc(embed_url)}" frameborder="0" loading="lazy"></iframe>'

        # GPS points table
        body += f'<h3>GPS Points</h3><div class="table-wrap"><table>'
        body += "<tr><th>#</th><th>File</th><th>Latitude</th><th>Longitude</th><th>Action</th></tr>"
        for i, img in enumerate(gps_images, 1):
            maps_link = (
                f'<a class="map-btn map-btn-google" style="padding:4px 12px;font-size:12px;" '
                f'href="{_esc(img.gps.google_maps_url)}" target="_blank">\U0001f30d Maps</a>'
                if img.gps.google_maps_url
                else "\u2014"
            )
            body += (
                f"<tr><td>{i}</td><td>{_esc(img.filename)}</td>"
                f"<td><code>{img.gps.latitude}</code></td>"
                f"<td><code>{img.gps.longitude}</code></td>"
                f"<td>{maps_link}</td></tr>"
            )
        body += "</table></div></div>"

    # Image gallery / overview
    body += f'<div class="card fade-section">'
    body += f'<h2><span class="section-icon">\U0001f5bc</span> Image Overview</h2>'

    body += (
        '<div class="legend">'
        '<div class="legend-item"><span class="status-dot dot-gps"></span> Has GPS</div>'
        '<div class="legend-item"><span class="status-dot dot-edited"></span> Edited</div>'
        '<div class="legend-item"><span class="status-dot dot-has-exif"></span> Has EXIF</div>'
        '<div class="legend-item"><span class="status-dot dot-no-exif"></span> No EXIF</div>'
        '</div>'
    )

    body += '<div class="image-list">'
    for img in report.images:
        # Determine status dot
        if img.has_gps:
            dot_cls = "dot-gps"
            tag = "GPS"
        elif img.is_edited:
            dot_cls = "dot-edited"
            tag = "Edited"
        elif img.has_exif:
            dot_cls = "dot-has-exif"
            tag = "EXIF"
        else:
            dot_cls = "dot-no-exif"
            tag = "No EXIF"

        body += (
            f'<div class="image-item">'
            f'<span class="status-dot {dot_cls}"></span>'
            f'<span class="image-item-name">{_esc(img.filename)}</span>'
            f'<span class="image-item-tag">{tag}</span>'
            f'</div>'
        )
    body += '</div></div>'

    # Per-image details
    body += f'<div class="card fade-section">'
    body += f'<h2><span class="section-icon">\U0001f50e</span> Image Details</h2>'
    for i, img in enumerate(report.images, 1):
        risks = assess_privacy_risks(img)
        score = compute_privacy_score(risks)

        body += (
            f'<div style="display:flex;align-items:center;margin:24px 0 12px 0;">'
            f'{_render_donut(score, mini=True)}'
            f'<h3 style="margin:0;">{i}. {_esc(img.filename)}</h3>'
            f'</div>'
        )
        body += _render_metadata_grid(img)
        if risks:
            body += _render_risks_table(risks)

    body += '</div>'

    body += _render_footer()
    return body


def export_html(data: Union[ImageMetadata, BatchReport], path: str) -> None:
    """Export a self-contained HTML report.

    Args:
        data: Single image metadata or batch report.
        path: Output file path.
    """
    if isinstance(data, ImageMetadata):
        body_html = _render_single_html(data)
    elif isinstance(data, BatchReport):
        body_html = _render_batch_html(data)
    else:
        body_html = "<p>No data to display.</p>"

    full_html = (
        f"<!DOCTYPE html>\n"
        f"<html lang=\"en\">\n"
        f"<head>\n"
        f"  <meta charset=\"UTF-8\">\n"
        f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"  <title>Metochina Report</title>\n"
        f"  <style>{_CSS}</style>\n"
        f"</head>\n"
        f"<body>\n"
        f"  <div class=\"container\">\n"
        f"    {body_html}\n"
        f"  </div>\n"
        f"  <script>{_JS_COPY}</script>\n"
        f"</body>\n"
        f"</html>"
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(full_html)

    logger.info("HTML report exported to %s", path)
