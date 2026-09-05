#!/usr/bin/env python3
"""Build the pytest-html-reporter documentation site.

Each page in content/ is a body fragment with a small JSON front-matter block.
This wraps it in the shared shell — head, top nav, sidebar, table of contents,
prev/next and footer — and writes a complete, standalone HTML file.

The output is plain static HTML with no runtime dependency on this script, so
the built pages can be served by GitHub Pages exactly as they are.

    python3 tools/build.py            # build everything
    python3 tools/build.py --check    # verify the built pages are up to date
"""

from __future__ import annotations

import json
import re
import sys
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"

SITE_TITLE = "pytest-html-reporter"
REPO = "https://github.com/prashanth-sams/pytest-html-reporter"
REPO_ACTION = "https://github.com/prashanth-sams/pytest-html-reporter-action"
REPO_VSCODE = "https://github.com/prashanth-sams/pytest-html-reporter-vscode"
PYPI = "https://pypi.org/project/pytest-html-reporter/"
MARKETPLACE = ("https://marketplace.visualstudio.com/items"
               "?itemName=prashanth-sams.pytest-html-reporter-vscode")

# The project's sponsor. The artwork lives in images/ and is a black mark on
# transparency; the stylesheet inverts it for the dark theme.
SPONSOR_NAME = "Pickoh"
SPONSOR_URL = "https://pickoh.com/"

# --------------------------------------------------------------- navigation

# (group label, [(slug, title, icon key)])
SIDEBAR = [
    ("Introduction", [
        ("getting-started", "Getting started", "rocket"),
        ("features", "Features", "sparkle"),
        ("report-tour", "Report tour", "layout"),
    ]),
    ("Reference", [
        ("cli-reference", "CLI reference", "terminal"),
        ("configuration", "Configuration", "sliders"),
        ("python-api", "Python API", "code"),
        ("compatibility", "Compatibility &amp; files", "package"),
    ]),
    ("Guides", [
        ("screenshots", "Screenshots", "camera"),
        ("steps-and-bdd", "Steps &amp; BDD", "list"),
        ("analytics", "Analytics &amp; history", "chart"),
        ("ci-integrations", "CI, xdist &amp; scale", "server"),
        ("security-privacy", "Security &amp; privacy", "shield"),
    ]),
    ("Ecosystem", [
        ("github-action", "GitHub Action", "action"),
        ("vscode", "VS Code extension", "vscode"),
    ]),
    ("Project", [
        ("changelog", "Changelog", "clock"),
        ("faq", "FAQ", "help"),
        ("contributing", "Contributing", "heart"),
    ]),
]

# Flat order drives prev/next.
ORDER = [slug for _, items in SIDEBAR for slug, _, _ in items]
TITLES = {slug: title for _, items in SIDEBAR for slug, title, _ in items}

ICONS = {
    "rocket":  '<path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2 2 0 0 0-2.9 0z"/><path d="M12 15 9 12a11 11 0 0 1 2-6c2.2-3 5.5-3.5 8-3.5 0 2.5-.5 5.8-3.5 8a11 11 0 0 1-6 2z"/><path d="M9 12H5s.4-2.5 2-3.5c1.7-1 3.5-.5 3.5-.5M12 15v4s2.5-.4 3.5-2c1-1.7.5-3.5.5-3.5"/>',
    "sparkle": '<path d="m12 3 2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/><path d="M19 3v4M17 5h4M5 17v2M4 18h2"/>',
    "layout":  '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
    "terminal":'<path d="m5 8 4 4-4 4M13 16h6"/><rect x="2" y="3" width="20" height="18" rx="2"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "code":    '<path d="m8 6-6 6 6 6M16 6l6 6-6 6"/>',
    "camera":  '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="m8 6 1.5-2.5h5L16 6"/><circle cx="12" cy="13" r="3.4"/>',
    "list":    '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "chart":   '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
    "server":  '<rect x="2" y="3" width="20" height="7" rx="2"/><rect x="2" y="14" width="20" height="7" rx="2"/><path d="M6 6.5h.01M6 17.5h.01"/>',
    "action":  '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "vscode":  '<path d="m17 3-9 7-4-3-2 1.5v7L4 17l4-3 9 7 4-2V5z"/>',
    "clock":   '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "help":    '<circle cx="12" cy="12" r="9"/><path d="M9.2 9.2a2.9 2.9 0 0 1 5.6 1c0 2-2.8 2.8-2.8 2.8M12 17h.01"/>',
    "package": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
    "shield":  '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "heart":   '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1L12 21l7.7-7.6 1.1-1a5.5 5.5 0 0 0 0-7.8z"/>',
}

