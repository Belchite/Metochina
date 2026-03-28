# Security Policy

## What Metochina Does

Metochina is a local EXIF metadata analysis tool. It reads image files on your machine, extracts embedded metadata (EXIF, IPTC, XMP), and presents the findings to you. It can also assess privacy risks based on the metadata found and generate map links from GPS coordinates.

## What Metochina Does NOT Do

Understanding what this tool does not do is just as important as understanding what it does.

### Only Processes Local Files

- Metochina operates exclusively on files stored on your local filesystem.
- It does not download, scrape, or fetch images from the internet.
- It does not access cloud storage, social media platforms, or any remote file systems.
- All file access is read-only; the tool never modifies your original images.

### Does Not Transmit Data

- Metochina does **not** send any data to external servers, APIs, or third-party services.
- No metadata, analysis results, GPS coordinates, or file information leaves your machine.
- There is no telemetry, analytics, crash reporting, or usage tracking of any kind.
- No outbound HTTP requests are made during analysis.

### Does Not Store Results Unless User Exports

- Analysis results exist only in memory during execution and are displayed in the terminal.
- No temporary files, caches, databases, or logs are created during normal operation.
- Results are written to disk **only** when you explicitly request an export (HTML, JSON, or CSV) using the --export flag or the interactive menu.
- You have full control over where exported files are saved and can delete them at any time.

### No Network Access

- The tool requires **no internet connection** to function.
- The only network-adjacent feature is the generation of map URL strings (Google Maps, OpenStreetMap) from GPS coordinates. These URLs are displayed as text in the output but are **not** automatically opened or accessed by the tool.
- If you click a generated map link, that action occurs in your browser and is outside the scope of Metochina.

### No Elevated Privileges

- Metochina does not require administrator or root privileges.
- It does not access system files, registry entries, or protected directories.
- It runs entirely within standard user permissions.

---

## Dependency Security

Metochina depends on the following well-established packages:

| Dependency | Purpose                        |
| ---------- | ------------------------------ |
| Pillow     | Image file reading and EXIF extraction |
| Click      | Command-line interface         |

Both are widely used, actively maintained open-source projects. We recommend keeping dependencies up to date:

    python -m pip install --upgrade Pillow click

---

## Reporting Security Issues

If you discover a security vulnerability in Metochina, we appreciate your help in disclosing it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. Send a detailed report to the project maintainers via private communication (email or GitHub Security Advisory).
3. Include the following in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
- **Assessment**: We will assess the severity and impact within 7 days.
- **Resolution**: We will work on a fix and coordinate disclosure with you.
- **Credit**: With your permission, we will credit you in the security advisory and changelog.

### Scope

The following are considered in scope for security reports:

- Vulnerabilities in Metochina's code that could lead to unintended data exposure
- Bugs that cause the tool to write data to unexpected locations
- Issues where the tool could be tricked into making network requests
- Dependency vulnerabilities that directly affect Metochina's functionality
- Path traversal or file access beyond the user's intended scope

The following are out of scope:

- Social engineering attacks against users
- Issues in upstream dependencies that do not affect Metochina
- Denial of service via excessively large files (the tool processes whatever you give it)
- Vulnerabilities requiring physical access to the user's machine

---

## Security Best Practices for Users

- Keep Python and all dependencies updated to their latest versions.
- Only analyze files from sources you trust, or in an isolated environment.
- Review exported files before sharing them, as they may contain sensitive metadata.
- Delete exported analysis results when they are no longer needed.
- Be cautious with GPS coordinate data, as it may reveal sensitive locations.
