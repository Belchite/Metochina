"""Command-line interface for Metochina.

Built with Click. Provides commands for scanning single images, batches,
GPS-only extraction, hashing, and risk assessment. Includes progress
indicators for batch operations.
"""

from __future__ import annotations

import logging
import os
import sys

import click

from metochina import __version__
from metochina.analysis.analyzer import (
    assess_batch_patterns,
    assess_privacy_risks,
    compute_privacy_score,
)
from metochina.core.extractor import extract_batch, extract_metadata, find_images
from metochina.core.hasher import compute_hashes
from metochina.output.console import (
    BANNER, BOLD, CYAN, DIM, GREEN, MAGENTA, RED, RESET, WHITE, YELLOW,
    _box_bottom, _box_divider, _box_double_divider, _box_empty, _box_line,
    _box_top, _c, _kv, _print_banner, _progress_bar, _risk_icon,
    _section_header, _threat_indicator,
    print_batch_report, print_metadata,
)
from metochina.output.exporters import export_csv, export_html, export_json

logger = logging.getLogger("metochina")


def _setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _resolve_targets(target: str, recursive: bool) -> list[str]:
    """Resolve a file or directory target into a list of image paths."""
    target = os.path.abspath(target)

    if os.path.isfile(target):
        return [target]
    elif os.path.isdir(target):
        images = find_images(target, recursive=recursive)
        if not images:
            click.echo(
                click.style(f"No supported images found in: {target}", fg="red"),
                err=True,
            )
            sys.exit(1)
        return images
    else:
        click.echo(
            click.style(f"Path not found: {target}", fg="red"),
            err=True,
        )
        sys.exit(1)


def _batch_progress(current: int, total: int, filename: str) -> None:
    """Progress callback for batch operations."""
    pct = (current / total) * 100
    bar_width = 25
    filled = int(bar_width * current / total)
    bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
    sys.stdout.write(f"\r  [{bar}] {current}/{total} ({pct:.0f}%) \u2014 {filename[:40]}")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(__version__, prog_name="metochina")
def cli(ctx: click.Context) -> None:
    """Metochina \u2014 OSINT Image Metadata Analyzer.

    Extract, analyze, and report on hidden metadata in image files.
    """
    if ctx.invoked_subcommand is None:
        _print_banner("OSINT Image Metadata Analyzer")
        click.echo(ctx.get_help())


@cli.command()
@click.argument("target")
@click.option("--json", "json_path", type=click.Path(), default=None, help="Export to JSON file.")
@click.option("--csv", "csv_path", type=click.Path(), default=None, help="Export to CSV file.")
@click.option("--html", "html_path", type=click.Path(), default=None, help="Export to HTML report.")
@click.option("--raw", is_flag=True, default=False, help="Show all raw EXIF fields.")
@click.option("--no-hash", is_flag=True, default=False, help="Skip hash computation.")
@click.option("-r", "--recursive", is_flag=True, default=False, help="Search subdirectories.")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Extended details.")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
def scan(
    target: str,
    json_path: str | None,
    csv_path: str | None,
    html_path: str | None,
    raw: bool,
    no_hash: bool,
    recursive: bool,
    verbose: bool,
    debug: bool,
) -> None:
    """Analyze an image or all images in a directory."""
    _setup_logging(debug)
    files = _resolve_targets(target, recursive)

    if len(files) == 1:
        meta = extract_metadata(files[0], skip_hash=no_hash)
        print_metadata(meta, verbose=verbose or raw, show_risks=True)

        if json_path:
            export_json(meta, json_path)
            click.echo(f"  {_c(GREEN, '\u2714')} JSON saved to: {json_path}")
        if html_path:
            export_html(meta, html_path)
            click.echo(f"  {_c(GREEN, '\u2714')} HTML saved to: {html_path}")
    else:
        click.echo(f"\n  Scanning {len(files)} image(s)...\n")
        report = extract_batch(files, skip_hash=no_hash, on_progress=_batch_progress)
        print()
        print_batch_report(report, verbose=verbose)

        if json_path:
            export_json(report, json_path)
            click.echo(f"  {_c(GREEN, '\u2714')} JSON saved to: {json_path}")
        if csv_path:
            export_csv(report, csv_path)
            click.echo(f"  {_c(GREEN, '\u2714')} CSV saved to: {csv_path}")
        if html_path:
            export_html(report, html_path)
            click.echo(f"  {_c(GREEN, '\u2714')} HTML saved to: {html_path}")


@cli.command()
@click.argument("filepath")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
def gps(filepath: str, debug: bool) -> None:
    """Show only GPS data for an image."""
    _setup_logging(debug)

    if not os.path.isfile(filepath):
        click.echo(click.style(f"File not found: {filepath}", fg="red"), err=True)
        sys.exit(1)

    meta = extract_metadata(filepath, skip_hash=True)

    print()
    print(_box_top())
    print(_box_line(
        _c(BOLD + WHITE, "\U0001f4cd GPS EXTRACTION  \u00b7  ") + _c(CYAN, meta.filename),
        align="center",
    ))
    print(_box_double_divider())

    if meta.has_gps:
        print(_box_empty())
        print(_kv("Latitude", _c(GREEN + BOLD, str(meta.gps.latitude))))
        print(_kv("Longitude", _c(GREEN + BOLD, str(meta.gps.longitude))))
        if meta.gps.altitude is not None:
            print(_kv("Altitude", f"{meta.gps.altitude}m"))
        if meta.gps.timestamp:
            print(_kv("GPS Timestamp", meta.gps.timestamp))
        if meta.gps.datum:
            print(_kv("Datum", meta.gps.datum))
        print(_box_empty())
        if meta.gps.google_maps_url:
            print(_box_line(
                f"      {_c(GREEN, '\U0001f310 Google Maps :')} {_c(CYAN, meta.gps.google_maps_url)}"
            ))
        if meta.gps.osm_url:
            print(_box_line(
                f"      {_c(GREEN, '\U0001f5fa  OpenStreetMap:')} {_c(CYAN, meta.gps.osm_url)}"
            ))
        print(_box_empty())
    else:
        print(_box_empty())
        print(_box_line(_c(YELLOW + BOLD, "      \u26a0  No GPS data found in this image.")))
        print(_box_empty())

    print(_box_bottom())
    print()


