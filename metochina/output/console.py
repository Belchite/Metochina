"""Console output with ANSI colors — cybersecurity OSINT aesthetic.

Pure ANSI escape-code formatting — no external dependencies like Rich.
Designed to work in Windows Terminal, macOS Terminal, and Linux terminals.
Uses Unicode box-drawing characters and block elements for a professional look.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from metochina.analysis.analyzer import (
    PrivacyRisk,
    assess_batch_patterns,
    assess_privacy_risks,
    compute_privacy_score,
)
from metochina.models.metadata import BatchReport, ImageMetadata

# ══════════════════════════════════════════════════════════════════════════════
# ANSI ESCAPE CODES
# ══════════════════════════════════════════════════════════════════════════════

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"

BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_CYAN = "\033[46m"

# Enable ANSI on Windows
if sys.platform == "win32":
    os.system("")  # noqa: S605 — triggers Windows ANSI VT processing

# ══════════════════════════════════════════════════════════════════════════════
# BOX-DRAWING CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

BOX_W = 74  # total width including border chars
INNER_W = BOX_W - 2  # content area inside ║ ... ║

# ══════════════════════════════════════════════════════════════════════════════
# ASCII ART BANNER
# ══════════════════════════════════════════════════════════════════════════════

BANNER = r"""
 ███╗   ███╗███████╗████████╗ ██████╗  ██████╗██╗  ██╗██╗███╗   ██╗ █████╗
 ████╗ ████║██╔════╝╚══██╔══╝██╔═══██╗██╔════╝██║  ██║██║████╗  ██║██╔══██╗
 ██╔████╔██║█████╗     ██║   ██║   ██║██║     ███████║██║██╔██╗ ██║███████║
 ██║╚██╔╝██║██╔══╝     ██║   ██║   ██║██║     ██╔══██║██║██║╚██╗██║██╔══██║
 ██║ ╚═╝ ██║███████╗   ██║   ╚██████╔╝╚██████╗██║  ██║██║██║ ╚████║██║  ██║
 ╚═╝     ╚═╝╚══════╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
"""

TAGLINE = "OSINT Image Metadata Analyzer"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def _color_enabled() -> bool:
    """Check if terminal supports colors."""
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Wrap text with ANSI color code if colors are enabled."""
    if not _color_enabled():
        return text
    return f"{code}{text}{RESET}"


