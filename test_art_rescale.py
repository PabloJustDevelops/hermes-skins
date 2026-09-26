#!/usr/bin/env python3
"""Rescale tests for the skin banner art.

WHY THIS EXISTS
---------------
`banner_hero` and `banner_logo` are NOT free-form. In `hermes_cli/banner.py`:

  * `banner_logo` is printed ONLY when the terminal is >= 95 columns, and it is
    printed as a raw block ABOVE the panel (line 1030-1031).
  * `banner_hero` is pasted into a `Table` row (line 1019-1021) that lives inside
    a `Panel` with `padding=(0, 2)`, sharing the row with a right-hand column of
    model/cwd/tool lines.

Consequences that break art silently:

  1. A hero line wider than the available left column gets WRAPPED by Rich, which
     shears the figure in half across two lines. No error, just a ruined drawing.
  2. A logo wider than the panel simply gets clipped on the right.
  3. Braille is 2x4 dots per cell, so a logo drawn as *dots* is illegible; the
     repo's wordmarks use real block glyphs (U+2588 family) at 6-14 lines.

So every skin must declare a width budget, and these tests FAIL if the art
exceeds it or if Rich actually wraps/truncates it at a given terminal size.
"""
import os
import re
import sys

import yaml
from rich.cells import cell_len
from rich.console import Console

# banner.py: `if shutil.get_terminal_size().columns >= 95: print(banner_logo)`
LOGO_MIN_COLS = 95
# Below this the two-column Table gives the art too little room to survive.
MIN_SAFE_COLS = 80
# Widths to prove the art survives: the floor, the logo threshold, a wide term.
TEST_COLS = (80, 95, 100, 120, 160)

MARKUP = re.compile(r"\[/?[^\]]*\]")


def plain(line: str) -> str:
    """Strip Rich markup so we measure the glyphs the terminal actually draws."""
    return MARKUP.sub("", line)


def art_width(block: str) -> int:
    """Widest visual line in the art (markup excluded)."""
    return max((cell_len(plain(l)) for l in block.splitlines()), default=0)


def art_height(block: str) -> int:
    return len([l for l in block.splitlines() if l.strip()])


def nonblank_lines(block: str) -> list:
    return [l for l in block.splitlines() if l.strip()]


def check_no_wrap(block: str, budget: int, label: str, failures: list):
    """Every art line must fit the column, or Rich wraps and shears the figure."""
    over = [(i, cell_len(plain(l))) for i, l in enumerate(block.splitlines())
            if cell_len(plain(l)) > budget]
    if over:
        failures.append(
            f"{label}: {len(over)} line(s) exceed the {budget}col budget "
            f"(widest {max(w for _, w in over)}): lines {[i for i, _ in over][:6]}")
    return not over


def check_real_render(block: str, cols: int, label: str, failures: list):
    """Render for real and prove no art line was wrapped or split by Rich."""
    con = Console(width=cols, force_terminal=True, color_system="truecolor")
    with con.capture() as cap:
        con.print(block)
    out = cap.get()
    got = {cell_len(plain(l).rstrip()) for l in out.splitlines() if l.strip()}
    src = [cell_len(plain(l).rstrip()) for l in block.splitlines() if l.strip()]
    if not src:
        return
    # If Rich wrapped, the rendered width is <= cols and no line keeps its width.
    if max(got) < max(src) and max(src) <= cols:
        wrapped = [w for w in got if w not in src]
        if wrapped:
            failures.append(
                f"{label}: at {cols} cols Rich re-wrapped the art "
                f"(source widest {max(src)} -> rendered {sorted(got)[-3:]})")
    if max(src) > cols:
        failures.append(f"{label}: widest line {max(src)} > {cols} cols -> clipped")


def check_logo_threshold(block: str, failures: list, name: str):
    """A logo that only appears at >=95 cols is invisible on most terminals."""
    if not nonblank_lines(block):
        failures.append(f"{name}: banner_logo is EMPTY (never rendered)")
        return
    w = art_width(block)
    if w > 92:
        failures.append(
            f"{name}: banner_logo is {w} cols wide, so it only shows on very wide "
            f"terminals (>= {LOGO_MIN_COLS}); at {LOGO_MIN_COLS} it is clipped")


