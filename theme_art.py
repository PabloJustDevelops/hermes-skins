#!/usr/bin/env python3
"""ASCII (braille) hero art for four candidate Hermes skins.

Each motif is drawn with real geometry into a 2x4-dots-per-cell grid, then
emitted as braille. Brightness (0..1) is tracked per pixel and maps to a color
ramp index, so a single line can carry a gradient — the same trick the repo's
best skins use.

Motifs
  A UMBRA     eye opening inside a reticle      (violet + cyan, 2 accents)
  B ORACLE    orthogonal grid, node emitting    (emerald + cyan)
  C NEUROSYN  soma, dendrites, synaptic knobs  (pink + violet)
  D GENESIS   fractured crystal, impact flash   (ice blue)

Output: Rich-markup lines (for the skin YAML) + per-cell colors (for the HTML
preview), so the preview shows EXACTLY what Rich will paint.
"""
import math

DOT = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
       (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80}


class Art:
    """Pixel canvas in braille-dot space (cols*2 x rows*4)."""

    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.W, self.H = cols * 2, rows * 4
        self.lum = [[-1.0] * self.W for _ in range(self.H)]

    def put(self, x, y, bright):
        px, py = int(round(x)), int(round(y))
        if 0 <= px < self.W and 0 <= py < self.H and bright > self.lum[py][px]:
            self.lum[py][px] = max(0.0, min(1.0, bright))

    def erase(self, x, y):
        px, py = int(round(x)), int(round(y))
        if 0 <= px < self.W and 0 <= py < self.H:
            self.lum[py][px] = -1.0

    def disc(self, cx, cy, r, bright, soft=0.45):
        for py in range(int(cy - r - 1), int(cy + r + 2)):
            for px in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(px - cx, py - cy)
                if d <= r + soft:
                    b = bright if d <= r - soft else bright * (1 - (d - (r - soft)) / (2 * soft + 1e-9))
                    self.put(px, py, b)

    def ring(self, cx, cy, r, thick, bright, gap=None, gap_bright=0.0):
        for py in range(int(cy - r - 2), int(cy + r + 3)):
            for px in range(int(cx - r - 2), int(cx + r + 3)):
                d = math.hypot(px - cx, py - cy)
                if r - thick / 2 <= d <= r + thick / 2:
                    if gap:
                        a = math.degrees(math.atan2(py - cy, px - cx)) % 360.0
                        for c, w in gap:
                            if (a - c) % 360.0 < w:
                                self.put(px, py, gap_bright)
                                break
                        else:
                            self.put(px, py, bright)
                    else:
                        self.put(px, py, bright)

    def line(self, x0, y0, x1, y1, b0, b1=None, width=0.7, dashed=None):
        b1 = b0 if b1 is None else b1
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) * 2))
        r = max(0.35, width / 2)
        for i in range(n + 1):
            t = i / n
            if dashed and (t * dashed[1]) % 1.0 > dashed[0]:
                continue
            self.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, b0 + (b1 - b0) * t, soft=0.3)

    def polyline(self, pts, b0, b1=None, width=0.7):
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            t0, t1 = i / (len(pts) - 1), (i + 1) / (len(pts) - 1)
            b = b0 if b1 is None else b0 + (b1 - b0) * t0
            b2 = b0 if b1 is None else b0 + (b1 - b0) * t1
            self.line(x0, y0, x1, y1, b, b2, width)

    def glyph(self, ch, cx, cy, bright, size=1.0):
        g = FONT.get(ch)
        if not g:
            return
        h, w = len(g), len(g[0])
        for j, rowtxt in enumerate(g):
            for i, c in enumerate(rowtxt):
                if c != " ":
                    self.disc(cx + (i - w / 2) * size, cy + (j - h / 2) * size, 0.5 * size, bright, soft=0.2)

    def frame(self, x0, y0, x1, y1, bright, tick=0, corner=0):
        self.line(x0, y0, x1, y0, bright, width=0.55)
        self.line(x1, y0, x1, y1, bright, width=0.55)
        self.line(x1, y1, x0, y1, bright, width=0.55)
        self.line(x0, y1, x0, y0, bright, width=0.55)
        if tick:
            n = int((x1 - x0) / tick)
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                self.disc(x, y0, 0.45, bright * 0.8, soft=0.2)
                self.disc(x, y1, 0.45, bright * 0.8, soft=0.2)
        if corner:
            L = 5
            for (ax, ay, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
                self.line(ax, ay, ax + dx * L, ay, bright, width=0.9)
                self.line(ax, ay, ax, ay + dy * L, bright, width=0.9)

    def braille(self, cx, cy):
        m = 0
        for dx in (0, 1):
            for dy in (0, 1, 2, 3):
                x, y = cx * 2 + dx, cy * 4 + dy
                if 0 <= x < self.W and 0 <= y < self.H and self.lum[y][x] >= 0:
                    m |= DOT[(dx, dy)]
        return chr(0x2800 + m) if m else " "

    def cell_bright(self, cx, cy):
        vals = [self.lum[cy * 4 + dy][cx * 2 + dx]
                for dx in (0, 1) for dy in (0, 1, 2, 3)
                if 0 <= cy * 4 + dy < self.H and 0 <= cx * 2 + dx < self.W
                and self.lum[cy * 4 + dy][cx * 2 + dx] >= 0]
        return max(vals) if vals else -1.0


# ------------------------------------------------------------------ motifs

def art_umbra(a: Art):
    """Almond eye inside a targeting reticle. Violet iris, cyan reticle."""
    cx, cy = a.W / 2, a.H / 2
    A, B = a.W * 0.34, a.H * 0.34          # almond half-width / half-height

    def lid(t):                              # pointed almond: sharp corners at t=+-1
        return B * (1.0 - t * t) ** 0.72

    n = 300
    for sign in (-1, 1):
        pts = [(cx + A * (-1 + 2 * i / n), cy + sign * lid(-1 + 2 * i / n)) for i in range(n + 1)]
        a.polyline(pts, 0.95, width=1.25)    # thick continuous lid

    ir = B * 0.94
    for py in range(a.H):
        for px in range(a.W):
            d = math.hypot(px - cx, py - cy)
            t = (px - cx) / A
            if abs(t) <= 1 and d <= min(lid(t), ir):
                ang = math.atan2(py - cy, px - cx)
                fib = 0.5 + 0.5 * math.cos(12 * ang)
                a.put(px, py, 0.26 + 0.26 * fib * (1 - d / max(ir, 1e-6)) + 0.10)
    a.ring(cx, cy, ir * 0.995, 0.5, 0.9)
    a.disc(cx, cy, ir * 0.40, 0.9, soft=0.2)          # pupil halo
    a.disc(cx, cy, ir * 0.27, 0.0, soft=0.10)         # dark pupil
    a.disc(cx - ir * 0.34, cy - ir * 0.36, ir * 0.12, 1.0, soft=0.25)   # catchlight

    # Reticle brackets + frame (cyan), and upper-lid crease for the "eyelid" cue.
    a.frame(cx - A * 1.22, cy - B * 1.55, cx + A * 1.22, cy + B * 1.55, 0.18, tick=6, corner=0.8)
    for s in (-1, 1):
        a.line(cx + s * A * 1.10, cy - B * 1.05, cx + s * A * 1.10, cy + B * 1.05, 0.60, width=0.85)
    a.polyline([(cx - A * 0.72, cy - B * 1.30), (cx, cy - B * 1.62), (cx + A * 0.72, cy - B * 1.30)],
               0.34, width=0.6)                      # upper crease
    a.line(cx, cy - B * 1.55, cx, cy - B * 1.05, 0.7, width=0.7)
    a.line(cx, cy + B * 1.05, cx, cy + B * 1.55, 0.7, width=0.7)


def art_oracle(a: Art):
    """Orthogonal grid with a node emitting beams. Emerald + cyan."""
    cx, cy = a.W / 2, a.H / 2
    span_x, span_y = a.W * 0.44, a.H * 0.42

    def fall(x, y):                                            # brightness falls off
        d = math.hypot((x - cx) / span_x, (y - cy) / span_y)
        return max(0.05, 0.42 * (1 - min(1.0, d) ** 1.35))

    step = 5
    x = int(cx % step)
    while x < a.W:
        for y in range(a.H):
            a.put(x, y, fall(x, y))
        x += step
    y = int(cy % step)
    while y < a.H:
        for xx in range(a.W):
            a.put(xx, y, fall(xx, y))
        y += step

    for i, r in enumerate((3.0, 6.4, 9.8, 13.2)):              # square rings
        b = 0.85 - i * 0.13
        for t in range(200):
            ang = t / 200 * math.tau
            # squarish radius
            rr = r * (1 + 0.16 * math.cos(4 * ang))
            a.disc(cx + math.cos(ang) * rr, cy + math.sin(ang) * rr, 0.45, b, soft=0.25)
    a.disc(cx, cy, 1.7, 1.0, soft=0.4)                          # core

    for ang in (0, math.pi / 2, math.pi, 3 * math.pi / 2):     # dashed beams
        dx, dy = math.cos(ang), math.sin(ang)
        a.line(cx + dx * 15, cy + dy * 15, cx + dx * 36, cy + dy * 36,
               0.8, 0.06, width=0.6, dashed=(0.55, 4))
    a.frame(cx - span_x * 0.94, cy - span_y * 0.92, cx + span_x * 0.94, cy + span_y * 0.92,
            0.22, tick=6, corner=0.8)


def art_neuro(a: Art):
    """Two connected somas with dendrites and synaptic knobs. Pink + violet."""
    cells = [(a.W * 0.36, a.H * 0.60, 9.0), (a.W * 0.68, a.H * 0.34, 6.2)]
    for cx, cy, r in cells:
        for py in range(a.H):
            for px in range(a.W):
                d = math.hypot(px - cx, py - cy)
                ang = math.atan2(py - cy, px - cx)
                rr = r * (1 + 0.14 * math.sin(3 * ang + 0.5) + 0.07 * math.sin(5 * ang))
                if d <= rr:
                    a.put(px, py, 0.60 + 0.30 * (1 - d / rr))

    def dendrite(x, y, ang, ln, wd, depth, bright):
        if depth == 0 or ln < 3.2:
            a.disc(x, y, 1.25, 1.0, soft=0.25)
            return
        n = max(7, int(ln * 2))
        px_, py_ = x, y
        for i in range(n + 1):
            t = i / n
            aa = ang + 0.34 * math.sin(t * 2.6 + depth * 1.3)
            nx, ny = x + math.cos(aa) * ln * t, y + math.sin(aa) * ln * t
            a.line(px_, py_, nx, ny, bright, bright, width=max(0.5, wd * (1 - 0.35 * t)))
            px_, py_ = nx, ny
        for s in (1, -1):
            dendrite(px_, py_, ang + s * 0.62, ln * 0.63, wd * 0.7, depth - 1, bright * 0.92)

    cx, cy, r = cells[0]
    for ang, ln, wd, br in ((-2.62, 16.0, 1.7, 0.95), (-2.10, 18.5, 1.8, 0.9),
                            (-1.45, 15.0, 1.6, 0.85), (-0.80, 16.5, 1.7, 0.88),
                            (-2.92, 12.0, 1.4, 0.72)):
        dendrite(cx + math.cos(ang) * r * 0.85, cy + math.sin(ang) * r * 0.85,
                 ang, ln, wd, 3, br)
    a.disc(cx, cy, 2.3, 0.95, soft=0.35)

    cx2, cy2, r2 = cells[1]
    for ang, ln, wd, br in ((-1.9, 11.0, 1.3, 0.8), (-1.15, 12.0, 1.3, 0.75), (-0.5, 9.5, 1.2, 0.7)):
        dendrite(cx2 + math.cos(ang) * r2 * 0.85, cy2 + math.sin(ang) * r2 * 0.85,
                 ang, ln, wd, 2, br)
    a.disc(cx2, cy2, 1.6, 0.95, soft=0.3)

    # Axon joining the two somas, with myelin dashes.
    ax0 = (cx + r * 0.8, cy - r * 0.35)
    ax1 = (cx2 - r2 * 0.9, cy2 + r2 * 0.35)
    n = 30
    prev = ax0
    for i in range(1, n + 1):
        t = i / n
        cur = (ax0[0] + (ax1[0] - ax0[0]) * t + math.sin(t * 3.4) * 1.6,
               ax0[1] + (ax1[1] - ax0[1]) * t + math.sin(t * 4.1) * 2.2)
        a.line(prev[0], prev[1], cur[0], cur[1], 0.9, 0.9, width=1.6)
        if i % 4 == 0:
            a.line(prev[0], prev[1], cur[0], cur[1], 1.0, 1.0, width=2.2)
        prev = cur
    a.disc(ax1[0] + 1.2, ax1[1], 1.2, 1.0, soft=0.3)


def art_genesis(a: Art):
    """A crystal SHATTERED by an impact: the shell is open, one shard flies off.

    The break is what makes it read as "fractured" — the outer contour must be
    interrupted, not closed, and a displaced fragment must sit off-axis.
    """
    cx, cy = a.W / 2, a.H * 0.50
    R, r = a.H * 0.44, a.H * 0.27
    hexa = [(cx + math.cos(math.radians(90 + 60 * i)) * R,
             cy + math.sin(math.radians(90 + 60 * i)) * R * 0.92) for i in range(6)]
    inner = [(cx + (x - cx) * 0.46, cy + (y - cy) * 0.46) for x, y in hexa]

    # Impact point, left of centre so the crack has somewhere to run.
    ix, iy = cx - R * 0.16, cy - R * 0.10

    # Outer shell: draw each edge, but DROP the two edges near the impact (the gap
    # is the break) and dim the rest.
    for i in range(6):
        p0, p1 = hexa[i], hexa[(i + 1) % 6]
        if i in (0, 1):
            continue
        a.polyline([p0, p1], 0.30, 0.55, width=0.8)
    # Jagged remnants of the broken edges (stubs pointing at the gap).
    a.line(*hexa[0], *hexa[1], 0.0, width=0.0)  # no-op guard
    for t in (0.12, 0.30):
        x0 = hexa[0][0] + (hexa[1][0] - hexa[0][0]) * t
        y0 = hexa[0][1] + (hexa[1][1] - hexa[0][1]) * t
        a.line(x0, y0, x0 + 2.0, y0 - 1.6, 0.75, 0.2, width=0.6)
    for t in (0.16, 0.34):
        x0 = hexa[1][0] + (hexa[0][0] - hexa[1][0]) * t
        y0 = hexa[1][1] + (hexa[0][1] - hexa[1][1]) * t
        a.line(x0, y0, x0 - 2.0, y0 + 1.6, 0.75, 0.2, width=0.6)

    a.polyline(inner + [inner[0]], 0.45, width=0.55)          # inner facets
    for i in (0, 2, 4):
        a.line(inner[i][0], inner[i][1], hexa[i][0], hexa[i][1], 0.5, 0.18, width=0.5)

    # The crack: a jagged polyline from the impact crossing the shell.
    crack = [(ix, iy)]
    ang = math.radians(28)
    for k in range(1, 7):
        ang += (0.42 if k % 2 else -0.36)
        step = R * (0.20 if k < 5 else 0.26)
        px_, py_ = crack[-1]
        crack.append((px_ + math.cos(ang) * step, py_ + math.sin(ang) * step * 0.92))
    a.polyline(crack, 1.0, 0.10, width=1.25)   # thick: the crack IS the subject
    for k in (2, 4):                                            # hairline offshoots
        px_, py_ = crack[k]
        a.line(px_, py_, px_ + math.cos(ang + 1.2) * R * 0.20, py_ + math.sin(ang + 1.2) * R * 0.18,
               0.55, 0.08, width=0.45)
    a.disc(ix, iy, 2.1, 1.0, soft=0.5)                         # impact bloom
    # Carve a void around the crack so the two halves read as separate pieces.
    for (px_, py_) in crack:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) <= 2 and a.lum[int(py_) + dy][int(px_) + dx] < 0.45:
                    a.lum[int(py_) + dy][int(px_) + dx] = -1.0

    # The shard that flew off: a small triangle, displaced up-right.
    sx, sy = cx + R * 0.86, cy - R * 0.74
    shard = [(sx, sy), (sx + 4.2, sy + 1.4), (sx + 2.0, sy + 5.0), (sx, sy)]
    a.polyline(shard, 1.0, 0.75, width=0.9)
    a.disc(sx + 1.2, sy + 1.0, 0.6, 1.0, soft=0.25)

    # Debris.
    for k in range(4):
        aa = math.radians(196 + 42 * k)
        d0, d1 = R * 0.62, R * (0.80 + 0.10 * (k % 3))
        a.line(cx + math.cos(aa) * d0, cy + math.sin(aa) * d0 * 0.92,
               cx + math.cos(aa) * d1, cy + math.sin(aa) * d1 * 0.92, 0.55, 0.08, width=0.45)

    # Short flash only, under the crystal (a full-width band read as a
    # strike-through line and hid the break).
    yb = cy + R * 0.72
    for py in range(int(yb - 1.5), int(yb + 2)):
        for px in range(int(cx - R * 0.62), int(cx + R * 0.62)):
            f = max(0.0, 1 - abs(py - yb) / 2.0) * (1 - abs(px - cx) / (R * 0.62))
            base = a.lum[py][px]
            a.put(px, py, 0.30 * f if base < 0 else min(1.0, base + 0.30 * f))
    a.frame(cx - R * 1.34, cy - R * 1.20, cx + R * 1.34, cy + R * 1.20, 0.12, tick=7, corner=0.75)


