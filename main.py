#!/usr/bin/env python3
"""THE WORLD IN ONE DAY -- front page for Wednesday 25 November 2026.

A single self-contained program: it draws the whole front page with the
Python standard library only and writes a deterministic 1024x1024 PNG
to MAKEFUN_OUTPUT_DIR/entry.png (default /output). No network, no files
read at run time, no randomness, no timestamps.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---- palette ------------------------------------------------------------
PAPER = (247, 243, 232)
CARD = (250, 245, 232)
INK = (16, 24, 40)
FACT_D = (70, 72, 84)
CARD_LINE = (160, 150, 125)
DATE_GOLD = (201, 162, 39)
NAVY_D = (12, 24, 48)
OCEAN = (16, 42, 76)
LAND = (94, 138, 122)
LAND_EDGE = (150, 190, 172)
GRAT = (38, 74, 112)
OCEAN_LABEL = (110, 140, 175)
MUTED = (150, 168, 192)
WHITE = (255, 255, 255)
GOLD = (201, 162, 39)
RED = (224, 82, 66)
SKY = (90, 165, 225)
ORANGE = (232, 142, 44)
TEAL = (64, 178, 168)
VIOLET = (168, 130, 220)
MAGENTA = (232, 64, 160)
LIGHT_GREY = (214, 222, 232)
# GHOST was the faint in-box rule colour; removed with the 2nd revision
# (25 Nov, AT: all lines behind the text in the news boxes are gone).
KICK_GREY = (110, 105, 90)
GRAT_LINE = (28, 62, 104)
EQUATOR = (56, 100, 152)


def dim(col, frac):
    """Return a colour darkened toward black by the given fraction."""
    return (int(col[0] * frac), int(col[1] * frac), int(col[2] * frac))


# ---- PNG writer ----------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(path, canvas):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0: no filtering
        raw += canvas.buf[y * W * 3:(y + 1) * W * 3]
    body = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", body)
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(blob)


# ---- canvas --------------------------------------------------------------
class Page:
    def __init__(self):
        self.buf = bytearray(W * H * 3)

    def px(self, x, y, col):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]

    def fill(self, col):
        for i in range(0, W * H * 3, 3):
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]

    def rect(self, x, y, w, h, col):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = col[0]
                self.buf[i + 1] = col[1]
                self.buf[i + 2] = col[2]

    def hline(self, x0, x1, y, col):
        if y < 0 or y >= H:
            return
        if x0 > x1:
            x0, x1 = x1, x0
        for x in range(max(0, x0), min(W, x1 + 1)):
            i = (y * W + x) * 3
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]

    def vline(self, x, y0, y1, col):
        if x < 0 or x >= W:
            return
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(max(0, y0), min(H, y1 + 1)):
            i = (y * W + x) * 3
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]

    def line(self, x0, y0, x1, y1, col):
        """Bresenham line between two points."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, col)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, col):
        """Filled circle."""
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - half, cx + half, cy + dy, col)

    def ring(self, cx, cy, r, col):
        """Thin circle outline, drawn point by point."""
        steps = max(24, r * 8)
        for k in range(steps):
            a = 2.0 * math.pi * k / steps
            self.px(cx + int(round(r * math.cos(a))),
                    cy + int(round(r * math.sin(a))), col)
            self.px(cx + int(round((r - 1) * math.cos(a))),
                    cy + int(round((r - 1) * math.sin(a))), col)

    def tri(self, ax, ay, bx, by, cx, cy, col):
        """Filled triangle via barycentric test over its bounding box."""
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if den == 0:
            return
        x0 = max(0, min(ax, bx, cx))
        x1 = min(W - 1, max(ax, bx, cx))
        y0 = max(0, min(ay, by, cy))
        y1 = min(H - 1, max(ay, by, cy))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                w0 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den
                w1 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den
                w2 = 1.0 - w0 - w1
                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    self.px(x, y, col)

    def poly(self, pts, col):
        """Filled polygon via a scanline edge crossing pass."""
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(round(xs[k])), int(round(xs[k + 1])), y, col)

    def poly_line(self, pts, col):
        """Polygon outline, closed."""
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            self.line(x0, y0, x1, y1, col)

    def burst(self, cx, cy, r_out, r_in, spikes, col):
        """Starburst: alternating long/short rays out of a centre point."""
        for k in range(spikes * 2):
            ang = math.pi * k / spikes - math.pi / 2.0
            r = r_out if k % 2 == 0 else r_in
            x = cx + int(round(r * math.cos(ang)))
            y = cy + int(round(r * math.sin(ang)))
            self.line(cx, cy, x, y, col)

