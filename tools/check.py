#!/usr/bin/env python3
"""Validate the built documentation site.

Catches the things that actually break a hand-authored static site: a link to a
page that does not exist, a duplicate heading id, an unescaped angle bracket
inside a code block, an image src pointing at nothing, a fragment that forgot
its front matter.

    python3 tools/check.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONTENT = ROOT / "content"

problems: list[str] = []
notes: list[str] = []


def fail(where: str, msg: str) -> None:
    problems.append(f"{where}: {msg}")


def note(where: str, msg: str) -> None:
    notes.append(f"{where}: {msg}")


class Wellformed(HTMLParser):
    """A light well-formedness check: unclosed or crossed block tags."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "param", "source", "track", "wbr", "path", "rect", "circle",
            "line", "polyline", "polygon", "ellipse", "use", "stop"}

    def __init__(self, name: str) -> None:
        super().__init__(convert_charrefs=True)
        self.name = name
        self.stack: list[tuple[str, int]] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                if i != len(self.stack) - 1:
                    unclosed = ", ".join(f"<{t}> (line {ln})" for t, ln in self.stack[i + 1:])
                    fail(self.name, f"</{tag}> at line {self.getpos()[0]} closes over unclosed {unclosed}")
                del self.stack[i:]
                return
        fail(self.name, f"stray </{tag}> at line {self.getpos()[0]}")

    def finish(self):
        for t, ln in self.stack:
            fail(self.name, f"<{t}> opened at line {ln} is never closed")



NESTED_IN = ("card", "steps", "prod", "acc", "def", "tl", "featlist", "codetabs")


class Headings(HTMLParser):
    """Find h2/h3 that are page sections rather than parts of a component."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0          # how deep inside an exempting component we are
        self.stack: list[bool] = []
        self.found: list[tuple[str, int, bool]] = []

    def handle_starttag(self, tag, attrs):
        if tag in Wellformed.VOID:
            return
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        exempt = any(c == n or c.startswith(n + "-") or c.startswith(n + "__")
                     for c in classes for n in NESTED_IN)
        self.stack.append(exempt)
        if exempt:
            self.depth += 1
        if tag in ("h2", "h3") and self.depth == 0:
            self.found.append((tag[1], self.getpos()[0], "id" in a))

    def handle_endtag(self, tag):
        if tag in Wellformed.VOID or not self.stack:
            return
        if self.stack.pop():
            self.depth = max(0, self.depth - 1)


def structural_headings(raw: str) -> list[tuple[str, int, bool]]:
    h = Headings()
    try:
        h.feed(raw)
    except Exception:  # noqa: BLE001
        return []
    return h.found


CODE_RE = re.compile(r"<pre><code[^>]*>(.*?)</code></pre>", re.S)
ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r'href="([^"]+)"')
SRC_RE = re.compile(r'src="([^"]+)"')
LANG_RE = re.compile(r"<pre><code(?![^>]*data-lang)")
META_RE = re.compile(r"^\s*<!--META\s*\{.*?\}\s*-->", re.S)


def check_fragment(p: Path) -> None:
    name = f"content/{p.name}"
    raw = p.read_text(encoding="utf-8")

    if not META_RE.match(raw):
        fail(name, "missing or malformed <!--META {...}--> front matter on the first line")
    if re.search(r"<h1[\s>]", raw):
        fail(name, "contains an <h1> — the builder supplies the page heading")
    if re.search(r"<style[\s>]", raw):
        fail(name, "contains a <style> block — all styling belongs in assets/css/site.css")

    # Unescaped markup inside code blocks: the classic page-breaking bug.
    for block in CODE_RE.findall(raw):
        stripped = re.sub(r"&[a-zA-Z]+;|&#\d+;", "", block)
        if "<" in stripped:
            snippet = stripped[max(0, stripped.index("<") - 30):stripped.index("<") + 40]
            fail(name, f"unescaped '<' inside a code block near: ...{snippet.strip()}...")

    for m in LANG_RE.finditer(raw):
        line = raw[: m.start()].count("\n") + 1
        note(name, f"<pre><code> with no data-lang at line {line} (no highlighting)")

    # Headings must be addressable — the TOC is built from their ids. Headings
    # inside a card, a step, a product panel, an accordion, a def block or a
    # timeline entry are deliberately exempt: they are part of a component, not
    # sections of the page, and the contract says to leave them out of the TOC.
    for lvl, line, has_id in structural_headings(raw):
        if not has_id:
            fail(name, f"<h{lvl}> at line {line} has no id — it cannot appear in the TOC")

    ids = ID_RE.findall(raw)
    for dup, n in Counter(ids).items():
        if n > 1:
            fail(name, f'duplicate id="{dup}" ({n} times)')

    parser = Wellformed(name)
    try:
        parser.feed(raw)
        parser.finish()
    except Exception as exc:  # noqa: BLE001
        fail(name, f"could not parse: {exc}")


def check_page(p: Path, slugs: set[str]) -> None:
    name = str(p.relative_to(ROOT))
    raw = p.read_text(encoding="utf-8")

    for href in HREF_RE.findall(raw):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (p.parent / href.split("#")[0]).resolve()
        if not target.exists():
            fail(name, f'href="{href}" points at nothing')

    for src in SRC_RE.findall(raw):
        if src.startswith(("http://", "https://", "data:")):
            continue
        target = (p.parent / src).resolve()
        if not target.exists():
            fail(name, f'src="{src}" points at nothing')

    ids = ID_RE.findall(raw)
    for dup, n in Counter(ids).items():
        if n > 1:
            fail(name, f'duplicate id="{dup}" in the built page ({n} times)')

    for anchor in re.findall(r'href="#([^"]+)"', raw):
        if anchor not in ids:
            fail(name, f'href="#{anchor}" has no matching id on the page')


def main() -> int:
    if not CONTENT.exists():
        print("no content/ directory", file=sys.stderr)
        return 1

    fragments = sorted(CONTENT.glob("*.html"))
    for f in fragments:
        check_fragment(f)

    slugs = {f.stem for f in fragments}
    pages = sorted(DOCS.glob("*.html")) if DOCS.exists() else []
    for pg in pages:
        check_page(pg, slugs)

    index = ROOT / "index.html"
    if index.exists():
        check_page(index, slugs)

    shots = sorted(set(re.findall(r'data-shot="([^"]+)"', "\n".join(
        f.read_text(encoding="utf-8") for f in fragments))))

    print(f"Checked {len(fragments)} fragment(s) and {len(pages) + 1} built page(s).")

    if notes:
        print(f"\n{len(notes)} note(s):")
        for n in notes[:40]:
            print(f"  · {n}")
        if len(notes) > 40:
            print(f"  · … and {len(notes) - 40} more")

    if shots:
        print(f"\n{len(shots)} screenshot slot(s) still to fill in assets/img/shots/:")
        for s in shots:
            print(f"  · {s}")

    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        return 1

    print("\nNo problems found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
