<p align="center">
  <strong>METOCHINA v1.2</strong><br>
  OSINT Image Metadata Analyzer
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License MIT"></a>
  <img src="https://img.shields.io/badge/version-1.2.0-blue?style=flat-square" alt="Version 1.2.0">
  <img src="https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square" alt="Tests passing">
  <a href="#contributing"><img src="https://img.shields.io/badge/PRs-welcome-blue?style=flat-square" alt="PRs Welcome"></a>
</p>

---

## What is Metochina?

**Metochina** is a command-line OSINT tool that extracts, analyzes, and reports on hidden metadata embedded in image files. It provides **automated privacy risk scoring**, **batch analysis with pattern detection**, **self-contained HTML reports**, and **direct GPS map links** — all from a single, dependency-light Python package.

### New in v1.2: Interactive Terminal UI

Run `python -m metochina` **without arguments** to launch the new interactive hacker-style terminal menu, inspired by tools like SET, Metasploit, and Lazagne:

- **5 rotating ASCII art banners** — different style on each launch
- **Numbered menu navigation** — no commands to memorize
- **Hacker-style prefixes** — `[+]` success, `[-]` error, `[*]` info, `[!]` warning
- **Box-drawn sections** — clean, structured output using Unicode box-drawing characters
- **Spinner and typing animations** — immersive terminal experience
- **Deep Scan mode** — full analysis with automatic export to JSON + HTML + CSV
- **Settings submenu** — toggle hashes, recursive scanning, export format, output directory

The classic CLI with all original commands remains fully available when arguments are provided.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/metochina/metochina.git
cd metochina

# 2. Install dependencies
pip install .

# 3. Launch the interactive menu
python -m metochina

# 4. Or use the classic CLI
python -m metochina scan photo.jpg
```

---

## Two Modes of Operation

### Interactive Mode (new in v1.2)

```bash
python -m metochina
```

Launches a full menu-driven interface:

```
[1] Scan Image         - Analyze a single image
[2] Batch Scan         - Scan all images in a directory
[3] GPS Extract        - Quick GPS coordinate extraction
[4] Hash File          - Compute MD5 + SHA-256
[5] Risk Assessment    - Privacy risk analysis
[6] Deep Scan          - Full analysis + auto-export
[7] Settings           - Configure tool options
[0] Exit
```

### CLI Mode (classic)

```bash
python -m metochina scan photo.jpg
python -m metochina gps photo.jpg
python -m metochina hash photo.jpg
python -m metochina risks photo.jpg
python -m metochina batch ./photos/ --html report.html
```

| Command | Description |
|:---|:---|
| `scan` | Analyze a single image or directory |
| `gps` | Extract GPS data with map links |
| `hash` | Compute MD5 + SHA-256 hashes |
| `risks` | Privacy risk assessment |
| `batch` | Batch analysis with summary report |
| `version` | Display version information |

---

## What It Extracts

| Category | Fields |
|:---|:---|
| **File Info** | Filename, path, size, format, MIME type, resolution, megapixels |
| **Hashes** | MD5, SHA-256 |
| **GPS** | Latitude, longitude, altitude, speed, direction, timestamp, datum, map links |
| **Camera** | Make, model, serial, lens, focal length, aperture, shutter, ISO, flash |
| **Software** | Software name, host computer, OS version, editing detection |
| **Timestamps** | Date taken, modified, digitized |
| **Privacy Risks** | HIGH/MEDIUM/LOW severity, exposure score (0-100) |

### Supported formats

`JPEG` `PNG` `TIFF` `WebP` `HEIC/HEIF` `BMP` `GIF`

---

## Privacy Risk Scoring

| Severity | Trigger | Points |
|:---|:---|:---:|
| **HIGH** | GPS coordinates, camera serial number | +25 each |
| **MEDIUM** | GPS altitude, timestamps, host computer, lens serial | +10 each |
| **LOW** | Camera make/model, software, editing detection | +3 each |

Score is capped at 100. Above 50 = substantial exposure.

---

## Architecture

```
metochina-v1.2/
├── metochina/
│   ├── __init__.py
│   ├── __main__.py            # Entry point (interactive or CLI)
│   ├── cli.py                 # Click CLI commands
│   ├── core/
│   │   ├── extractor.py       # EXIF extraction engine
│   │   ├── gps.py             # GPS coordinate parser
│   │   └── hasher.py          # MD5 + SHA-256 hashing
│   ├── models/
│   │   └── metadata.py        # Data models
│   ├── analysis/
│   │   └── analyzer.py        # Privacy risk assessment
│   ├── output/
│   │   ├── console.py         # Terminal formatting
│   │   └── exporters.py       # JSON, CSV, HTML export
│   └── ui/                    # NEW in v1.2
│       ├── banner.py          # 5 ASCII art banners
│       ├── menu.py            # Interactive menu system
│       ├── display.py         # Box drawing, prefixes
│       └── effects.py         # Spinner, typing, progress bar
├── tests/
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

---

## Testing

```bash
python -m unittest discover -s tests -v
```

---

## Legal Disclaimer

> **This tool is intended for lawful OSINT research, digital forensics, journalism, and personal privacy auditing only.**
>
> Users are solely responsible for ensuring their use complies with all applicable laws. **Do not use this tool to stalk, harass, or unlawfully surveil any individual.**

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built by Belchite for the OSINT community. Use responsibly.</sub>
</p>