BRAND_MARK = (
    '<svg class="brand__mark" viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="2" y="3" width="3.9" height="18" rx="1" fill="#3571a3"/>'
    '<rect x="7.4" y="7.85" width="3.9" height="13.15" rx="1" fill="#ffd143"/>'
    '<rect x="12.8" y="12.7" width="3.9" height="8.3" rx="1" fill="#8b8b8b"/>'
    '<rect x="18.2" y="17.3" width="3.9" height="3.7" rx="1" fill="#3571a3"/>'
    "</svg>"
)

GITHUB_GLYPH = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5A11.5 '
    '11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88'
    '-1.37-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.2 1.77 1.2 1.03 1.77 '
    '2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.1'
    '-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.5 3.17-1.18 3.17'
    '-1.18.63 1.59.24 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.26 5.69.41.36.78 '
    '1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z"/></svg>'
)

SEARCH_GLYPH = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
    '<path d="m20 20-3.6-3.6"/></svg>'
)


def searchbtn(prefix: str) -> str:
    """The topbar trigger. Everything else about search is built by site.js.

    The index it loads is written by write_search_index(); data-search-root is
    how the script turns the site-relative paths in that file into links that
    work from both / and /docs/."""
    return f"""<button class="searchbtn" type="button" data-search-root="{prefix}"
      aria-label="Search the documentation" aria-haspopup="dialog">
      {SEARCH_GLYPH}
      <span class="searchbtn__label">Search docs</span>
      <kbd class="searchbtn__kbd"><span class="searchbtn__mod">Ctrl</span>K</kbd>
    </button>"""


# (slug, label). A slug is a docs page; DEMO_SLUG is the one entry that points
# outside docs/ — at report/index.html, which redirects to the real report
# generated by an actual pytest run and committed under report/.
DEMO_SLUG = "__demo__"
# index.html is named rather than left to the server: over file:// — opening the
# built site straight off disk — a bare directory gives Chrome's listing, not the
# redirect. Pages serves exactly the same URL either way.
DEMO_HREF = "report/index.html"

TOP_NAV_LINKS = [
    ("getting-started", "Docs"),
    ("report-tour", "Report tour"),
    (DEMO_SLUG, "Live&nbsp;demo"),
    ("cli-reference", "Reference"),
    ("github-action", "Action"),
    ("vscode", "VS&nbsp;Code"),
    ("changelog", "Changelog"),
]


