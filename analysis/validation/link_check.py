from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        key = "src" if tag in {"img", "script"} else "href" if tag in {"a", "link"} else ""
        if key and values.get(key):
            self.links.append(values[key] or "")


def run(root: Path, html_path: Path | None = None) -> list[str]:
    html_path = html_path or root / "index.html"
    parser = LinkParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.scheme or link.startswith("#") or link.startswith("mailto:"):
            continue
        target = html_path.parent / unquote(parsed.path)
        if not target.exists():
            missing.append(link)
    return missing