MOTIFS = {"umbra": art_umbra, "oracle": art_oracle, "neuro": art_neuro, "genesis": art_genesis}


# ------------------------------------------------------------------ palette

RAMPS = {
    "umbra":   ["#2A1B4A", "#4C2E8A", "#7C4DDB", "#A78BFA", "#E9D5FF", "#22D3EE"],
    "oracle":  ["#04231C", "#0B4A38", "#12775A", "#1FBF87", "#5EE9B4", "#22D3EE"],
    "neuro":   ["#2A0F2E", "#6B1F5C", "#B03A8C", "#E86BB0", "#F9B8DC", "#A78BFA"],
    "genesis": ["#080B1E", "#1B2A5E", "#3559A8", "#5B87E0", "#A8C4FF", "#E0E7FF"],
}

SUBTITLES = {
    "umbra":   "◈ U M B R A   S Y S T E M S ◈",
    "oracle":  "◈ O R A C L E   N E T ◈",
    "neuro":   "◈ N E U R O S Y N   L I N K ◈",
    "genesis": "◈ G E N E S I S   P R O T O C O L ◈",
}
NAMES = {"umbra": "UMBRA", "oracle": "ORACLE", "neuro": "NEUROSYN", "genesis": "GENESIS"}

# Minimal 4x5 block font for the figlet-style wordmark.
FONT = {
    "A": [" ██ ", "█  █", "████", "█  █", "█  █"], "B": ["████ ", "█   █", "████ ", "█   █", "████ "],
    "C": [" ████", "█    ", "█    ", "█    ", " ████"], "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "G": [" ████", "█    ", "█  ██", "█   █", " ████"], "I": ["█████", "  █  ", "  █  ", "  █  ", "█████"],
    "L": ["█    ", "█    ", "█    ", "█    ", "█████"], "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"], "O": [" ██  ", "█  █ ", "█  █ ", "█  █ ", " ██  "],
    "R": ["████ ", "█   █", "████ ", "█ █  ", "█  █ "], "S": [" ████", "█    ", " ███ ", "    █", "████ "],
    "U": ["█   █", "█   █", "█   █", "█   █", " ███ "], "Y": ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    " ": ["    "] * 5, "◈": [" ██ ", "█  █", "█  █", "█  █", " ██ "],
}