# ---- bitmap font ----------------------------------------------------------
# Second-generation 5x7 design, redrawn for this revision: 7 rows of 5
# pixels per glyph, open counters (barred I, short mid-bars on E/F,
# single-storey g with a tail) so letters stay distinct at small sizes.
# Capitals use the full height; lowercase sits on the x-height (rows
# 2-6) with descenders (g, j, p, q, y) dropping to row 6. "#" is a set
# pixel. All text is drawn with tracking (see draw_text): 2px at scale
# 2 and above, so no two letters ever touch -- the cramped look of the
# first version came from zero tracking plus bold overhang.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11100", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11100", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "10001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11110", "10000", "01110"),
    "f": ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "00000", "01110", "10001", "10001", "01110", "00100"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("00100", "00100", "01110", "00100", "00100", "00100", "00010"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "10001", "01111", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_w(s, scale, track=0):
    """Pixel width of a string at the given scale and tracking."""
    if not s:
        return 0
    adv = 5 * scale + track
    return len(s) * adv - track


def draw_text(pg, x, y, s, scale, col, bold=False, track=0):
    """Draw a string; each font pixel becomes scale x scale screen pixels.
    Bold adds a second pass shifted 1px right. Returns the drawn width."""
    cx = x
    for ch in s:
        rows = FONT.get(ch, BLANK)
        for ry in range(7):
            row = rows[ry]
            for rx in range(5):
                if row[rx] == "1":
                    pg.rect(cx + rx * scale, y + ry * scale, scale, scale, col)
                    if bold:
                        pg.rect(cx + rx * scale + 1, y + ry * scale,
                                scale, scale, col)
        cx += 5 * scale + track
    return cx - x - track


def draw_centred(pg, cx, y, s, scale, col, bold=False, track=0):
    """Draw a string centred on cx. Returns the left edge used."""
    w = text_w(s, scale, track) + (1 if bold else 0)
    x = cx - w // 2
    draw_text(pg, x, y, s, scale, col, bold, track)
    return x


def wrap(s, scale, track, maxw):
    """Greedy word wrap; returns a list of lines that fit maxw pixels."""
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale, track) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# ---- world map ------------------------------------------------------------
# Simplified coastline outlines from geographic knowledge, as (lon, lat)
# point lists. Antarctica is left out on purpose.

NORTH_AMERICA = [
    (-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69), (-85, 66),
    (-80, 73), (-65, 62), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
    (-80, 32), (-81, 26), (-84, 30), (-90, 29), (-97, 26), (-105, 22),
    (-97, 16), (-92, 15), (-86, 13), (-83, 9), (-79, 9), (-85, 11),
    (-90, 14), (-95, 16), (-100, 18), (-105, 20), (-110, 23), (-114, 29),
    (-120, 34), (-124, 40), (-124, 48), (-130, 55), (-140, 60), (-155, 58),
    (-165, 60),
]

GREENLAND = [
    (-45, 60), (-40, 64), (-30, 68), (-22, 70), (-25, 76), (-35, 80),
    (-50, 80), (-58, 76), (-55, 70), (-52, 64),
]

