# hermes-skins

Four hand-built [Hermes](https://github.com/NousResearch/hermes-agent) skins —
**umbra**, **oracle**, **neuro**, **genesis** — each with generated ASCII art and
a palette that passes **WCAG 2.1 AA** throughout.

A Hermes skin is a single YAML file. No code, no plugins: the same file themes
the CLI, the TUI and the desktop app.

```bash
cp skins/umbra.yaml ~/.hermes/skins/
hermes config set display.skin umbra
```

> **Profiles:** `display.skin` does **not** propagate between profiles. Copy the
> file to `~/.hermes/profiles/<profile>/skins/` too, or that profile silently falls
> back to the `default` skin.

---

## The four

| Skin | Palette | Art | Mood |
|---|---|---|---|
| **umbra** | violet `#A78BFA` + cyan `#22D3EE` | an eye opening inside a targeting reticle | the balanced one |
| **oracle** | emerald `#5EE9B4` + cyan | an orthogonal grid with a node that emits | technical, flat, no "monster" |
| **neuro** | pink `#E86BB0` + violet | two somas, dendrites and an axon | organic, warm |
| **genesis** | ice blue `#A8C4FF` | a crystal shattered by an impact | sober, minimal |

All four share one idea: a near-black base, one saturated accent (or two), a
15–20 line braille figure that *faces you*, a figlet wordmark, its own prompt
symbol, 14 themed `tool_emojis`, and a closing line.

---

## Accessibility (the part most collections skip)

Every text colour is measured against **its own** status bar. Existing
community skins fail this: the popular *mythos* skin drops to **3.6:1** on
`status_bar_dim`, well under the 4.5:1 AA threshold.

Here, the worst colour in each skin:

| skin | lowest contrast |
|---|---|
| umbra | 6.40:1 |
| oracle | 6.27:1 |
| neuro | 6.37:1 |
| genesis | 5.29:1 |

All above AA, no exceptions.

---

## Regenerating the art

The braille is never hand-drawn. `theme_art.py` renders each motif with real
geometry (the almond of an eyelid, recursive dendrites, the crack through a
crystal) onto a 2×4-dots-per-cell grid, then maps per-cell brightness onto a
colour ramp.

```bash
python3 build_all_skins.py ~/.hermes/skins/   # regenerate all four YAMLs
python3 build_all_skins.py ./skins/           # or just into the repo
python3 theme_art.py umbra                    # print one motif as Rich markup
```

> **Look at the output.** The first pass of all four motifs came out wrong — the
> eye read as a flower, neurosyn as noise. They only improved after rasterising
> to PNG and actually looking. `theme_art.py` writes `art-<motif>.png` for
> exactly that reason.

**Why the art is never pasted by hand:** a YAML literal block fixes its
indentation at its first line, and any line indented *less* terminates the
block. This art has lines at column 0, so hand-copying silently breaks the
file. `yaml_art()` rebases every line on the first line's margin.

---

## Layout

```
skins/              the four installable YAMLs
theme_art.py        the four braille motifs (geometry)
build_all_skins.py  generates the full YAMLs from theme_art.py
LICENSE             MIT
```

## Install one

```bash
cp skins/<name>.yaml ~/.hermes/skins/
hermes config set display.skin <name>
```

## License

MIT. The skin *format* follows [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent);
the art and palettes are original to this repository.
