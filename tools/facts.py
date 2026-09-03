#!/usr/bin/env python3
"""Check the documentation against the source it documents.

The site is hand-written prose about three codebases that keep moving. This
reads the ground truth out of those codebases — the flags pytest_addoption
registers, the ini keys addini declares, the inputs and outputs in action.yml,
the commands and settings in the extension's package.json — and reports any
name the docs use that no longer exists, plus a short list of facts that are
easy to get wrong and expensive to get wrong.

Point it at the repos with --repos if they do not sit beside this one:

    python3 tools/facts.py
    python3 tools/facts.py --repos ~/src
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

DEFAULT_SIBLINGS = ROOT.parent
NAMES = {
    "lib": "pytest-html-reporter",
    "action": "pytest-html-reporter-actions",
    "vscode": "pytest-html-reporter-vscode",
}

problems: list[str] = []
skipped: list[str] = []
checked = 0


def fail(msg: str) -> None:
    problems.append(msg)


def site_text() -> str:
    parts = [(ROOT / "index.html").read_text(encoding="utf-8")]
    parts += [p.read_text(encoding="utf-8") for p in sorted(CONTENT.glob("*.html"))]
    return html.unescape("\n".join(parts))


def note_ver(msg: str) -> None:
    skipped.append(msg)


def where(token: str) -> list[str]:
    """Which fragments mention this token."""
    hits = []
    pat = re.compile(r"(?<![\w./-])" + re.escape(token) + r"(?![\w./-])")
    for p in [ROOT / "index.html"] + sorted(CONTENT.glob("*.html")):
        if pat.search(html.unescape(p.read_text(encoding="utf-8"))):
            hits.append(p.name)
    return hits


# ----------------------------------------------------------------- the library


def check_library(repo: Path, text: str) -> None:
    global checked
    plugin = (repo / "pytest_html_reporter" / "plugin.py")
    if not plugin.exists():
        skipped.append(f"library: no {plugin}")
        return
    src = plugin.read_text(encoding="utf-8")

    real_flags = set(re.findall(r'addoption\(\s*["\'](--[a-z0-9-]+)["\']', src))
    real_ini = set(re.findall(r'addini\(\s*["\']([a-z0-9_]+)["\']', src))

    # The standalone console-script is a separate argparse surface in cli.py.
    # Its flags are documented on the same page, so they belong in the same set.
    cli = repo / "pytest_html_reporter" / "cli.py"
    if cli.exists():
        real_flags |= set(re.findall(r'["\'](--[a-z0-9-]+)["\']', cli.read_text(encoding="utf-8")))

    # Flags the docs mention that the plugin does not register. pytest's own
    # options are excluded — the docs discuss them on purpose.
    PYTEST_OWN = {
        "--capture", "--cov", "--cov-branch", "--cov-report", "--co", "--collect-only",
        "--html", "--junit-xml", "--junitxml", "--log-cli-level", "--log-level",
        "--maxfail", "--numprocesses", "--reruns", "--reruns-delay", "--tb",
        "--version", "--help", "--no-header", "--strict-markers", "--rootdir",
        "--install-extension", "--dist", "--verbose", "--quiet", "--color",
    }
    #             ends on an alphanumeric, so a prose stem like "--report-" is not a flag
    used = set(re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*[a-z0-9])(?![\w-])", text))
    used = {f for f in used if len(f) > 4}
    unknown = sorted(f for f in used - real_flags - PYTEST_OWN if f.startswith(("--html", "--report", "--archive", "--title", "--junit")))
    for f in unknown:
        fail(f"flag {f} is documented in {', '.join(where(f))} but plugin.py registers no such option")
    checked += len(used)

    # ini keys, same idea
    #                                                              not followed by .py — that is a module
    used_ini = set(re.findall(
        r"(?<![\w.-])(report_[a-z_]+|archive_[a-z_]+|html_report)(?![\w-])(?!\.py)", text))
    for k in sorted(used_ini - real_ini):
        fail(f"ini key {k} is documented in {', '.join(where(k))} but plugin.py declares no such key")
    checked += len(used_ini)

    # A handful of specific, load-bearing facts.
    reporter = (repo / "pytest_html_reporter" / "html_reporter.py")
    if reporter.exists():
        m = re.search(r"['\"](pytest_html_report[a-z_]*\.html)['\"]", reporter.read_text(encoding="utf-8"))
        if m:
            real = m.group(1)
            checked += 1
            for w in ("pytest_html_reporter.html", "pytest-html-report.html"):
                if w == real or w not in text:
                    continue
                for page in where(w):
                    body = (ROOT / page).read_text(encoding="utf-8") if page == "index.html" \
                        else (CONTENT / page).read_text(encoding="utf-8")
                    if real in body:
                        # The page also uses the right name, so this is most likely a
                        # deliberate quotation of the stale README. Worth seeing, not failing.
                        note_ver(f"{page} contains {w} as well as the correct {real} — "
                                 f"check it is a quotation and not a slip")
                    else:
                        fail(f"the default report filename is {real}, but {page} says {w}")

    init = (repo / "pytest_html_reporter" / "__init__.py")
    setup = (repo / "setup.py")
    ver = None
    for f in (init, setup):
        if f.exists():
            m = re.search(r'__version__\s*=\s*["\']([\d.]+)["\']|version\s*=\s*["\']([\d.]+)["\']',
                          f.read_text(encoding="utf-8"))
            if m:
                ver = m.group(1) or m.group(2)
                break
    if ver:
        checked += 1
        if ver not in text:
            fail(f"the library version is {ver}; no page mentions it")
        stale = [v for v in re.findall(r"\bv?0\.[0-9]+\.[0-9]+\b", text) if v.lstrip("v") > ver]
        if stale:
            fail(f"docs mention version(s) newer than setup.py's {ver}: {', '.join(sorted(set(stale)))}")

    # Public API surface
    if init.exists():
        itext = init.read_text(encoding="utf-8")
        names = set(re.findall(r'["\']([A-Za-z_]\w*)["\']', itext))          # __all__
        for chunk in re.findall(r"^from .* import (.+)$", itext, re.M):
            for n in chunk.strip("()").split(","):
                n = n.strip()
                if not n:
                    continue
                names.add(n.split(" as ")[-1].strip())   # the alias is the public name
        api_used = set(re.findall(r"from pytest_html_reporter import ([^\n<]+)", text))
        for line in api_used:
            for n in [x.strip() for x in line.split(",") if x.strip()]:
                checked += 1
                if names and n not in names and n.isidentifier():
                    fail(f"the docs import {n} from pytest_html_reporter, which does not export it")


# ------------------------------------------------------------------ the action


def check_action(repo: Path, text: str) -> None:
    global checked
    y = repo / "action.yml"
    if not y.exists():
        skipped.append(f"action: no {y}")
        return
    src = y.read_text(encoding="utf-8")

    def block(name: str) -> list[str]:
        m = re.search(rf"^{name}:\n(.*?)^\w", src, re.S | re.M)
        return re.findall(r"^  ([a-z0-9_-]+):", m.group(1), re.M) if m else []

    inputs, outputs = set(block("inputs")), set(block("outputs"))
    page = CONTENT / "github-action.html"
    if not page.exists():
        return
    ptext = html.unescape(page.read_text(encoding="utf-8"))

    # `with:` keys the page uses that the action does not accept
    for m in re.finditer(r"^\s{4}([a-z][a-z0-9-]+):\s", ptext, re.M):
        k = m.group(1)
        if k in inputs or k in {"uses", "with", "run", "name", "if", "env", "id", "shell"}:
            continue
        if k in {"python-version", "fetch-depth", "path", "ref", "token"}:
            continue  # belongs to other actions in the same example
        # only complain about things that look like ours
        if k.startswith(("report", "archive", "artifact", "comment", "history", "fail", "min", "job", "summary", "pages")):
            fail(f"github-action.html uses input '{k}', which action.yml does not declare")
    checked += len(inputs)

    missing = sorted(i for i in inputs if not re.search(r"(?<![\w-])" + re.escape(i) + r"(?![\w-])", ptext))
    if missing:
        fail(f"action inputs never documented: {', '.join(missing)}")
    missing_o = sorted(o for o in outputs if not re.search(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", ptext))
    if missing_o:
        fail(f"action outputs never documented: {', '.join(missing_o)}")
    checked += len(outputs)


# ------------------------------------------------------------------ the editor


def check_vscode(repo: Path, text: str) -> None:
    global checked
    pkg = repo / "package.json"
    if not pkg.exists():
        skipped.append(f"vscode: no {pkg}")
        return
    data = json.loads(pkg.read_text(encoding="utf-8"))
    contributes = data.get("contributes", {})
    commands = {c["command"] for c in contributes.get("commands", [])}
    settings = set(contributes.get("configuration", {}).get("properties", {}))

    page = CONTENT / "vscode.html"
    if not page.exists():
        return
    ptext = html.unescape(page.read_text(encoding="utf-8"))

    for token in set(re.findall(r"pytestHtmlReporter\.[A-Za-z.]+", ptext)):
        checked += 1
        if token not in commands and token not in settings:
            known = contributes.get("views", {})
            if any(token == v.get("id") for vs in known.values() for v in vs):
                continue
            if token == "pytestHtmlReporter.sidebar":
                continue
            fail(f"vscode.html names '{token}', which package.json declares as neither a command nor a setting")

    for c in sorted(commands - set(re.findall(r"pytestHtmlReporter\.[A-Za-z.]+", ptext))):
        fail(f"extension command never documented: {c}")
    for s in sorted(settings - set(re.findall(r"pytestHtmlReporter\.[A-Za-z.]+", ptext))):
        fail(f"extension setting never documented: {s}")

    ident = f"{data.get('publisher')}.{data.get('name')}"
    checked += 1
    if ident not in ptext:
        fail(f"vscode.html never gives the extension id {ident}")
    # package.json can carry a bump that has not shipped yet. What the docs
    # should name is the released version, which is the CHANGELOG's top entry.
    pkg_ver = data.get("version")
    log = repo / "CHANGELOG.md"
    released = None
    if log.exists():
        m = re.search(r"^##\s*\[?v?([\d.]+)\]?", log.read_text(encoding="utf-8"), re.M)
        released = m.group(1) if m else None
    if released and pkg_ver and released != pkg_ver:
        skipped.append(
            f"vscode: package.json is at {pkg_ver} but the CHANGELOG's latest release is "
            f"{released} — checking the docs against {released}")
    target = released or pkg_ver
    if target:
        checked += 1
        if target not in ptext:
            fail(f"vscode.html never gives the released extension version {target}")

    # An unreleased bump in package.json must not leak onto any page as "the
    # version". Check every page, not just this one.
    if released and pkg_ver and released != pkg_ver:
        for page_path in [ROOT / "index.html"] + sorted(CONTENT.glob("*.html")):
            body = html.unescape(page_path.read_text(encoding="utf-8"))
            if re.search(r"(?<![\w.])" + re.escape(pkg_ver) + r"(?![\w.])", body):
                fail(f"{page_path.name} names extension version {pkg_ver}, which package.json "
                     f"carries but the CHANGELOG has not released — the released version is {released}")



def main() -> int:
    base = DEFAULT_SIBLINGS
    if "--repos" in sys.argv:
        base = Path(sys.argv[sys.argv.index("--repos") + 1]).expanduser().resolve()

    text = site_text()
    for key, folder in NAMES.items():
        repo = base / folder
        if not repo.exists():
            skipped.append(f"{key}: {repo} not found")
            continue
        {"lib": check_library, "action": check_action, "vscode": check_vscode}[key](repo, text)

    print(f"Cross-checked {checked} name(s) against the source repos.")
    for s in skipped:
        print(f"  · skipped — {s}")

    if problems:
        print(f"\n{len(problems)} disagreement(s) between the docs and the source:", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        return 1
    print("\nThe docs and the source agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
