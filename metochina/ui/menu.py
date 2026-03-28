"""Interactive hacker-style terminal menu for Metochina.

Provides a numbered menu system that wraps the existing CLI functionality
with a visual, Kali Linux-inspired interface.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

from metochina import __version__
from metochina.analysis.analyzer import (
    assess_batch_patterns,
    assess_privacy_risks,
    compute_privacy_score,
)
from metochina.core.extractor import extract_batch, extract_metadata, find_images
from metochina.core.hasher import compute_hashes
from metochina.output.exporters import export_csv, export_html, export_json
from metochina.ui.banner import print_banner, print_startup_sequence
from metochina.ui.display import (
    box_bottom,
    box_divider,
    box_empty,
    box_line,
    box_top,
    critical,
    error,
    info,
    menu_box,
    question,
    result,
    score_bar,
    section_box,
    success,
    warning,
)
from metochina.ui.effects import pause, progress_bar, spinner


# ── Settings ────────────────────────────────────────────────────────────────

class Settings:
    """Runtime settings for the interactive UI."""

    def __init__(self) -> None:
        self.compute_hashes: bool = True
        self.recursive: bool = True
        self.default_export: str = "html"
        self.output_dir: str = os.path.join(".", "reports")


_settings = Settings()


# ── Helpers ─────────────────────────────────────────────────────────────────

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _prompt() -> str:
    """Show the metochina prompt and get input."""
    try:
        return input(f"\n{GREEN}{BOLD}metochina{RESET} {DIM}>{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _ask_path(label: str = "Enter image path") -> Optional[str]:
    """Ask user for a file/directory path."""
    path = question(f"{label}: ")
    if not path:
        error("No path provided.")
        return None
    path = path.strip().strip('"').strip("'")
    return path


def _ask_export(data, filename_base: str = "report") -> None:
    """Ask user if they want to export and do it."""
    choice = question("Export results? (json/html/csv/no): ").lower().strip()
    if choice == "no" or not choice:
        return

    os.makedirs(_settings.output_dir, exist_ok=True)

    if choice in ("json", "html", "csv", "all"):
        formats = [choice] if choice != "all" else ["json", "html", "csv"]
        for fmt in formats:
            path = os.path.join(_settings.output_dir, f"{filename_base}.{fmt}")
            try:
                if fmt == "json":
                    export_json(data, path)
                elif fmt == "html":
                    export_html(data, path)
                elif fmt == "csv":
                    from metochina.models.metadata import BatchReport
                    if isinstance(data, BatchReport):
                        export_csv(data, path)
                    else:
                        warning("CSV export is only available for batch reports.")
                        continue
                success(f"Report saved: {path}")
            except Exception as exc:
                error(f"Export failed: {exc}")
    else:
        warning(f"Unknown format: {choice}")


def _display_metadata(meta) -> None:
    """Display metadata for a single image using section boxes."""

    # File info
    file_items = [
        (">", "Filename", meta.filename),
        (">", "Size", meta.file_size_human),
        (">", "Format", meta.file_format or "Unknown"),
        (">", "Resolution", f"{meta.resolution} ({meta.megapixels} MP)" if meta.resolution else "Unknown"),
        (">", "Color Mode", meta.color_mode or "Unknown"),
    ]
    section_box("FILE INFORMATION", file_items)

    # Hashes
    if meta.md5 or meta.sha256:
        hash_items = [
            ("+", "MD5", meta.md5 or "—"),
            ("+", "SHA-256", meta.sha256 or "—"),
        ]
        section_box("INTEGRITY HASHES", hash_items)

    # GPS
    if meta.has_gps:
        gps_items = [
            ("+", "Latitude", str(meta.gps.latitude)),
            ("+", "Longitude", str(meta.gps.longitude)),
        ]
        if meta.gps.altitude is not None:
            gps_items.append(("+", "Altitude", f"{meta.gps.altitude}m {meta.gps.altitude_ref or ''}".strip()))
        if meta.gps.speed is not None:
            gps_items.append(("+", "Speed", f"{meta.gps.speed} {meta.gps.speed_ref or ''}".strip()))
        if meta.gps.timestamp:
            gps_items.append(("+", "GPS Time", meta.gps.timestamp))
        if meta.gps.google_maps_url:
            gps_items.append(("+", "Google Maps", meta.gps.google_maps_url))
        if meta.gps.osm_url:
            gps_items.append(("+", "OSM", meta.gps.osm_url))
        section_box("\U0001f4cd GPS LOCATION FOUND", gps_items)
    else:
        print()
        error("No GPS data found in this image.")

    # Dates
    if meta.date_taken or meta.date_modified:
        date_items = []
        if meta.date_taken:
            date_items.append((">", "Date Taken", meta.date_taken))
        if meta.date_modified:
            date_items.append((">", "Date Modified", meta.date_modified))
        if meta.date_digitized:
            date_items.append((">", "Date Digitized", meta.date_digitized))
        section_box("TIMESTAMPS", date_items)

    # Camera
    cam = meta.camera.to_dict()
    if cam:
        cam_items = []
        for key, val in cam.items():
            label = key.replace("_", " ").title()
            prefix = "!!" if key == "serial_number" else ">"
            val_str = str(val)
            if key == "serial_number":
                val_str += " (EXPOSED!)"
            cam_items.append((prefix, label, val_str))
        section_box("\U0001f4f8 CAMERA / DEVICE", cam_items)

    # Software
    sw = meta.software.to_dict()
    if sw:
        sw_items = []
        for key, val in sw.items():
            label = key.replace("_", " ").title()
            if key == "was_edited" and val:
                sw_items.append(("!", "Was Edited", "YES — image appears edited"))
            elif key == "was_edited":
                sw_items.append((">", "Was Edited", "No"))
            else:
                sw_items.append((">", label, str(val)))
        section_box("\U0001f4bb SOFTWARE", sw_items)

    # Privacy Risks
    risks = assess_privacy_risks(meta)
    score = compute_privacy_score(risks)

    risk_items = []
    for r in risks:
        if r.level == "HIGH":
            risk_items.append(("!!", f"HIGH    {r.category}", r.description))
        elif r.level == "MEDIUM":
            risk_items.append(("!", f"MEDIUM  {r.category}", r.description))
        else:
            risk_items.append(("*", f"LOW     {r.category}", r.description))

    if risk_items:
        risk_items.append(("", "", ""))
        risk_items.append((">", "Privacy Score", score_bar(score)))
        section_box("\u26a0 PRIVACY RISKS", risk_items)
    else:
        print()
        success("No significant privacy risks detected.")
        print(f"  Privacy Score: {score_bar(score)}")

    # Warnings
    if meta.warnings:
        print()
        for w in meta.warnings:
            warning(w)


# ── Menu Actions ────────────────────────────────────────────────────────────

def _action_scan_image() -> None:
    """[1] Scan a single image."""
    path = _ask_path("Enter image path")
    if not path:
        return
    if not os.path.isfile(path):
        error(f"File not found: {path}")
        return

    spinner("Analyzing image...", duration=1.0)

    meta = extract_metadata(path, skip_hash=not _settings.compute_hashes)
    print()
    _display_metadata(meta)

    _ask_export(meta, os.path.splitext(meta.filename)[0] + "_report")
    pause()


def _action_batch_scan() -> None:
    """[2] Batch scan a directory."""
    path = _ask_path("Enter directory path")
    if not path:
        return
    if not os.path.isdir(path):
        error(f"Directory not found: {path}")
        return

    recursive = _settings.recursive
    ans = question("Include subdirectories? (y/n): ").lower().strip()
    if ans == "n":
        recursive = False
    elif ans == "y":
        recursive = True

    images = find_images(path, recursive=recursive)
    if not images:
        error("No supported images found.")
        return

    info(f"Found {len(images)} image(s). Scanning...")
    print()

    def _on_progress(current: int, total: int, filename: str) -> None:
        bar = progress_bar(current, total, width=30, prefix="  Scanning")
        sys.stdout.write(f"\r{bar}")
        sys.stdout.flush()
        if current == total:
            sys.stdout.write("\n")

    report = extract_batch(images, skip_hash=not _settings.compute_hashes, on_progress=_on_progress)
    print()

    # Summary
    summary_items = [
        (">", "Total Files", str(report.total_files)),
        ("+", "Files with EXIF", str(report.files_with_exif)),
        ("+", "Files with GPS", str(report.files_with_gps)),
        ("!", "Files Edited", str(report.files_edited)),
        (">", "Unique Cameras", ", ".join(report.unique_cameras) if report.unique_cameras else "—"),
        (">", "Elapsed", f"{report.elapsed_seconds:.2f}s"),
    ]
    section_box("BATCH SUMMARY", summary_items)

    # Patterns
    patterns = assess_batch_patterns(report)
    if patterns:
        print()
        info("Patterns detected:")
        for p in patterns:
            result("  Pattern", p)

    # Per-image list
    print()
    for i, img in enumerate(report.images, 1):
        flags = []
        if img.has_gps:
            flags.append(f"{GREEN}GPS{RESET}")
        if img.software.was_edited:
            flags.append(f"{YELLOW}EDIT{RESET}")
        if not img.has_exif:
            flags.append(f"{RED}NO-EXIF{RESET}")
        flags_str = " ".join(f"[{f}]" for f in flags) if flags else ""
        info(f"  {i:3d}. {img.filename}  {flags_str}")

    _ask_export(report, "batch_report")
    pause()


def _action_gps_extract() -> None:
    """[3] Quick GPS extraction."""
    path = _ask_path("Enter image path")
    if not path:
        return
    if not os.path.isfile(path):
        error(f"File not found: {path}")
        return

    spinner("Extracting GPS data...", duration=0.8)

    meta = extract_metadata(path, skip_hash=True)
    print()

    if meta.has_gps:
        gps_items = [
            ("+", "Latitude", str(meta.gps.latitude)),
            ("+", "Longitude", str(meta.gps.longitude)),
        ]
        if meta.gps.altitude is not None:
            gps_items.append(("+", "Altitude", f"{meta.gps.altitude}m {meta.gps.altitude_ref or ''}".strip()))
        if meta.gps.google_maps_url:
            gps_items.append(("+", "Google Maps", meta.gps.google_maps_url))
        if meta.gps.osm_url:
            gps_items.append(("+", "OpenStreetMap", meta.gps.osm_url))
        section_box("\U0001f4cd GPS LOCATION FOUND", gps_items)
    else:
        error("No GPS data found in this image.")

    pause()


def _action_hash_file() -> None:
    """[4] Calculate file hashes."""
    path = _ask_path("Enter file path")
    if not path:
        return
    if not os.path.isfile(path):
        error(f"File not found: {path}")
        return

    spinner("Computing hashes...", duration=0.6)

    md5, sha256 = compute_hashes(path)
    print()
    success(f"MD5:    {md5}")
    success(f"SHA256: {sha256}")

    pause()


def _action_risk_assessment() -> None:
    """[5] Privacy risk assessment."""
    path = _ask_path("Enter image path")
    if not path:
        return
    if not os.path.isfile(path):
        error(f"File not found: {path}")
        return

    spinner("Analyzing risks...", duration=0.8)

    meta = extract_metadata(path, skip_hash=True)
    risks = assess_privacy_risks(meta)
    score = compute_privacy_score(risks)
    print()

    if risks:
        for r in risks:
            if r.level == "HIGH":
                critical(f"HIGH   — {r.description}")
            elif r.level == "MEDIUM":
                warning(f"MEDIUM — {r.description}")
            else:
                info(f"LOW    — {r.description}")
        print()
        print(f"  Privacy Score: {score_bar(score)}")
    else:
        success("No significant privacy risks detected.")
        print(f"  Privacy Score: {score_bar(score)}")

    pause()


def _action_deep_scan() -> None:
    """[6] Deep scan — full analysis + all exports."""
    path = _ask_path("Enter image or directory path")
    if not path:
        return

    os.makedirs(_settings.output_dir, exist_ok=True)

    if os.path.isfile(path):
        spinner("Deep scanning image...", duration=1.2)

        meta = extract_metadata(path, skip_hash=False)
        print()
        _display_metadata(meta)

        base = os.path.splitext(meta.filename)[0]
        # Auto-export JSON + HTML
        json_path = os.path.join(_settings.output_dir, f"{base}_deep.json")
        html_path = os.path.join(_settings.output_dir, f"{base}_deep.html")
        export_json(meta, json_path)
        success(f"JSON saved: {json_path}")
        export_html(meta, html_path)
        success(f"HTML saved: {html_path}")

    elif os.path.isdir(path):
        images = find_images(path, recursive=_settings.recursive)
        if not images:
            error("No supported images found.")
            return

        info(f"Deep scanning {len(images)} image(s)...")
        print()

        def _on_progress(current: int, total: int, filename: str) -> None:
            bar = progress_bar(current, total, width=30, prefix="  Scanning")
            sys.stdout.write(f"\r{bar}")
            sys.stdout.flush()
            if current == total:
                sys.stdout.write("\n")

        report = extract_batch(images, skip_hash=False, on_progress=_on_progress)
        print()

        summary_items = [
            (">", "Total Files", str(report.total_files)),
            ("+", "Files with EXIF", str(report.files_with_exif)),
            ("+", "Files with GPS", str(report.files_with_gps)),
            ("!", "Files Edited", str(report.files_edited)),
            (">", "Elapsed", f"{report.elapsed_seconds:.2f}s"),
        ]
        section_box("DEEP SCAN SUMMARY", summary_items)

        # Auto-export all formats
        json_path = os.path.join(_settings.output_dir, "deep_batch.json")
        html_path = os.path.join(_settings.output_dir, "deep_batch.html")
        csv_path = os.path.join(_settings.output_dir, "deep_batch.csv")
        export_json(report, json_path)
        success(f"JSON saved: {json_path}")
        export_html(report, html_path)
        success(f"HTML saved: {html_path}")
        export_csv(report, csv_path)
        success(f"CSV saved: {csv_path}")
    else:
        error(f"Path not found: {path}")
        return

    pause()


def _action_settings() -> None:
    """[7] Settings submenu."""
    while True:
        print()
        items = [
            ("1", "Toggle hash calculation", f"currently: {'ON' if _settings.compute_hashes else 'OFF'}"),
            ("2", "Toggle recursive scan", f"currently: {'ON' if _settings.recursive else 'OFF'}"),
            ("3", "Set default export format", f"currently: {_settings.default_export.upper()}"),
            ("4", "Set output directory", f"currently: {_settings.output_dir}"),
            ("5", "Back to main menu", ""),
        ]
        menu_box("SETTINGS", items)

        choice = _prompt()

        if choice == "1":
            _settings.compute_hashes = not _settings.compute_hashes
            success(f"Hash calculation: {'ON' if _settings.compute_hashes else 'OFF'}")
        elif choice == "2":
            _settings.recursive = not _settings.recursive
            success(f"Recursive scan: {'ON' if _settings.recursive else 'OFF'}")
        elif choice == "3":
            fmt = question("Enter format (json/html/csv): ").lower().strip()
            if fmt in ("json", "html", "csv"):
                _settings.default_export = fmt
                success(f"Default export format: {fmt.upper()}")
            else:
                error("Invalid format.")
        elif choice == "4":
            d = question("Enter output directory: ").strip()
            if d:
                _settings.output_dir = d
                success(f"Output directory: {d}")
        elif choice == "5" or choice == "":
            break


# ── Main Loop ───────────────────────────────────────────────────────────────

_MAIN_MENU_ITEMS = [
    ("1", "Scan Image", "Analyze a single image"),
    ("2", "Batch Scan", "Analyze entire folder"),
    ("3", "GPS Extract", "Quick GPS extraction"),
    ("4", "Hash File", "Calculate file hashes"),
    ("5", "Risk Assessment", "Privacy risk analysis"),
    ("6", "Deep Scan", "Full scan + all exports"),
    ("7", "Settings", "Configure options"),
    ("0", "Exit", ""),
]

_ACTIONS = {
    "1": _action_scan_image,
    "2": _action_batch_scan,
    "3": _action_gps_extract,
    "4": _action_hash_file,
    "5": _action_risk_assessment,
    "6": _action_deep_scan,
    "7": _action_settings,
}


def run_interactive() -> None:
    """Launch the interactive terminal UI."""
    # Enable ANSI on Windows
    if sys.platform == "win32":
        os.system("")  # noqa: S605

    # Startup sequence
    print_startup_sequence()
    print_banner(version=__version__, author="Belchite")

    while True:
        try:
            menu_box("MAIN MENU", _MAIN_MENU_ITEMS)
            choice = _prompt()

            if choice == "0" or choice.lower() in ("exit", "quit", "q"):
                print()
                info("Thanks for using Metochina. Stay safe.")
                print()
                break
            elif choice in _ACTIONS:
                _ACTIONS[choice]()
            elif choice == "":
                continue
            else:
                error(f"Invalid option: {choice}")

        except KeyboardInterrupt:
            print()
            info("Interrupted. Type 0 to exit or press Enter for menu.")
        except Exception as exc:
            error(f"Error: {exc}")