def head(meta: dict, prefix: str) -> str:
    title = meta["title"]
    desc = meta.get("description", "")
    full = f"{title} · {SITE_TITLE}" if title != SITE_TITLE else title
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full)}</title>
<meta name="description" content="{escape(desc)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="{prefix}assets/img/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{prefix}assets/img/icon-256.png">
<meta property="og:title" content="{escape(full)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{prefix}assets/img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<script>
/* Set the theme before first paint so a dark reader never sees a white flash. */
(function(){{try{{var t=localStorage.getItem('phr-theme');
if(!t)t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}
document.documentElement.classList.add('js');}})();
</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""


def topbar(slug: str, prefix: str) -> str:
    parts = []
    for s, t in TOP_NAV_LINKS:
        if s == DEMO_SLUG:
            parts.append('<a class="navlinks__demo" href="{}{}">{}</a>'.format(prefix, DEMO_HREF, t))
            continue
        cls = ' class="is-active"' if s == slug else ""
        parts.append('<a href="{}docs/{}.html"{}>{}</a>'.format(prefix, s, cls, t))
    links = "".join(parts)
    return f"""<header class="topbar">
  <div class="topbar__inner">
    <button class="iconbtn navburger" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="sidebar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </button>
    <a class="brand" href="{prefix}index.html" aria-label="pytest-html-reporter home">
      {BRAND_MARK}
      <span class="brand__text"><span class="brand__a">pytest</span><span class="brand__b">HTML Reporter</span></span>
    </a>
    <nav class="navlinks" aria-label="Main">{links}</nav>
    <div class="topbar__spacer"></div>
    {searchbtn(prefix)}
    <div class="topbar__right">
      <a class="iconbtn" href="{PYPI}" target="_blank" rel="noopener" title="PyPI" aria-label="pytest-html-reporter on PyPI">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/></svg>
      </a>
      <a class="iconbtn" href="{REPO}" target="_blank" rel="noopener" title="GitHub" aria-label="Source on GitHub">{GITHUB_GLYPH}</a>
      <button class="iconbtn theme-toggle" type="button" aria-label="Toggle theme">
        <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.2M12 19.8V22M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2 12h2.2M19.8 12H22M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>
        <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.6A8.6 8.6 0 0 1 9.4 3.5a8.6 8.6 0 1 0 11.1 11.1z"/></svg>
      </button>
    </div>
  </div>
</header>
<div class="navscrim" aria-hidden="true"></div>
"""


def sidebar(slug: str, prefix: str) -> str:
    out = ['<aside class="sidebar" id="sidebar"><nav aria-label="Documentation">']
    for label, items in SIDEBAR:
        out.append('<div class="sidebar__group">')
        out.append(f'<span class="sidebar__label">{label}</span>')
        for s, title, icon in items:
            active = " is-active" if s == slug else ""
            path = ICONS.get(icon, ICONS["code"])
            out.append(
                f'<a class="sidebar__link{active}" href="{prefix}docs/{s}.html">'
                f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
                f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>'
                f"{title}</a>"
            )
        out.append("</div>")
    out.append("</nav>")
    # Below the navigation, not inside it: a credit, not a destination.
    out.append(
        f'<a class="sponsor-side" href="{SPONSOR_URL}" target="_blank" rel="noopener sponsored">'
        f'<span class="sponsor-label">Sponsored by</span>'
        f'<img class="sponsor-logo" src="{prefix}images/pickoh.png" alt="{SPONSOR_NAME}" '
        f'width="1018" height="251" loading="lazy" decoding="async"></a>'
    )
    out.append("</aside>")
    return "\n".join(out)


HEADING_RE = re.compile(
    r'<h([23])([^>]*?)\sid="([^"]+)"([^>]*)>(.*?)</h\1>', re.S | re.I
)
TAG_RE = re.compile(r"<[^>]+>")


def build_toc(body: str) -> str:
    items = []
    for m in HEADING_RE.finditer(body):
        level = m.group(1)
        hid = m.group(3)
        text = TAG_RE.sub("", m.group(5)).strip()
        text = re.sub(r"\s+", " ", text)
        items.append((level, hid, text))
    if len(items) < 2:
        return ""
    # A reference page can carry sixty headings. Listing every h3 alongside them
    # turns the contents into a second document you have to read to use the
    # first one, so past twenty entries only the h2 sections are listed.
    if len(items) > 20:
        top = [i for i in items if i[0] == "2"]
        if len(top) >= 3:
            items = top
    rows = "\n".join(
        f'<li class="lvl-{lvl}"><a href="#{hid}">{txt}</a></li>' for lvl, hid, txt in items
    )
    return f"""<aside class="toc" aria-label="On this page">
  <div class="toc__title">On this page</div>
  <ul>
{rows}
  </ul>
</aside>"""


def pagenav(slug: str, prefix: str) -> str:
    if slug not in ORDER:
        return ""
    i = ORDER.index(slug)
    prev_s = ORDER[i - 1] if i > 0 else None
    next_s = ORDER[i + 1] if i < len(ORDER) - 1 else None
    parts = ['<nav class="pagenav" aria-label="Pagination">']
    if prev_s:
        parts.append(
            f'<a class="prev" href="{prefix}docs/{prev_s}.html">'
            f"<span>&larr; Previous</span><b>{TITLES[prev_s]}</b></a>"
        )
    else:
        parts.append("<span></span>")
    if next_s:
        parts.append(
            f'<a class="next" href="{prefix}docs/{next_s}.html">'
            f"<span>Next &rarr;</span><b>{TITLES[next_s]}</b></a>"
        )
    parts.append("</nav>")
    return "\n".join(parts)


def footer(prefix: str) -> str:
    return f"""<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div class="footer__about">
        <a class="brand" href="{prefix}index.html">{BRAND_MARK}
          <span class="brand__text"><span class="brand__a">pytest</span><span class="brand__b">HTML Reporter</span></span>
        </a>
        <p>A light-weight static HTML report for the pytest framework. MIT licensed, built by Prashanth Sams and contributors.</p>
        <a class="sponsor-foot" href="{SPONSOR_URL}" target="_blank" rel="noopener sponsored">
          <span class="sponsor-label">Sponsored by</span>
          <img class="sponsor-logo" src="{prefix}images/pickoh.png" alt="{SPONSOR_NAME}" width="1018" height="251" loading="lazy" decoding="async">
        </a>
      </div>
      <div>
        <h2>Documentation</h2>
        <ul>
          <li><a href="{prefix}docs/getting-started.html">Getting started</a></li>
          <li><a href="{prefix}docs/features.html">Features</a></li>
          <li><a href="{prefix}docs/report-tour.html">Report tour</a></li>
          <li><a href="{prefix}docs/cli-reference.html">CLI reference</a></li>
          <li><a href="{prefix}docs/python-api.html">Python API</a></li>
          <li><a href="{prefix}docs/compatibility.html">Compatibility &amp; files</a></li>
        </ul>
      </div>
      <div>
        <h2>Ecosystem</h2>
        <ul>
          <li><a href="{prefix}docs/github-action.html">GitHub Action</a></li>
          <li><a href="{prefix}docs/vscode.html">VS Code extension</a></li>
          <li><a href="{prefix}docs/ci-integrations.html">CI &amp; scale</a></li>
          <li><a href="{prefix}docs/analytics.html">Analytics &amp; history</a></li>
          <li><a href="{prefix}docs/security-privacy.html">Security &amp; privacy</a></li>
        </ul>
      </div>
      <div>
        <h2>Project</h2>
        <ul>
          <li><a href="{REPO}" target="_blank" rel="noopener">Source on GitHub</a></li>
          <li><a href="{PYPI}" target="_blank" rel="noopener">PyPI package</a></li>
          <li><a href="{MARKETPLACE}" target="_blank" rel="noopener">VS Code Marketplace</a></li>
          <li><a href="{REPO}/issues" target="_blank" rel="noopener">Issue tracker</a></li>
          <li><a href="{prefix}docs/contributing.html">Contributing</a></li>
          <li><a href="{prefix}docs/faq.html">FAQ</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <span>MIT licensed &middot; &copy; Prashanth Sams</span>
      <span>Built for people who read their test reports.</span>
    </div>
  </div>
</footer>
<script src="{prefix}assets/js/site.js"></script>
</body>
</html>
"""


FRONT_RE = re.compile(r"^\s*<!--META\s*(\{.*?\})\s*-->", re.S)


def render(path: Path) -> tuple[str, str, list[dict]]:
    raw = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(raw)
    if not m:
        raise SystemExit(f"{path.name}: missing <!--META {{...}}--> front-matter block")
    meta = json.loads(m.group(1))
    body = raw[m.end():].strip()
    slug = path.stem
    prefix = "../"

    doc_hero = f"""<div class="crumbs">
  <a href="{prefix}index.html">Home</a>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>
  <a href="{prefix}docs/getting-started.html">Docs</a>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>
  <span>{meta['title']}</span>
</div>
<header class="doc-hero">
  <span class="eyebrow">{meta.get('eyebrow', 'Documentation')}</span>
  <h1>{meta['title']}</h1>
  <p class="lede">{meta.get('lede', meta.get('description', ''))}</p>
</header>"""

    html = (
        head(meta, prefix)
        + topbar(slug, prefix)
        + '<div class="docs">\n'
        + sidebar(slug, prefix)
        + '\n<main class="docmain" id="main">\n'
        + doc_hero
        + "\n"
        + body
        + "\n"
        + pagenav(slug, prefix)
        + "\n</main>\n"
        + build_toc(body)
        + "\n</div>\n"
        + footer(prefix)
    )
    return slug, html, search_records(slug, meta, body)



# ------------------------------------------------------------- search index

# A section of a reference page can run to several thousand characters. Past
# this the record stops earning its download, so it is cut — the heading and
# the opening of the section are what a search result actually shows.
SNIPPET_MAX = 900

DROP_RE = re.compile(r"<(script|style|svg)\b.*?</\1>", re.S | re.I)
TAGS_RE = re.compile(r"<[^>]+>")
CODE_RE = re.compile(r"<code[^>]*>(.*?)</code>", re.S | re.I)
# A flag, a setting, a module path, a file name — the things a reader types into
# a search box verbatim. Bare prose in <code> ("true", "pytest") is not one.
TOKEN_RE = re.compile(r"^-{0,2}[A-Za-z0-9_][A-Za-z0-9_./-]{2,44}$")


def plain(html: str) -> str:
    """Everything a reader would see in this fragment, as one line of text."""
    text = DROP_RE.sub(" ", html)
    text = TAGS_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", unescape(text))
    # Dropping the tags leaves a gap wherever markup hugged its punctuation —
    # "report.html , and" — which a search snippet then shows verbatim.
    return re.sub(r" ([,.;:!?)\]])", r"\1", text).strip()


def keywords(chunk: str) -> str:
    """The code tokens in this section.

    A CLI reference documents its flags in a table, not in headings, so
    searching for --html-report otherwise finds every page that happens to
    mention it and never the page that defines it."""
    seen: dict[str, None] = {}
    for raw in CODE_RE.findall(chunk):
        tok = plain(raw)
        if not TOKEN_RE.match(tok):
            continue
        # A word with no punctuation is prose in a <code> font, not a name.
        if tok.isalpha() and not tok.startswith("-"):
            continue
        seen.setdefault(tok.lower(), None)
        if len(seen) >= 48:
            break
    return " ".join(seen)


def search_records(slug: str, meta: dict, body: str) -> list[dict]:
    """One record per section, because a result should land on the heading it
    matched rather than at the top of a two-thousand-word page."""
    title = unescape(meta["title"])
    page = f"docs/{slug}.html"
    marks = list(HEADING_RE.finditer(body))

    recs = []
    lede = plain(meta.get("lede", meta.get("description", "")))
    intro = plain(body[: marks[0].start()] if marks else body)
    recs.append({
        "p": page, "t": title, "h": "", "a": "",
        "x": (lede + " " + intro).strip()[:SNIPPET_MAX],
        "k": keywords(body[: marks[0].start()] if marks else body),
    })

    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        heading = plain(m.group(5))
        if not heading:
            continue
        chunk = body[m.end(): end]
        recs.append({
            "p": page, "t": title, "h": heading, "a": m.group(3),
            "x": plain(chunk)[:SNIPPET_MAX],
            "k": keywords(chunk),
        })
    return recs


def write_search_index(records: list[dict], check: bool = False) -> bool:
    """Returns True when the file on disk is already what this run would write."""
    path = ROOT / "assets" / "search-index.json"
    payload = json.dumps({"v": 1, "d": records}, ensure_ascii=False, separators=(",", ":")) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == payload:
        print("  = assets/search-index.json")
        return True
    if check:
        return False
    path.write_text(payload, encoding="utf-8")
    print(f"  + assets/search-index.json ({len(records)} sections, {len(payload):,} bytes)")
    return True


SITE_URL = "https://pytest-html-reporter.github.io"


def write_sitemap(sources) -> None:
    """A sitemap, so the pages are findable rather than only reachable."""
    urls = ["/"] + [f"/docs/{p.stem}.html" for p in sources]
    body = "\n".join(
        f"  <url><loc>{SITE_URL}{u}</loc>"
        f"<changefreq>weekly</changefreq>"
        f"<priority>{'1.0' if u == '/' else '0.8'}</priority></url>"
        for u in urls
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"  + sitemap.xml ({len(urls)} urls), robots.txt")


def main() -> int:
    check = "--check" in sys.argv
    OUT.mkdir(exist_ok=True)
    sources = sorted(CONTENT.glob("*.html"))
    if not sources:
        print("no content/*.html found", file=sys.stderr)
        return 1

    stale = []
    records = []
    for src in sorted(sources, key=lambda p: (ORDER.index(p.stem) if p.stem in ORDER else len(ORDER), p.stem)):
        slug, html, recs = render(src)
        records.extend(recs)
        dest = OUT / f"{slug}.html"
        old = dest.read_text(encoding="utf-8") if dest.exists() else None
        if old == html:
            print(f"  = {dest.relative_to(ROOT)}")
            continue
        if check:
            stale.append(dest.relative_to(ROOT))
            continue
        dest.write_text(html, encoding="utf-8")
        print(f"  + {dest.relative_to(ROOT)}  ({len(html):,} bytes)")

    if not check:
        write_sitemap(sources)
    if not write_search_index(records, check):
        stale.append(Path("assets/search-index.json"))

    missing = [s for s in ORDER if not (CONTENT / f"{s}.html").exists()]
    if missing:
        print(f"\n  ! sidebar entries with no content file: {', '.join(missing)}", file=sys.stderr)

    if check and stale:
        print(f"\nout of date: {', '.join(map(str, stale))}", file=sys.stderr)
        return 1
    print(f"\nBuilt {len(sources)} page(s) into {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
