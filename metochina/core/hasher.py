"""File hashing utilities for integrity verification.

Computes MD5 and SHA-256 digests using chunked reads to handle large files
without excessive memory consumption.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 65536  # 64 KB


def compute_hashes(filepath: str) -> Tuple[str, str]:
    """Compute MD5 and SHA-256 hashes for a file.

    Args:
        filepath: Path to the file.

    Returns:
        Tuple of (md5_hex, sha256_hex) lowercase hex digest strings.

    Raises:
        OSError: If the file cannot be read.
    """
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK_SIZE)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)

    return md5.hexdigest(), sha256.hexdigest()
