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

## Why the art breaks (and how the tests catch it)

`banner_hero` and `banner_logo` are not free-form. In `hermes_cli/banner.py`:

* `banner_logo` prints **only** when the terminal is **>= 95 columns**, above the
  panel.
* `banner_hero` is pasted into a `Table` row (line 1019) inside a
  `Panel(padding=(0, 2))`, sharing the row with a right-hand column of
  model/cwd/tool lines.

So a hero line wider than ~46 columns gets **wrapped by Rich, shearing the figure
in half** — no error, just a ruined drawing. And a logo wider than the panel is
silently clipped. Braille is 2x4 dots per cell, so a wordmark drawn as braille
*dots* is illegible at wordmark size; these use the solid `█` block family.

`test_art_rescale.py` enforces all of it:

```bash
python3 test_art_rescale.py            # test the repo's skins/
python3 test_art_rescale.py /tmp/out   # test freshly generated output
```

It measures every art line with `rich.cells.cell_len` (markup excluded), renders
each skin for real at **80, 95, 100, 120 and 160 columns**, and fails if Rich
would wrap or clip anything, if a logo is missing or too wide for the 95-column
threshold, if branding is incomplete, or if the greeting has no per-character
colour fade.

---

## The ASCII conventions (and one that is wrong)

`test_art_rescale.py` enforces two things that a naive generator gets wrong.

**1. Colour the ramp smoothly, per cell.** The first umbra ramp ran
`259,260,260,255,269,188` degrees of hue — an **81-degree jump** between the two
brightest tones (violet straight to cyan). With per-cell colouring that becomes
visible banding across the iris. The ramps now interpolate hue in 7 steps with a
**max step of 14 degrees**, and the test fails any ramp that jumps more than 20.

**2. Do NOT paint the background with U+2800.** Several popular skins fill the
figure's bounding box with `U+2800` (blank braille). A terminal draws U+2800 as
a **visible dotted cell** — it is real ink, not transparent space — so the figure
ends up inside a field of placeholder boxes. Verified directly: in a font without
real braille, U+2800 renders with *exactly the same* ink as U+28FF (a tofu box).

Negative space is therefore real spaces, and the hero is cropped to the figure's
real bounding box (22-46 columns) instead of padded out to a rectangle.

Each skin signs its art with a letter-spaced tagline in the dim tone
(`♥ u m b r a`, `◆ q u e r y`) and a `welcome` greeting faded per character.

---

## Why the art breaks (and how the tests catch it)

`banner_hero` and `banner_logo` are not free-form. In `hermes_cli/banner.py`:

* `banner_logo` prints **only** when the terminal is **>= 95 columns**, above the
  panel.
* `banner_hero` is pasted into a `Table` row (line 1019) inside a
  `Panel(padding=(0, 2))`, sharing the row with a right-hand column of
  model/cwd/tool lines.

So a hero line wider than ~46 columns gets **wrapped by Rich, shearing the figure
in half** — no error, just a ruined drawing. And a logo wider than the panel is
silently clipped. Braille is 2x4 dots per cell, so a wordmark drawn as braille
*dots* is illegible at wordmark size; these use the solid `█` block family.

`test_art_rescale.py` enforces all of it:

```bash
python3 test_art_rescale.py            # test the repo's skins/
python3 test_art_rescale.py /tmp/out   # test freshly generated output
```

It measures every art line with `rich.cells.cell_len` (markup excluded), renders
each skin for real at **80, 95, 100, 120 and 160 columns**, and fails if Rich
would wrap or clip anything, if a logo is missing or too wide for the 95-column
threshold, if branding is incomplete, or if the greeting has no per-character
colour fade.

---

## The ASCII conventions (reverse-engineered)

Every skin in the reference collection follows three rules that a naive
generator gets wrong. Measured across the 16 reference skins (374 art lines):

| | reference | naive per-cell |
|---|---|---|
| spans per line | **2.33** | 23.9 |
| tones per line | **2.33** | 3.6 |
| background | **U+2800** blank braille | spaces |

1. **Colour by role, not per pixel.** ~2 tones per line: a muted frame and a
   bright figure. Per-cell ramps read as noise and cost 9x the markup.
2. **The background is U+2800** (blank braille), never U+0020, so the art is a
   solid braille field instead of holes.
3. **One `[color]...[/]` span wraps the run.** `test_art_rescale.py` rejects a
   skin that exceeds 2.6 tones/line, 6 spans/line, or uses real spaces.

Each skin also signs its art with a letter-spaced tagline in the dim tone
(`♥ u m b r a`, `◆ q u e r y`) and a `welcome` greeting faded per character —
the way the reference wordmarks do.

---

## Layout

```
skins/                the four installable YAMLs
theme_art.py          the four braille motifs (geometry)
blockfont.py          5x5 block-letter font for the wordmarks
build_all_skins.py    generates the full YAMLs from theme_art.py + blockfont.py
test_art_rescale.py   width/render tests (see above)
LICENSE               MIT
```

## Install one

```bash
cp skins/<name>.yaml ~/.hermes/skins/
hermes config set display.skin <name>
```

## License

MIT. The skin *format* follows [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent);
the art and palettes are original to this repository.