def wordmark(name, bright_lo=0.55, bright_hi=1.0):
    """Figlet-style wordmark as braille-free block text, colored by column ramp."""
    word = NAMES[name]
    ramp = RAMPS[name]
    art = Art(len(word) * 5 + 1, 6)
    x = 2
    for ch in word:
        art.glyph(ch, x, art.H / 2, bright_hi, size=1.0)
        x += 5
    return art


# ------------------------------------------------------------------ render

def to_cells(art: Art, ramp, n_levels=None):
    """Per-cell (char, hex) with a brightness->ramp mapping, gravity-merged."""
    levels = n_levels or len(ramp)
    out = []
    for cy in range(art.rows):
        row = []
        for cx in range(art.cols):
            b = art.cell_bright(cx, cy)
            if b < 0:
                row.append((" ", None))
                continue
            i = min(levels - 1, int((b ** 0.85) * levels * 0.999))
            row.append((art.braille(cx, cy), ramp[i]))
        out.append(row)
    return out


def rich_lines(cells):
    """Collapse per-cell colors into Rich markup runs (keeps the YAML small)."""
    lines = []
    for row in cells:
        runs, cur, col = [], [], None
        for ch, c in row:
            if c != col:
                if cur and col:
                    runs.append((col, "".join(cur)))
                cur, col = [], c
            cur.append(ch)
        if cur and col:
            runs.append((col, "".join(cur)))
        s = "".join(f"[{c}]{t}[/]" if c else t for c, t in runs).rstrip()
        if s:
            lines.append(s)
    return lines


