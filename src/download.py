from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path

try:
    from .common import DEFAULT_ZIP, RESEARCH_DATE, SOURCE_PAGE, SOURCE_URL, sha256
except ImportError:  # Direct execution: python3 src/download.py
    from common import DEFAULT_ZIP, RESEARCH_DATE, SOURCE_PAGE, SOURCE_URL, sha256


def download(url: str, output: Path, metadata: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "daito-gtfs-fares-v2-poc/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.startswith(b"PK"):
        raise ValueError("downloaded content is not a ZIP archive")
    output.write_bytes(payload)
    record = {
        "source_page": SOURCE_PAGE,
        "download_url": url,
        "downloaded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "research_date": RESEARCH_DATE,
        "bytes": len(payload),
        "sha256": sha256(output),
    }
    metadata.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official Daito City GTFS-JP ZIP")
    parser.add_argument("--url", default=SOURCE_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_ZIP.with_suffix(".metadata.json"))
    args = parser.parse_args()
    print(json.dumps(download(args.url, args.output, args.metadata), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
