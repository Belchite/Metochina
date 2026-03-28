# Changelog

All notable changes to Metochina will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-03-28

### Highlights

Interactive hacker-style terminal UI. Run `python -m metochina` without arguments to enter the visual menu.

### Added

- **Interactive terminal UI**: Full menu-driven interface inspired by Kali Linux tools (SET, Metasploit, Lazagne). Numbered menu options with box-drawing navigation.

- **5 rotating ASCII art banners**: Different banner style shown randomly on each launch — block, slant, graffiti, cyberpunk, and classic styles.

- **Startup animation sequence**: Typing effects, module loading messages with delays, and spinner animations during processing.

- **Hacker-style line prefixes**: `[+]` success (green), `[-]` error (red), `[*]` info (cyan), `[!]` warning (yellow), `[!!]` critical (red bold), `[?]` question (magenta), `[>]` result (white bold).

- **Section boxes**: Box-drawn sections for File Info, GPS, Camera, Software, Timestamps, Hashes, and Privacy Risks using `┌─┐│└─┘├┤` characters.

- **Deep Scan mode** (`[6]`): Full analysis with automatic export to JSON + HTML + CSV.

- **Settings submenu** (`[7]`): Toggle hash computation, recursive scanning, default export format, and output directory.

- **Progress bar**: Visual `████░░░░` progress bar for batch operations.

- **Spinner animations**: Braille character spinner (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`) during analysis.

- **Privacy score bar**: Color-coded inline score visualization in risk assessment.

- **New UI module**: `metochina/ui/` package with `banner.py`, `menu.py`, `display.py`, `effects.py`.

### Changed

- `__main__.py` now detects whether arguments are provided. No arguments launches the interactive UI; with arguments, the standard Click CLI is used (fully backwards compatible).

- Version bumped to 1.2.0.

### Fixed

- Nothing — v1.0 core logic is unchanged and stable.

---

## [1.0.0] - 2024-12-01

### Highlights

First public release of Metochina, a local OSINT metadata analysis tool for images.

### Added

- **Full EXIF extraction**: Comprehensive extraction of EXIF metadata from JPEG, PNG, TIFF, WebP, HEIC, BMP, and GIF files using Pillow.

- **GPS coordinate parsing**: Automatic parsing of EXIF GPS data with DMS to decimal degrees conversion.

- **Interactive map links**: Google Maps and OpenStreetMap URLs from GPS coordinates.

- **Privacy risk assessment**: Automated HIGH/MEDIUM/LOW risk scoring with Privacy Exposure Score (0-100).

- **Software detection**: Editing software identification with `was_edited` heuristic.

- **HTML/JSON/CSV export**: Self-contained dark-theme HTML reports, structured JSON, flat CSV.

- **Batch analysis**: Directory scanning with aggregate statistics and pattern detection.

- **CLI with Click**: Commands: `scan`, `gps`, `hash`, `risks`, `batch`, `version`.

- **File integrity hashing**: SHA-256 and MD5 via chunked reads.

- **Comprehensive test suite**: 50+ unit tests.

- **CI/CD pipeline**: GitHub Actions on Ubuntu, Windows, macOS with Python 3.11-3.13.