def render_png(art: Art, ramp, path, scale=9, pad=14):
    """Rasterize the braille to a PNG so the art can be eyeballed."""
    from PIL import Image
    w = art.W * scale + pad * 2
    h = art.H * scale + pad * 2
    img = Image.new("RGB", (w, h), (10, 10, 14))
    px = img.load()
    for y in range(art.H):
        for x in range(art.W):
            b = art.lum[y][x]
            if b < 0:
                continue
            i = min(len(ramp) - 1, int((b ** 0.85) * len(ramp) * 0.999))
            r, g, bl = int(ramp[i][1:3], 16), int(ramp[i][3:5], 16), int(ramp[i][5:7], 16)
            cx, cy = pad + x * scale, pad + y * scale
            for yy in range(cy, cy + scale):
                for xx in range(cx, cx + scale):
                    if 0 <= xx < w and 0 <= yy < h:
                        px[xx, yy] = (r, g, bl)
    img.save(path)
    return path


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(MOTIFS) if which == "all" else [which]
    for nm in names:
        a = Art(46, 20)
        MOTIFS[nm](a)
        for ln in rich_lines(to_cells(a, RAMPS[nm])):
            print(ln)
        print()
        render_png(a, RAMPS[nm], f"/home/pablorg/.hermes/cache/scratch/art-{nm}.png")
        print(f"# -> art-{nm}.png  ({a.cols}x{a.rows} cells)")