def check_repo_format(block, label, failures, is_logo=False):
    r"""Match the reference collection's ASCII conventions.

    Measured on joeynyc/hermes-skins (16 skins, 246 lines):
      * background painted with U+2800 (blank braille), never a real space;
      * ~1 tone per line, at most 2 - colour by ROLE, not per pixel;
      * 310/362 lines are a single `[color]...[/]` span.
    Per-cell spans (what a naive generator emits) run ~9x the markup and read
    as noise, so they are rejected here.
    """
    lines = [l for l in block.splitlines() if l.strip()]
    if not lines:
        return
    # 1. No real spaces in the art body: the reference uses U+2800. Counted on
    # the visible glyphs only (markup stripped), which is what the terminal
    # actually renders.
    spaces = sum(plain(l).count(" ") for l in lines)
    if spaces:
        failures.append(
            f"{label}: {spaces} real space(s) in the art; the reference skins paint "
            f"the background with U+2800 (blank braille)")
    # 2. Colour by role, not per pixel.
    tones, spans = [], []
    for l in lines:
        cs = re.findall(r"\[(?:bold |dim )?#[0-9A-Fa-f]{6}\]", l)
        tones.append(len(set(cs)))
        spans.append(len(cs))
    avg_t, avg_s = sum(tones) / len(tones), sum(spans) / len(spans)
    if avg_t > 2.6:
        failures.append(
            f"{label}: {avg_t:.2f} tones/line (reference is 1.04, max 2) - the art is "
            f"coloured per pixel and will read as noise")
    if avg_s > 6.0:
        failures.append(
            f"{label}: {avg_s:.2f} spans/line (reference is 2.8) - markup bloat that "
            f"also makes the YAML fragile")
    # 3. The art must actually paint a background.
    if sum(l.count("\u2800") for l in lines) == 0:
        failures.append(f"{label}: no U+2800 background at all")


def check_heritage(skins_dir: str, budget_for_hero, failures: list):
    """Full battery over every skin in the repo."""
    report = []
    for fn in sorted(os.listdir(skins_dir)):
        if not fn.endswith(".yaml"):
            continue
        path = os.path.join(skins_dir, fn)
        d = yaml.safe_load(open(path, encoding="utf-8"))
        name = d.get("name", fn[:-5])
        hero = d.get("banner_hero", "")
        logo = d.get("banner_logo", "")
        hw, hh = art_width(hero), art_height(hero)
        lw, lh = art_width(logo), art_height(logo)

        check_no_wrap(hero, budget_for_hero(name, hw), f"{name}.hero", failures)
        check_repo_format(hero, f"{name}.hero", failures)
        check_repo_format(logo, f"{name}.logo", failures)
        for cols in TEST_COLS:
            check_real_render(hero, cols, f"{name}.hero@{cols}", failures)
        check_logo_threshold(logo, failures, name)
        for cols in TEST_COLS:
            check_real_render(logo, cols, f"{name}.logo@{cols}", failures)

        # Branding completeness: the repo's skins all carry a gradient welcome.
        br = d.get("branding", {})
        for key in ("agent_name", "prompt_symbol", "response_label", "goodbye", "help_header"):
            if not br.get(key):
                failures.append(f"{name}: branding.{key} is missing/empty")
        if not re.search(r"\[/?(bold )?#[0-9A-Fa-f]{6}\]", br.get("welcome", "")):
            failures.append(
                f"{name}: branding.welcome has no per-character colour markup "
                f"(the repo wordmarks fade the greeting letter by letter)")

        report.append((name, hw, hh, lw, lh, len(d.get("colors", {})),
                       len(d.get("tool_emojis", {}))))
    return report


def main():
    # Default to the repo's own skins/; override with argv[1] (used to test
    # freshly generated output in a temp dir before installing it).
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    else:
        repo = os.path.join(here, "skins")
    if not os.path.isdir(repo):
        repo = os.path.expanduser("~/.hermes/skins")
    print(f"skins dir: {repo}\n")

    # The hero budget: it shares a Table row with the right column inside a
    # Panel(padding=(0,2)). Measured worst case leaves ~46 cols of art.
    BUDGET = 46

    def budget_for(name, measured):
        return BUDGET

    failures = []
    report = check_heritage(repo, budget_for, failures)

    print(f"{'skin':10s} {'heroW':>6s} {'heroH':>6s} {'logoW':>6s} {'logoH':>6s} {'col':>4s} {'emoji':>6s}")
    for name, hw, hh, lw, lh, nc, ne in report:
        print(f"{name:10s} {hw:6d} {hh:6d} {lw:6d} {lh:6d} {nc:4d} {ne:6d}")

    print(f"\n{'='*70}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)\n")
        for f in failures:
            print("  - " + f)
        return 1
    print(f"PASS: all skins survive {TEST_COLS} cols with a {BUDGET}col hero budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