def _strip_ansi(text: str) -> str:
    """Return visible length of text by stripping ANSI codes."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _visible_len(text: str) -> int:
    return len(_strip_ansi(text))


# ── Box-drawing primitives ────────────────────────────────────────────────────


def _box_top() -> str:
    return _c(CYAN, "╔" + "═" * INNER_W + "╗")


def _box_bottom() -> str:
    return _c(CYAN, "╚" + "═" * INNER_W + "╝")


def _box_divider() -> str:
    return _c(CYAN, "╟" + "─" * INNER_W + "╢")


def _box_double_divider() -> str:
    return _c(CYAN, "╠" + "═" * INNER_W + "╣")


def _box_line(content: str, align: str = "left") -> str:
    """Render a line inside the box: ║ content ║"""
    vis = _visible_len(content)
    pad_total = INNER_W - 2 - vis  # 2 for leading/trailing space
    if pad_total < 0:
        pad_total = 0
    if align == "center":
        left_pad = pad_total // 2
        right_pad = pad_total - left_pad
        inner = " " * (left_pad + 1) + content + " " * (right_pad + 1)
    else:
        inner = " " + content + " " * (pad_total + 1)
    return _c(CYAN, "║") + inner + _c(CYAN, "║")


def _box_empty() -> str:
    return _c(CYAN, "║") + " " * INNER_W + _c(CYAN, "║")


def _section_header(icon: str, title: str) -> str:
    """Section header inside the box with icon."""
    header_text = _c(BOLD + CYAN, f" {icon}  {title} ")
    vis = _visible_len(header_text)
    remaining = INNER_W - 2 - vis
    if remaining < 0:
        remaining = 0
    left_bar = _c(GRAY, "──")
    right_bar = _c(GRAY, "─" * remaining)
    inner = " " + left_bar + header_text + right_bar + " "
    # Recalculate to fit
    vis_inner = _visible_len(inner)
    if vis_inner < INNER_W:
        inner += " " * (INNER_W - vis_inner)
    return _c(CYAN, "║") + inner[:INNER_W + (len(inner) - vis_inner)] + _c(CYAN, "║")


def _kv(key: str, value: Optional[str], indent: int = 6) -> str:
    """Format a key-value pair inside the box."""
    pad = " " * indent
    if value is None:
        content = f"{pad}{_c(GRAY, key + ':')}  {_c(DIM, '—')}"
    else:
        content = f"{pad}{_c(WHITE + BOLD, key + ':')}  {value}"
    return _box_line(content)


def _threat_indicator(level: str) -> str:
    """Return colored threat level circle indicator."""
    if level == "HIGH":
        return _c(RED + BOLD, "\U0001f534 HIGH")
    elif level == "MEDIUM":
        return _c(YELLOW + BOLD, "\U0001f7e1 MEDIUM")
    return _c(GREEN, "\U0001f7e2 LOW")


def _risk_icon(level: str) -> str:
    if level == "HIGH":
        return "\U0001f534"
    elif level == "MEDIUM":
        return "\U0001f7e1"
    return "\U0001f7e2"


def _progress_bar(score: int, width: int = 30) -> str:
    """Render a Unicode block progress bar for privacy score."""
    filled = int((score / 100) * width)
    partial = 0
    remaining = width - filled

    if score >= 70:
        color = RED + BOLD
        label_color = RED + BOLD
        threat = "HIGH"
    elif score >= 40:
        color = YELLOW
        label_color = YELLOW + BOLD
        threat = "MEDIUM"
    else:
        color = GREEN
        label_color = GREEN + BOLD
        threat = "LOW"

    bar_filled = _c(color, "\u2588" * filled)
    bar_partial = ""
    bar_empty = _c(GRAY, "\u2591" * remaining)
    bar = f"{bar_filled}{bar_partial}{bar_empty}"
    label = _c(label_color, f" {score}/100")
    threat_label = _threat_indicator(threat)

    return f"  \u2590{bar}\u258c{label}  {threat_label}"


def _print_banner(subtitle: str = TAGLINE) -> None:
    """Print the large ASCII art banner."""
    print()
    for line in BANNER.strip().split("\n"):
        print(_c(MAGENTA + BOLD, line))
    print()
    centered = subtitle.center(74)
    print(_c(DIM + WHITE, centered))
    print()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════


def print_metadata(
    meta: ImageMetadata,
    verbose: bool = False,
    show_risks: bool = True,
) -> None:
    """Print metadata for a single image to stdout."""

    # ── Banner ────────────────────────────────────────────────────────────
    _print_banner("OSINT Image Metadata Analyzer")

    print(_box_top())
    print(_box_line(
        _c(BOLD + WHITE, "TARGET: ") + _c(CYAN, meta.filename or "unknown"),
        align="center",
    ))
    print(_box_double_divider())

    # ── GPS LOCATION ──────────────────────────────────────────────────────
    if meta.has_gps:
        print(_section_header("\U0001f4cd", "GPS LOCATION"))
        print(_box_empty())
        lat_str = _c(GREEN + BOLD + UNDERLINE, str(meta.gps.latitude))
        lon_str = _c(GREEN + BOLD + UNDERLINE, str(meta.gps.longitude))
        print(_kv("Latitude", lat_str))
        print(_kv("Longitude", lon_str))
        if meta.gps.altitude is not None:
            print(_kv("Altitude", f"{meta.gps.altitude}m {meta.gps.altitude_ref or ''}".strip()))
        if meta.gps.speed is not None:
            print(_kv("Speed", f"{meta.gps.speed} {meta.gps.speed_ref or ''}".strip()))
        if meta.gps.direction is not None:
            print(_kv("Direction", f"{meta.gps.direction} {meta.gps.direction_ref or ''}".strip()))
        if meta.gps.timestamp:
            print(_kv("GPS Timestamp", meta.gps.timestamp))
        if meta.gps.datum:
            print(_kv("Datum", meta.gps.datum))
        print(_box_empty())
        if meta.gps.google_maps_url:
            print(_box_line(
                f"      {_c(GREEN, '\U0001f310 Google Maps :')} {_c(UNDERLINE + CYAN, meta.gps.google_maps_url)}"
            ))
        if meta.gps.osm_url:
            print(_box_line(
                f"      {_c(GREEN, '\U0001f5fa  OpenStreetMap:')} {_c(UNDERLINE + CYAN, meta.gps.osm_url)}"
            ))
        print(_box_divider())

    # ── FILE INFO ─────────────────────────────────────────────────────────
    print(_section_header("\U0001f4c4", "FILE INFO"))
    print(_box_empty())
    print(_kv("Filename", meta.filename))
    print(_kv("Path", meta.filepath))
    print(_kv("Size", meta.file_size_human))
    print(_kv("Format", meta.file_format))
    print(_kv("MIME Type", meta.mime_type))
    print(_kv("Resolution", meta.resolution))
    print(_kv("Megapixels", str(meta.megapixels) if meta.megapixels else None))
    print(_kv("Color Mode", meta.color_mode))
    if meta.bit_depth:
        print(_kv("Bit Depth", str(meta.bit_depth)))
    print(_box_divider())

    # ── INTEGRITY HASHES ──────────────────────────────────────────────────
    if meta.md5 or meta.sha256:
        print(_section_header("\U0001f512", "INTEGRITY HASHES"))
        print(_box_empty())
        print(_kv("MD5", _c(CYAN, meta.md5 or "\u2014")))
        print(_kv("SHA-256", _c(CYAN, meta.sha256 or "\u2014")))
        print(_box_divider())

    # ── TIMESTAMPS ────────────────────────────────────────────────────────
    if meta.date_taken or meta.date_modified or meta.date_digitized:
        print(_section_header("\u23f1", "TIMESTAMPS"))
        print(_box_empty())
        print(_kv("Date Taken", meta.date_taken))
        print(_kv("Date Modified", meta.date_modified))
        print(_kv("Date Digitized", meta.date_digitized))
        print(_box_divider())

    # ── CAMERA / DEVICE ───────────────────────────────────────────────────
    cam = meta.camera.to_dict()
    if cam:
        print(_section_header("\U0001f4f7", "CAMERA / DEVICE"))
        print(_box_empty())
        for key, val in cam.items():
            label = key.replace("_", " ").title()
            print(_kv(label, str(val)))
        print(_box_divider())

    # ── SOFTWARE ──────────────────────────────────────────────────────────
    sw = meta.software.to_dict()
    if sw:
        print(_section_header("\U0001f4bb", "SOFTWARE"))
        print(_box_empty())
        for key, val in sw.items():
            label = key.replace("_", " ").title()
            val_str = str(val)
            if key == "was_edited" and val:
                val_str = _c(YELLOW + BOLD, "\u26a0 Yes \u2014 image appears edited")
            elif key == "was_edited":
                val_str = _c(GREEN, "No")
            print(_kv(label, val_str))
        print(_box_divider())

    # ── PRIVACY RISK ASSESSMENT ───────────────────────────────────────────
    if show_risks:
        risks = assess_privacy_risks(meta)
        score = compute_privacy_score(risks)

        print(_section_header("\U0001f6e1", "PRIVACY RISK ASSESSMENT"))
        print(_box_empty())
        print(_box_line(_c(BOLD + WHITE, "      Privacy Exposure Score:")))
        print(_box_line(_progress_bar(score)))
        print(_box_empty())

        if risks:
            for risk in risks:
                icon = _risk_icon(risk.level)
                if risk.level == "HIGH":
                    level_c = _c(RED + BOLD, risk.level)
                elif risk.level == "MEDIUM":
                    level_c = _c(YELLOW + BOLD, risk.level)
                else:
                    level_c = _c(GRAY, risk.level)
                print(_box_line(
                    f"      {icon} {level_c}  {_c(DIM, '\u2502')} {_c(WHITE, risk.category)}"
                ))
                print(_box_line(
                    f"           {_c(WHITE, risk.description)}"
                ))
                print(_box_line(
                    f"           {_c(DIM + ITALIC, '\u2192 ' + risk.recommendation)}"
                ))
                print(_box_empty())
        else:
            print(_box_line(
                _c(GREEN + BOLD, "      \u2714 No significant privacy risks detected.")
            ))
            print(_box_empty())

        print(_box_divider())

    # ── RAW EXIF (verbose) ────────────────────────────────────────────────
    if verbose and meta.raw_exif:
        print(_section_header("\U0001f50e", f"RAW EXIF ({meta.raw_exif_count} fields)"))
        print(_box_empty())
        for key, val in sorted(meta.raw_exif.items()):
            val_str = str(val)
            if len(val_str) > 80:
                val_str = val_str[:80] + _c(DIM, "...")
            print(_kv(key, _c(GRAY, val_str)))
        print(_box_divider())

    # ── WARNINGS ──────────────────────────────────────────────────────────
    if meta.warnings:
        print(_section_header("\u26a0", "WARNINGS"))
        print(_box_empty())
        for w in meta.warnings:
            print(_box_line(f"      {_c(YELLOW + BOLD, '\u26a0')}  {_c(YELLOW, w)}"))
        print(_box_empty())

    # ── Footer ────────────────────────────────────────────────────────────
    print(_box_bottom())
    print()


def print_batch_report(
    report: BatchReport,
    verbose: bool = False,
) -> None:
    """Print a batch analysis report to stdout."""

    # ── Banner ────────────────────────────────────────────────────────────
    _print_banner("Batch Analysis Report")

    print(_box_top())
    print(_box_line(
        _c(BOLD + WHITE, f"BATCH SCAN  \u00b7  {report.total_files} file(s) analyzed"),
        align="center",
    ))
    print(_box_double_divider())

    # ── SUMMARY ───────────────────────────────────────────────────────────
    print(_section_header("\U0001f4ca", "SUMMARY"))
    print(_box_empty())

    # Mini-table for summary stats
    col1_w = 22
    col2_w = 40

    def _table_row(label: str, value: str) -> str:
        label_colored = _c(WHITE + BOLD, label)
        vis_label = _visible_len(label_colored)
        pad_label = col1_w - _visible_len(label)
        return f"      {label_colored}{' ' * pad_label} {_c(DIM, '\u2502')} {value}"

    print(_box_line(
        f"      {_c(UNDERLINE + GRAY, ' ' * col1_w)} {_c(DIM, '\u2502')} {_c(UNDERLINE + GRAY, ' ' * col2_w)}"
    ))
    print(_box_line(_table_row("Total Files", str(report.total_files))))
    print(_box_line(_table_row("Files with EXIF", str(report.files_with_exif))))
    gps_val = str(report.files_with_gps)
    if report.files_with_gps:
        gps_val = _c(GREEN + BOLD, f"\U0001f4cd {report.files_with_gps}")
    print(_box_line(_table_row("Files with GPS", gps_val)))
    print(_box_line(_table_row("Files Edited", str(report.files_edited))))
    print(_box_line(_table_row(
        "Unique Cameras",
        ", ".join(report.unique_cameras) if report.unique_cameras else _c(DIM, "\u2014"),
    )))
    print(_box_line(_table_row(
        "Unique Software",
        ", ".join(report.unique_software) if report.unique_software else _c(DIM, "\u2014"),
    )))
    print(_box_line(_table_row("Elapsed", _c(CYAN, f"{report.elapsed_seconds:.2f}s"))))
    print(_box_empty())
    print(_box_divider())

    # ── PATTERNS DETECTED ─────────────────────────────────────────────────
    patterns = assess_batch_patterns(report)
    if patterns:
        print(_section_header("\U0001f50d", "PATTERNS DETECTED"))
        print(_box_empty())
        for p in patterns:
            print(_box_line(f"      {_c(CYAN + BOLD, '\u25b8')} {_c(WHITE, p)}"))
        print(_box_empty())
        print(_box_divider())

    # ── IMAGES ────────────────────────────────────────────────────────────
    print(_section_header("\U0001f5bc", "IMAGES"))
    print(_box_empty())

    # Table header
    idx_w = 4
    name_w = 30
    flags_w = 28
    header_line = (
        f"      {_c(UNDERLINE + BOLD + WHITE, '#'.ljust(idx_w))}"
        f"{_c(UNDERLINE + BOLD + WHITE, 'Filename'.ljust(name_w))}"
        f"{_c(UNDERLINE + BOLD + WHITE, 'Flags'.ljust(flags_w))}"
    )
    print(_box_line(header_line))

    for i, img in enumerate(report.images, 1):
        # Build flags
        flags = []
        if img.has_gps:
            flags.append(_c(GREEN + BOLD, "\U0001f4cdGPS"))
        if img.software.was_edited:
            flags.append(_c(YELLOW + BOLD, "\u270fEDIT"))
        if not img.has_exif:
            flags.append(_c(RED + BOLD, "\u26d4NOEXIF"))

        idx_str = _c(DIM, str(i).rjust(3) + ".")
        fname = img.filename or "unknown"
        if len(fname) > name_w - 2:
            fname = fname[: name_w - 5] + "..."
        fname_str = _c(WHITE, fname.ljust(name_w - 1))
        flags_str = " ".join(flags) if flags else _c(DIM, "\u2014")

        print(_box_line(f"     {idx_str} {fname_str} {flags_str}"))

        if verbose:
            details = []
            if img.camera.make or img.camera.model:
                cam = " ".join(filter(None, [img.camera.make, img.camera.model]))
                details.append(f"{_c(GRAY, '\U0001f4f7')} {_c(DIM, cam)}")
            if img.date_taken:
                details.append(f"{_c(GRAY, '\u23f1')} {_c(DIM, img.date_taken)}")
            if img.has_gps:
                coord = f"{img.gps.latitude}, {img.gps.longitude}"
                details.append(f"{_c(GRAY, '\U0001f4cd')} {_c(GREEN, coord)}")
                if img.gps.google_maps_url:
                    details.append(f"          {_c(UNDERLINE + CYAN, img.gps.google_maps_url)}")
            if details:
                for d in details:
                    print(_box_line(f"           {d}"))

    print(_box_empty())

    # ── Footer ────────────────────────────────────────────────────────────
    print(_box_bottom())
    print()
