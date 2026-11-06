"""Check every link in README.md and report the dead ones.

Usage: python3 scripts/check_links.py [README.md]

Exits 0 if all links resolve, 1 if any are dead. Meant to run in CI,
but you can run it locally before opening a PR.
"""

import re
import sys
import urllib.request
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
TIMEOUT = 15


def extract_links(readme: Path) -> list[str]:
    seen: list[str] = []
    for match in LINK_RE.finditer(readme.read_text()):
        url = match.group(1)
        if url not in seen:
            seen.append(url)
    return seen


def check(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "awesome-ai-tools-link-check/1.0"})
    try:
        # Some sites reject HEAD, so try HEAD first and fall back to GET.
        try:
            req.get_method = lambda: "HEAD"
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return 200 <= resp.status < 400, f"HTTP {resp.status}"
        except Exception:
            req.get_method = lambda: "GET"
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return 200 <= resp.status < 400, f"HTTP {resp.status}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    readme = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("README.md")
    links = extract_links(readme)
    print(f"checking {len(links)} links in {readme}")
    dead: list[tuple[str, str]] = []
    for url in links:
        ok, detail = check(url)
        mark = "ok  " if ok else "DEAD"
        print(f"[{mark}] {url} ({detail})")
        if not ok:
            dead.append((url, detail))
    if dead:
        print(f"\n{len(dead)} dead link(s):")
        for url, detail in dead:
            print(f"  - {url}: {detail}")
        return 1
    print("\nall links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
