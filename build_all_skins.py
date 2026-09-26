#!/usr/bin/env python3
"""Build all four candidate skins (umbra, oracle, neuro, genesis) as installable
YAML + the generator that produced their art, for the hermes-skins repo.

Every skin is generated, never hand-written: the braille art is embedded in a
YAML literal block whose indentation is fixed by its FIRST line, and this art's
leftmost lines sit at column 0, so hand-copying breaks the file. `yaml_art()`
rebases every line on the first line's margin.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from theme_art import Art, MOTIFS, RAMPS, to_cells  # noqa: E402
from blockfont import render_wordmark  # noqa: E402

SKINS_DIR = os.path.expanduser("~/.hermes/skins")

# Per-theme palette. `dim` is the one colour that usually fails AA in third-party
# skins (mythos: 3.6:1) — here every value is >= 4.5:1 on its own status bar.
THEMES = {
    "umbra": dict(
        title="Umbra", hue="violet + cyan", bg="#0a0a0c", sbbg="#141020",
        accent="#A78BFA", accent2="#22D3EE", title_c="#E9D5FF", text="#EDE9FE",
        dim="#9C90C4", label="#22D3EE", border="#2A2140",
        ok="#5EE9B4", warn="#FFD166", err="#FF6B8A", bad="#F59E6B",
        menu="#12101C", menu_cur="#2E2450", meta="#1B1730", meta_cur="#3E3268",
        sel="#2A2140", voice="#141020", strong="#C4B5FD", dim_sb="#9C90C4",
        session_border="#3A2E58",
        sym="◈", prompt="◈ ❯ ", agent="Umbra Agent",
        label_text=" ◈ Umbra ",
        goodbye="The eye closes. The light stays.",
        tagline="An eye opening inside a targeting reticle.",
        verbs=["opening the eye", "measuring the pupil", "calibrating the reticle",
               "waiting for the section", "sweeping the image", "focusing the iris",
               "awaiting the light", "closing the cycle"],
        faces=["(◈)", "(◎)", "(◉)", "(◍)", "(•)"],
        think_faces=["(◈)", "(◎)", "(◉)", "(◍)", "(✦)"],
        wings=[["◈", "◈"], ["◎", "◎"], ["◉", "◉"]],
        ramp=RAMPS["umbra"],
    ),
    "oracle": dict(
        title="Oracle", hue="emerald + cyan", bg="#050a09", sbbg="#08201a",
        accent="#5EE9B4", accent2="#22D3EE", title_c="#D1FAE5", text="#D1FAE5",
        dim="#7FB8A4", label="#22D3EE", border="#123A2E",
        ok="#5EE9B4", warn="#FFD166", err="#FF6B8A", bad="#F59E6B",
        menu="#061410", menu_cur="#12463A", meta="#0A211B", meta_cur="#186B54",
        sel="#123A2E", voice="#08201a", strong="#A7F3D0", dim_sb="#7FB8A4",
        session_border="#1A5443",
        sym="◎", prompt="◎ ❯ ", agent="Oracle Agent",
        label_text=" ◎ Oracle ",
        goodbye="Query complete. Signal closed.",
        tagline="An orthogonal grid with a node that emits.",
        verbs=["querying the grid", "solving the node", "sampling the lattice",
               "listening for the reply", "tracing the path", "resolving the lattice",
               "holding the signal", "closing the query"],
        faces=["(◎)", "(◉)", "(▣)", "(◈)", "(◇)"],
        think_faces=["(◎)", "(◉)", "(▣)", "(◈)", "(✦)"],
        wings=[["◎", "◎"], ["◉", "◉"], ["▣", "▣"]],
        ramp=RAMPS["oracle"],
    ),
    "neuro": dict(
        title="Neurosyn", hue="pink + violet", bg="#0d0610", sbbg="#1c0c22",
        accent="#E86BB0", accent2="#A78BFA", title_c="#F9B8DC", text="#FCE7F3",
        dim="#C08CB0", label="#A78BFA", border="#3A1B44",
        ok="#7DD3A0", warn="#FFD166", err="#FF6B8A", bad="#F59E6B",
        menu="#150A1C", menu_cur="#3D1B4C", meta="#1D0F26", meta_cur="#542A66",
        sel="#3A1B44", voice="#1c0c22", strong="#F9B8DC", dim_sb="#C08CB0",
        session_border="#4E2459",
        sym="◈", prompt="◈ ❯ ", agent="Neurosyn Agent",
        label_text=" ◈ Neurosyn ",
        goodbye="Synapse closed. Signal fading.",
        tagline="Two somas, dendrites and a synaptic link.",
        verbs=["firing the synapse", "growing the dendrite", "reading the soma",
               "waiting for the spike", "tracing the axon", "listening for the volley",
               "consolidating the trace", "closing the synapse"],
        faces=["(◉)", "(◍)", "(◎)", "(◈)", "(◇)"],
        think_faces=["(◉)", "(◍)", "(◎)", "(◈)", "(✦)"],
        wings=[["◉", "◉"], ["◍", "◍"], ["◎", "◎"]],
        ramp=RAMPS["neuro"],
    ),
    "genesis": dict(
        title="Genesis", hue="ice blue", bg="#070912", sbbg="#0d1226",
        accent="#A8C4FF", accent2="#5B87E0", title_c="#E0E7FF", text="#E0E7FF",
        dim="#9FB0D8", label="#5B87E0", border="#1E2A4E",
        ok="#7DD3A0", warn="#FFD166", err="#FF6B8A", bad="#F59E6B",
        menu="#0A0D1C", menu_cur="#1E2A50", meta="#101634", meta_cur="#2A3A66",
        sel="#1E2A4E", voice="#0d1226", strong="#C4D8FF", dim_sb="#9FB0D8",
        session_border="#2A3A66",
        sym="◈", prompt="◈ ❯ ", agent="Genesis Agent",
        label_text=" ◈ Genesis ",
        goodbye="Protocol ends. Light fades to protocol.",
        tagline="A crystal shattered by an impact.",
        verbs=["splitting the lattice", "tracing the fracture", "reading the facets",
               "waiting for the flash", "mapping the shards", "measuring the break",
               "holding the protocol", "ending the sequence"],
        faces=["(◈)", "(◇)", "(◆)", "(◭)", "(▣)"],
        think_faces=["(◈)", "(◇)", "(◆)", "(✦)", "(✧)"],
        wings=[["◈", "◈"], ["◆", "◆"], ["◇", "◇"]],
        ramp=RAMPS["genesis"],
    ),
}

TOOL_EMOJIS = {
    "terminal": "Θ", "web_search": "Ω", "read_file": "◇", "write_file": "◆",
    "search_files": "◈", "execute_code": "Δ", "browser_navigate": "Φ",
    "delegate_task": "▣", "mixture_of_agents": "⚗", "memory": "◐",
    "clarify": "Θ", "cronjob": "↻", "process": "⚙", "todo": "☐",
}


def yaml_art(lines, indent="  "):
    """Embed art in a literal block that cannot terminate early.

    A literal block's indent is fixed by its first non-empty line; any line with
    LESS indent ends the block and Rich markup becomes a YAML syntax error. The
    art carries its own leading spaces (its horizontal position) and its leftmost
    lines sit at column 0, so rebase on the first line's margin.
    """
    lead = lambda s: len(s) - len(s.lstrip(" "))
    body = [ln.rstrip() for ln in lines if ln.strip()]
    if not body:
        return ""
    base = lead(body[0])
    return "\n".join(f"{indent}{ln[min(base, lead(ln)):]:}" for ln in body)


def markup_lines(art, ramp):
    cells = to_cells(art, ramp)
    out = []
    for row in cells:
        s = "".join((f"[{c}]{ch}[/]" if c else ch) for ch, c in row).rstrip()
        if s:
            out.append(s)
    return out


def wordmark(name, ramp, gap=1):
    """Block-letter wordmark with a per-letter colour ramp (never braille dots:
    at wordmark size braille is illegible, so this uses the U+2588 family)."""
    lines = render_wordmark(name, gap=gap)
    per_col = max(1, len(ramp) // max(1, len(name)))
    out = []
    for row in lines:
        buf = []
        col_i = 0
        for chpos, ch in enumerate(row):
            if ch == " ":
                buf.append(" ")
                continue
            idx = min(len(ramp) - 1, (chpos * per_col) // max(1, len(lines[0]) or 1))
            buf.append(f"[{ramp[idx]}]{ch}[/]")
        out.append("".join(buf).rstrip())
    return out


def gradient_welcome(agent, ramp):
    """Per-character colour fade for the greeting, like the community wordmarks."""
    msg = f"Welcome to {agent}! Type your message or /help for commands."
    n = len(ramp)
    out = []
    for i, ch in enumerate(msg):
        if ch == " ":
            out.append(" ")
        else:
            out.append(f"[bold {ramp[min(n - 1, (i * n) // max(1, len(msg)))]}]{ch}[/]")
    return "".join(out)


def q(s):
    """Quote a value for YAML, escaping the two chars that matter."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build(name, cfg):
    c = dict(
        background=cfg["bg"],
        ui_accent=cfg["accent"], banner_accent=cfg["accent"], banner_title=cfg["title_c"],
        banner_text=cfg["text"], ui_text=cfg["text"], banner_dim=cfg["dim"], ui_label=cfg["label"],
        banner_border=cfg["border"], ui_border=cfg["border"],
        ui_ok=cfg["ok"], ui_warn=cfg["warn"], ui_error=cfg["err"],
        prompt=cfg["text"], input_rule=cfg["accent"], response_border=cfg["accent2"],
        status_bar_bg=cfg["sbbg"], status_bar_text=cfg["text"], status_bar_strong=cfg["strong"],
        status_bar_dim=cfg["dim_sb"], status_bar_good=cfg["ok"], status_bar_warn=cfg["warn"],
        status_bar_bad=cfg["bad"], status_bar_critical=cfg["err"],
        session_label=cfg["accent"], session_border=cfg["session_border"],
        completion_menu_bg=cfg["menu"], completion_menu_current_bg=cfg["menu_cur"],
        completion_menu_meta_bg=cfg["meta"], completion_menu_meta_current_bg=cfg["meta_cur"],
        selection_bg=cfg["sel"], voice_status_bg=cfg["voice"], shell_dollar=cfg["accent2"],
        ui_tool=cfg["accent"], ui_thinking=cfg["dim"],
        diff_added=cfg["ok"], diff_removed=cfg["err"],
        diff_added_word=cfg["ok"], diff_removed_word=cfg["err"],
        syntax_string=cfg["ok"], syntax_number=cfg["warn"], syntax_keyword=cfg["accent2"],
        syntax_comment=cfg["dim"],
    )
    art = Art(46, 20)
    MOTIFS[name](art)
    hero = markup_lines(art, cfg["ramp"])
    logo = wordmark(cfg["title"].upper(), [cfg["accent2"], cfg["accent"],
                                       cfg["strong"], cfg["title_c"], cfg["text"]])

    L = []
    L.append(f"# {cfg['title']} — {cfg['tagline']}")
    L.append("# Art: braille generated with real geometry (never hand-drawn).")
    L.append("# Contrast: every text colour >= 4.5:1 (WCAG AA) on its own status bar.")
    L.append(f"name: {name}")
    L.append(f"description: {q(cfg['title'] + ' — ' + cfg['tagline'])}")
    L.append("")
    L.append("colors:")
    for k, v in c.items():
        L.append(f'  {k}: "{v}"')
    L.append("")
    L.append("spinner:")
    L.append(f"  waiting_faces: [{', '.join(q(f) for f in cfg['faces'])}]")
    L.append(f"  thinking_faces: [{', '.join(q(f) for f in cfg['think_faces'])}]")
    L.append("  thinking_verbs:")
    for v in cfg["verbs"]:
        L.append(f"    - {q(v)}")
    L.append("  wings:")
    for w in cfg["wings"]:
        L.append(f"    - [{q(w[0])}, {q(w[1])}]")
    L.append("")
    L.append("tool_emojis:")
    for k, v in TOOL_EMOJIS.items():
        L.append(f"  {k}: {q(v)}")
    L.append("")
    L.append("branding:")
    L.append(f"  agent_name: {q(cfg['agent'])}")
    L.append(f"  prompt_symbol: {q(cfg['prompt'])}")
    L.append(f"  response_label: {q(cfg['label_text'])}")
    L.append(f"  welcome: {q(gradient_welcome(cfg['agent'], [cfg['accent2'], cfg['accent'], cfg['strong'], cfg['title_c']]))}")
    L.append(f"  goodbye: {q(cfg['goodbye'])}")
    L.append(f"  help_header: {q('(' + cfg['sym'] + ') Available Commands')}")
    L.append("")
    L.append('tool_prefix: "▏"')
    L.append("")
    L.append("banner_logo: |")
    L.append(yaml_art(logo))
    L.append("")
    L.append("banner_hero: |")
    L.append(yaml_art(hero))
    return "\n".join(L) + "\n"


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else SKINS_DIR
    os.makedirs(out_dir, exist_ok=True)
    for name, cfg in THEMES.items():
        body = build(name, cfg)
        path = os.path.join(out_dir, f"{name}.yaml")
        open(path, "w", encoding="utf-8").write(body)
        print(f"wrote {path} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