SOUTH_AMERICA = [
    (-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
    (-70, -23), (-70, -30), (-73, -37), (-73, -44), (-70, -52), (-66, -55),
    (-68, -50), (-65, -45), (-62, -40), (-57, -35), (-50, -30), (-41, -23),
    (-35, -9), (-35, -6), (-43, -3), (-50, 0), (-55, 5), (-60, 8),
    (-70, 11), (-77, 7),
]

AFRICA = [
    (-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-12, 8),
    (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (13, 0), (9, -4),
    (12, -10), (13, -17), (12, -26), (16, -29), (19, -34), (26, -34),
    (32, -29), (35, -24), (40, -16), (40, -11), (43, -12), (46, -11),
    (51, -11), (51, -2), (48, 2), (44, 5), (41, 11), (39, 15), (37, 18),
    (35, 22), (32, 27), (30, 31), (22, 33), (11, 34), (10, 37), (0, 36),
]

# Europe and Asia drawn as one landmass so no seam shows between them.
EURASIA = [
    (-9, 37), (-9, 43), (-2, 48), (1, 51), (7, 54), (8, 57), (12, 58),
    (10, 62), (18, 69), (25, 71), (35, 68), (50, 69), (68, 72), (80, 73),
    (100, 77), (115, 74), (130, 72), (150, 70), (162, 66), (178, 65),
    (170, 60), (162, 60), (158, 55), (156, 51), (142, 50), (140, 45),
    (135, 43), (130, 38), (127, 35), (122, 31), (120, 28), (118, 24),
    (112, 22), (108, 18), (106, 10), (104, 9), (100, 2), (98, 10),
    (97, 15), (94, 17), (92, 21), (89, 22), (86, 20), (82, 16), (80, 10),
    (77, 8), (76, 9), (73, 16), (70, 20), (66, 25), (61, 25), (57, 26),
    (54, 27), (52, 28), (50, 29), (48, 29), (52, 25), (56, 26), (59, 22),
    (58, 20), (55, 17), (52, 15), (48, 14), (44, 13), (43, 12), (40, 15),
    (38, 20), (36, 25), (35, 28), (34, 28), (33, 31), (35, 33), (36, 36),
    (33, 36), (30, 36), (27, 37), (26, 38), (23, 36), (22, 39), (20, 40),
    (18, 40), (16, 38), (15, 40), (13, 42), (10, 44), (8, 44), (6, 43),
    (3, 42), (0, 39), (-2, 37), (-6, 36),
]

AUSTRALIA = [
    (113, -22), (114, -30), (115, -35), (118, -35), (124, -33), (129, -32),
    (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (150, -37),
    (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
    (140, -17), (136, -15), (135, -12), (132, -11), (130, -13), (126, -14),
    (122, -17), (118, -20),
]

BRITAIN = [
    (-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
    (-3, 50),
]

JAPAN = [
    (130, 31), (132, 33), (134, 34), (136, 35), (138, 35), (140, 38),
    (141, 41), (142, 44), (144, 44), (143, 42), (141, 39), (139, 37),
    (137, 35), (133, 34),
]

NEW_GUINEA = [
    (131, -1), (136, -2), (141, -3), (146, -6), (150, -8), (147, -9),
    (143, -8), (138, -8), (134, -4),
]

MADAGASCAR = [
    (44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (45, -25),
    (43, -22),
]

SUMATRA = [
    (95, 5), (98, 2), (100, -1), (103, -3), (105, -5), (104, -3),
    (100, 0), (97, 3),
]

BORNEO = [
    (109, 1), (112, 3), (116, 6), (118, 2), (117, -2), (114, -3),
    (110, -3),
]

LANDS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
         AUSTRALIA, BRITAIN, JAPAN, NEW_GUINEA, MADAGASCAR, SUMATRA, BORNEO]

MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 24, 104, 1000, 384


def proj(lon, lat):
    """Equirectangular projection into the map rectangle."""
    x = 24 + (lon + 180) / 360.0 * 976
    y = 104 + (85 - lat) / 145.0 * 280
    return int(round(x)), int(round(y))


def draw_marker(pg, cx, cy, num, accent):
    """Numbered story marker: darkened halo, white ring, accent disc."""
    pg.disc(cx, cy, 18, dim(accent, 0.55))
    pg.disc(cx, cy, 14, WHITE)
    pg.disc(cx, cy, 12, accent)
    draw_centred(pg, cx, cy - 7, str(num), 2, NAVY_D, bold=True, track=1)


def draw_map(pg, stories):
    pg.rect(MAP_X0, MAP_Y0, MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0, OCEAN)
    # graticule every 30 degrees; the equator is drawn a little brighter
    for lon in range(-180, 181, 30):
        x, _ = proj(lon, 0)
        pg.vline(x, MAP_Y0, MAP_Y1 - 1, GRAT_LINE)
    for lat in range(-60, 61, 30):
        _, y = proj(0, lat)
        pg.hline(MAP_X0, MAP_X1 - 1, y, EQUATOR if lat == 0 else GRAT_LINE)
    # continents: sage fill, then a lighter coastline stroke
    for land in LANDS:
        pts = [proj(lon, lat) for lon, lat in land]
        pg.poly(pts, LAND)
    for land in LANDS:
        pts = [proj(lon, lat) for lon, lat in land]
        pg.poly_line(pts, LAND_EDGE)
    # ocean labels
    draw_centred(pg, 430, 256, "ATLANTIC OCEAN", 1, OCEAN_LABEL, track=2)
    draw_centred(pg, 80, 200, "PACIFIC OCEAN", 1, OCEAN_LABEL, track=2)
    draw_centred(pg, 640, 300, "INDIAN OCEAN", 1, OCEAN_LABEL, track=2)
    # north arrow: white triangle with an N underneath
    pg.tri(60, 336, 54, 352, 66, 352, WHITE)
    draw_centred(pg, 60, 356, "N", 1, WHITE, bold=True, track=1)
    # story markers
    for st in stories:
        x, y = proj(st["lon"], st["lat"])
        draw_marker(pg, x, y, st["num"], st["accent"])
    # gold frame
    pg.hline(24, 1000, 104, GOLD)
    pg.hline(24, 1000, 105, GOLD)
    pg.hline(24, 1000, 382, GOLD)
    pg.hline(24, 1000, 383, GOLD)
    pg.vline(24, 104, 383, GOLD)
    pg.vline(25, 104, 383, GOLD)
    pg.vline(998, 104, 383, GOLD)
    pg.vline(999, 104, 383, GOLD)

# ---- stories ---------------------------------------------------------------
STORIES = [
    {"num": 1, "place": "Hodeidah, Yemen", "region": "Middle East",
     "lon": 42.9, "lat": 14.8,
     "accent": GOLD, "dark": (150, 115, 20), "band": NAVY_D,
     "headline": "SAUDI-LED STRIKES HIT HODEIDAH PORT",
     "fact": "Port hit after an evacuation order. "
             "Houthi drone hits Riyadh tower, 11 hurt.",
     "stat": "Port struck; 11 hurt in Riyadh",
     "source": "WireMinute - AP"},
    {"num": 2, "place": "Jiuquan, China", "region": "Space",
     "lon": 98.5, "lat": 39.7,
     "accent": SKY, "dark": (35, 105, 165), "band": (16, 44, 74),
     "headline": "SHENZHOU-24 LIFTS OFF",
     "fact": "Zeeshan Ali, Pakistan's first astronaut.",
     "stat": "First Pakistani in space",
     "source": "Paris Times - WireMinute"},
    {"num": 3, "place": "Washington, USA", "region": "Security",
     "lon": -77.0, "lat": 38.9,
     "accent": RED, "dark": (175, 45, 35), "band": (74, 18, 14),
     "headline": "CIA AND SPY OFFICE HIT BY CYBERATTACK",
     "fact": "Hack hits unclassified systems only.",
     "stat": "Unclassified systems hit",
     "source": "WireMinute - CuriousCats"},
    {"num": 4, "place": "Jakarta, Indonesia", "region": "Politics",
     "lon": 106.8, "lat": -6.2,
     "accent": ORANGE, "dark": (185, 105, 15), "band": (74, 40, 12),
     "headline": "INDONESIA'S VICE-PRESIDENT RESIGNS",
     "fact": "Vice-president quits amid political strain.",
     "stat": "Vice-president quits",
     "source": "Starlit Daily"},
    {"num": 5, "place": "Madrid, Spain", "region": "Sport",
     "lon": -5.5, "lat": 40.4,
     "accent": TEAL, "dark": (20, 110, 100), "band": (10, 44, 44),
     "headline": "REAL MADRID ROUT PSV 5-1",
     "fact": "Bellingham's stunner, Mbappe's brace sink PSV.",
     "stat": "Real Madrid win 5-1",
     "source": "WireMinute - Starlit Daily"},
    {"num": 6, "place": "Geneva, Switzerland", "region": "Society",
     "lon": 9.0, "lat": 46.2,
     "accent": VIOLET, "dark": (115, 80, 175), "band": (44, 28, 74),
     "headline": "FIVE WOMEN KILLED EVERY HOUR, UN SAYS",
     "fact": "Relatives behind most 2025 killings, UN says.",
     "stat": "Five an hour in 2025",
     "source": "UN - WireMinute"},
    {"num": 7, "place": "Hanoi, Vietnam", "region": "Asia",
     "lon": 105.8, "lat": 21.0,
     "accent": MAGENTA, "dark": (180, 40, 120), "band": (74, 16, 52),
     "headline": "BLAST IN HANOI KILLS SIX",
     "fact": "Gas suspected. Ten hurt in a residential area.",
     "stat": "Six killed, 10 injured",
     "source": "WireMinute"},
]


# ---- card illustrations ----------------------------------------------------
def _arc(pg, x0, y0, x1, y1, lift, col):
    """A shallow curved path from (x0, y0) to (x1, y1), bowed up by lift."""
    prev = None
    for k in range(21):
        t = k / 20.0
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t - lift * 4 * t * (1 - t)))
        if prev is not None:
            pg.line(prev[0], prev[1], x, y, col)
        prev = (x, y)


def _plus(pg, x, y, col):
    pg.hline(x - 2, x + 2, y, col)
    pg.vline(x, y - 2, y + 2, col)


def scene_rocket(pg, bx, by):
    _arc(pg, bx + 18, by + 48, bx + 290, by + 10, 14, (140, 180, 220))
    for sx, sy in ((bx + 40, by + 14), (bx + 90, by + 10), (bx + 250, by + 26),
                   (bx + 285, by + 34)):
        _plus(pg, sx, sy, WHITE)
    # rocket body, nose, window, fins, flame
    pg.rect(bx + 150, by + 18, 10, 22, WHITE)
    pg.tri(bx + 150, by + 18, bx + 160, by + 18, bx + 155, by + 8, RED)
    pg.disc(bx + 155, by + 26, 3, SKY)
    pg.tri(bx + 150, by + 32, bx + 150, by + 40, bx + 145, by + 40, RED)
    pg.tri(bx + 160, by + 32, bx + 160, by + 40, bx + 165, by + 40, RED)
    pg.burst(bx + 155, by + 44, 9, 4, 6, ORANGE)
    pg.disc(bx + 155, by + 44, 3, GOLD)


def scene_monitor(pg, bx, by):
    pg.rect(bx + 110, by + 12, 96, 30, (18, 30, 52))
    pg.rect(bx + 116, by + 17, 84, 20, (28, 48, 78))
    pg.poly([(bx + 162, by + 16), (bx + 148, by + 32), (bx + 158, by + 32),
             (bx + 150, by + 40), (bx + 170, by + 24), (bx + 160, by + 24)],
            GOLD)
    pg.vline(bx + 158, by + 42, by + 48, (200, 200, 200))
    pg.hline(bx + 140, bx + 176, by + 49, (200, 200, 200))
    pg.disc(bx + 92, by + 24, 2, RED)
    pg.disc(bx + 224, by + 24, 2, RED)


def scene_desk(pg, bx, by):
    pg.rect(bx + 120, by + 10, 60, 26, WHITE)
    for k, yy in enumerate((by + 17, by + 23, by + 29)):
        pg.hline(bx + 127, bx + 173, yy, (150, 150, 150))
    pg.hline(bx + 16, bx + 300, by + 44, (205, 195, 175))
    pg.vline(bx + 30, by + 44, by + 54, (205, 195, 175))
    pg.vline(bx + 286, by + 44, by + 54, (205, 195, 175))
    pg.vline(bx + 260, by + 8, by + 30, RED)
    pg.tri(bx + 260, by + 40, bx + 251, by + 29, bx + 269, by + 29, RED)


def scene_goal(pg, bx, by):
    for gx in range(bx + 50, bx + 171, 12):
        pg.vline(gx, by + 14, by + 46, (110, 150, 140))
    pg.hline(bx + 50, bx + 170, by + 26, (110, 150, 140))
    pg.hline(bx + 50, bx + 170, by + 38, (110, 150, 140))
    pg.vline(bx + 50, by + 14, by + 46, WHITE)
    pg.vline(bx + 170, by + 14, by + 46, WHITE)
    pg.hline(bx + 50, bx + 170, by + 14, WHITE)
    _arc(pg, bx + 178, by + 46, bx + 242, by + 34, 10, WHITE)
    pg.disc(bx + 252, by + 32, 9, WHITE)
    pg.disc(bx + 252, by + 32, 3, INK)
    pg.disc(bx + 246, by + 27, 1, INK)
    pg.disc(bx + 258, by + 27, 1, INK)
    pg.disc(bx + 246, by + 37, 1, INK)
    pg.disc(bx + 258, by + 37, 1, INK)


def scene_candle(pg, bx, by):
    for sx, sy in ((bx + 40, by + 14), (bx + 90, by + 20), (bx + 240, by + 12),
                   (bx + 280, by + 22)):
        _plus(pg, sx, sy, (200, 190, 230))
    pg.burst(bx + 156, by + 18, 12, 6, 8, GOLD)
    pg.disc(bx + 156, by + 18, 5, GOLD)
    pg.tri(bx + 156, by + 8, bx + 151, by + 19, bx + 161, by + 19, ORANGE)
    pg.rect(bx + 150, by + 26, 12, 22, WHITE)
    pg.hline(bx + 152, bx + 160, by + 34, (180, 180, 180))
    pg.hline(bx + 140, bx + 172, by + 49, (160, 150, 200))


def scene_blast(pg, bx, by):
    pg.poly([(bx + 40, by + 40), (bx + 90, by + 30), (bx + 96, by + 42),
             (bx + 46, by + 52)], (140, 140, 150))
    pg.poly([(bx + 110, by + 44), (bx + 160, by + 34), (bx + 166, by + 46),
             (bx + 116, by + 54)], (120, 120, 130))
    pg.poly([(bx + 180, by + 42), (bx + 220, by + 36), (bx + 226, by + 48),
             (bx + 186, by + 54)], (140, 140, 150))
    pg.burst(bx + 245, by + 26, 16, 7, 8, ORANGE)
    pg.burst(bx + 245, by + 26, 10, 5, 8, RED)
    pg.disc(bx + 245, by + 26, 5, GOLD)
    pg.disc(bx + 60, by + 14, 3, (160, 160, 170))
    pg.disc(bx + 130, by + 12, 2, (160, 160, 170))

SCENES = {2: scene_rocket, 3: scene_monitor, 4: scene_desk,
          5: scene_goal, 6: scene_candle, 7: scene_blast}


# ---- hero and cards ---------------------------------------------------------
def draw_hero(pg, hero):
    pg.rect(24, 396, 976, 140, NAVY_D)
    for t in range(3):
        pg.hline(24, 999, 396 + t, GOLD)
        pg.hline(24, 999, 533 + t, GOLD)
        pg.vline(24 + t, 396, 535, GOLD)
        pg.vline(997 + t, 396, 535, GOLD)
    draw_marker(pg, 54, 428, 1, hero["accent"])
    w = draw_text(pg, 80, 420, hero["place"], 2, GOLD, bold=True, track=2)
    draw_text(pg, 80 + w + 12, 422, hero["region"], 1, MUTED, track=2)
    draw_text(pg, 48, 452, hero["headline"], 3, WHITE, bold=True, track=2)
    draw_text(pg, 48, 484, hero["fact"], 2, LIGHT_GREY, track=2)
    # Revision 25 Nov (AT, 2nd): no divider rule between the fact and the
    # stat any more -- the rows are separated by the vertical gap alone.
    draw_text(pg, 48, 512, hero["stat"], 2, GOLD, bold=True, track=2)
    draw_text(pg, 684, 512, "Source: " + hero["source"], 1, MUTED, track=1)


def draw_card(pg, st, x, y):
    w, h = 317, 198
    # Revision 25 Nov (AT): no cream fill any more -- the card area stays
    # the dark page background and the cream colour lives on as the text
    # colour (PAPER) instead. Only the thin border outlines the card.
    pg.rect(x, y, w, 56, st["band"])
    SCENES[st["num"]](pg, x, y)
    pg.rect(x, y, w, 3, st["dark"])
    # 1px border in card-line colour
    pg.hline(x, x + w - 1, y, CARD_LINE)
    pg.hline(x, x + w - 1, y + h - 1, CARD_LINE)
    pg.vline(x, y, y + h - 1, CARD_LINE)
    pg.vline(x + w - 1, y, y + h - 1, CARD_LINE)
    # Revision 25 Nov (AT, 2nd): all the faint ghosted newspaper rules
    # inside the card are gone -- the horizontal dividers the yellow X
    # marks pointed at, and the two vertical ones too, since they also
    # ran behind the text. The text rows are separated by vertical gaps
    # alone; only the thin outer border and the illustration band stay.
    # number badge, kicker, region
    draw_marker(pg, x + 22, y + 78, st["num"], st["accent"])
    draw_text(pg, x + 42, y + 70, st["place"], 2, st["accent"], bold=True,
              track=2)
    draw_text(pg, x + 42, y + 88, st["region"], 1, MUTED, track=2)
    # headline and fact, wrapped to at most two lines each
    hl = wrap(st["headline"], 2, 2, 289)[:2]
    for k, line in enumerate(hl):
        draw_text(pg, x + 14, y + 100 + k * 18, line, 2, PAPER, bold=True,
                  track=2)
    fl = wrap(st["fact"], 2, 2, 289)[:2]
    for k, line in enumerate(fl):
        draw_text(pg, x + 14, y + 136 + k * 16, line, 2, PAPER, track=2)
    # stat and source -- no separator rule above the stat any more
    # (2nd revision: all in-box divider lines removed)
    draw_text(pg, x + 14, y + h - 24, st["stat"], 2, st["accent"], bold=True,
              track=2)
    draw_text(pg, x + 14, y + h - 9, "Source: " + st["source"], 1,
              MUTED, track=1)


def build():
    pg = Page()
    pg.fill(NAVY_D)
    # masthead
    draw_centred(pg, 512, 26, "THE WORLD IN ONE DAY", 3, WHITE, track=3)
    draw_centred(pg, 512, 58, "WEDNESDAY 25 NOVEMBER 2026", 4, DATE_GOLD,
                 bold=True, track=2)
    pg.hline(24, 1000, 96, GOLD)
    pg.hline(24, 1000, 97, GOLD)
    # map with all seven markers
    draw_map(pg, STORIES)
    # hero story and the six cards
    draw_hero(pg, STORIES[0])
    cols = (24, 353, 682)
    rows = (548, 758)
    for k, st in enumerate(STORIES[1:]):
        draw_card(pg, st, cols[k % 3], rows[k // 3])
    # footer
    draw_centred(pg, 512, 970,
                 "7 STORIES - VERIFIED AGAINST WIREMINUTE, STARLIT DAILY, "
                 "PARIS TIMES AND OTHERS - 25 NOVEMBER 2026",
                 1, MUTED, track=1)
    return pg


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    save_png(os.path.join(outdir, "entry.png"), build())


if __name__ == "__main__":
    main()