@cli.command()
@click.argument("filepath")
def hash(filepath: str) -> None:
    """Show MD5 and SHA-256 hashes for a file."""
    if not os.path.isfile(filepath):
        click.echo(click.style(f"File not found: {filepath}", fg="red"), err=True)
        sys.exit(1)

    md5, sha256 = compute_hashes(filepath)
    fname = os.path.basename(filepath)

    print()
    print(_box_top())
    print(_box_line(
        _c(BOLD + WHITE, "\U0001f512 INTEGRITY HASHES  \u00b7  ") + _c(CYAN, fname),
        align="center",
    ))
    print(_box_double_divider())
    print(_box_empty())
    print(_kv("MD5", _c(CYAN, md5)))
    print(_kv("SHA-256", _c(CYAN, sha256)))
    print(_box_empty())
    print(_box_bottom())
    print()


@cli.command()
@click.argument("filepath")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
def risks(filepath: str, debug: bool) -> None:
    """Show privacy risk assessment for an image."""
    _setup_logging(debug)

    if not os.path.isfile(filepath):
        click.echo(click.style(f"File not found: {filepath}", fg="red"), err=True)
        sys.exit(1)

    meta = extract_metadata(filepath, skip_hash=True)
    risk_list = assess_privacy_risks(meta)
    score = compute_privacy_score(risk_list)

    print()
    print(_box_top())
    print(_box_line(
        _c(BOLD + WHITE, "\U0001f6e1 RISK ASSESSMENT  \u00b7  ") + _c(CYAN, meta.filename),
        align="center",
    ))
    print(_box_double_divider())
    print(_box_empty())
    print(_box_line(_c(BOLD + WHITE, "      Privacy Exposure Score:")))
    print(_box_line(_progress_bar(score)))
    print(_box_empty())

    if risk_list:
        print(_box_divider())
        for risk in risk_list:
            icon = _risk_icon(risk.level)
            if risk.level == "HIGH":
                level_c = _c(RED + BOLD, risk.level)
            elif risk.level == "MEDIUM":
                level_c = _c(YELLOW + BOLD, risk.level)
            else:
                level_c = _c(DIM, risk.level)
            print(_box_line(
                f"      {icon} {level_c}  {_c(DIM, '\u2502')} {_c(WHITE, risk.category)}"
            ))
            print(_box_line(f"           {risk.description}"))
            print(_box_line(f"           {_c(DIM, '\u2192 ' + risk.recommendation)}"))
            print(_box_empty())
    else:
        print(_box_line(_c(GREEN + BOLD, "      \u2714 No significant privacy risks detected.")))
        print(_box_empty())

    print(_box_bottom())
    print()


@cli.command()
@click.argument("directory")
@click.option("--json", "json_path", type=click.Path(), default=None, help="Export to JSON file.")
@click.option("--csv", "csv_path", type=click.Path(), default=None, help="Export to CSV file.")
@click.option("--html", "html_path", type=click.Path(), default=None, help="Export to HTML report.")
@click.option("--no-hash", is_flag=True, default=False, help="Skip hash computation.")
@click.option("-r", "--recursive", is_flag=True, default=True, help="Search subdirectories (default: on).")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Extended details.")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
def batch(
    directory: str,
    json_path: str | None,
    csv_path: str | None,
    html_path: str | None,
    no_hash: bool,
    recursive: bool,
    verbose: bool,
    debug: bool,
) -> None:
    """Analyze all images in a directory with a summary report."""
    _setup_logging(debug)

    if not os.path.isdir(directory):
        click.echo(click.style(f"Directory not found: {directory}", fg="red"), err=True)
        sys.exit(1)

    files = find_images(directory, recursive=recursive)
    if not files:
        click.echo(click.style(f"No supported images found in: {directory}", fg="red"), err=True)
        sys.exit(1)

    click.echo(f"\n  Found {_c(BOLD + WHITE, str(len(files)))} image(s). Analyzing...\n")

    report = extract_batch(files, skip_hash=no_hash, on_progress=_batch_progress)
    print()
    print_batch_report(report, verbose=verbose)

    if json_path:
        export_json(report, json_path)
        click.echo(f"  {_c(GREEN, '\u2714')} JSON saved to: {json_path}")
    if csv_path:
        export_csv(report, csv_path)
        click.echo(f"  {_c(GREEN, '\u2714')} CSV saved to: {csv_path}")
    if html_path:
        export_html(report, html_path)
        click.echo(f"  {_c(GREEN, '\u2714')} HTML saved to: {html_path}")


@cli.command()
def version() -> None:
    """Show version information."""
    _print_banner()
    print(_box_top())
    print(_box_line(
        _c(BOLD + MAGENTA, f"Metochina v{__version__}"),
        align="center",
    ))
    print(_box_divider())
    print(_box_empty())
    print(_kv("Version", _c(CYAN, __version__)))
    print(_kv("Python", _c(CYAN, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")))
    print(_kv("Platform", _c(CYAN, sys.platform)))
    print(_kv("License", "MIT"))
    print(_kv("Deps", "Pillow, Click"))
    print(_box_empty())
    print(_box_bottom())
    print()
