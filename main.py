#!/usr/bin/env python3
"""news-image-20261125 — one image summing up the world news of
Wednesday 25 November 2026.

Pure Python 3 standard library only. No network, no files read at run
time: every pixel is drawn in code, deterministically, so two runs
write byte-identical PNGs.

Layout (1024 x 1024, front page with a dark world map — the look AT
chose for the 20/21 Nov entries: one HERO story + 6 numbered cards,
each story pinned to the map by a numbered marker in its own colour):
  masthead  : THE WORLD IN ONE DAY / WEDNESDAY 25 NOVEMBER 2026
  map       : dark ocean, sage-teal continents, 7 numbered markers
  hero      : Hodeidah — Saudi-led strikes hit the port
  grid 2x3  : Jiuquan Shenzhou-24 launch | Washington CIA hack |
              Jakarta VP resigns | Madrid Real rout PSV |
              Geneva UN femicide report | Hanoi blast kills six
  footer    : verification line

Headlines are ALL CAPS; every other line in the news boxes is
sentence case, as AT asked on 23 Nov. All seven stories were checked
against the 25 Nov 2026 news cycle (see NEWS.md in this repo).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
CARD = (250, 245, 232)
INK = (16, 24, 40)
FACT_D = (70, 72, 84)
CARD_LINE = (160, 150, 125)
DATE_GOLD = (201, 162, 39)
NAVY = (20, 38, 74)
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

# ---------------------------------------------------------------- 5x7 font
# 7 rows of 5 pixels each; "#" = on. Capitals are full height;
# lowercase letters sit on the x-height (rows 2-6) with descenders
# (g, j, p, q, y) dropping to row 6, in the same stroke style.
FONT = {
    "A": (" .###. ", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "$": ("..#..", ".####", "#.#.#", ".#.#.", "..##.", ".#.#.", "####."),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".####", "..##."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "..#.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.##", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.#..", "##...", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
}
FONT = {k: tuple(r.strip()[:5].ljust(5, ".") for r in v)
        for k, v in FONT.items()}


def _chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    return out + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def write_png(path, rgb, w, h):
    """Deterministic PNG: filter-0 rows, zlib level 9, fixed chunk order."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def hline(self, x, y, w, c, t=1):
        for k in range(t):
            self.rect(x, y + k, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for k in range(t):
            self.rect(x + k, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx + dy, x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x + a, y + b, c)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            for yy in range(cy - rr, cy + rr + 1):
                for xx in range(cx - rr, cx + rr + 1):
                    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                    if rr * rr - 2 * rr <= d2 <= rr * rr:
                        self.set(xx, yy, c)

    def tri(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        for yy in range(min(y0, y1, y2), max(y0, y1, y2) + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy <= max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.rect(xa, yy, xb - xa + 1, 1, c)

    def starburst(self, cx, cy, r0, r1, n, c):
        pts = []
        for k in range(2 * n):
            r = r1 if k % 2 == 0 else r0
            a = math.pi * k / n - math.pi / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        for k in range(len(pts)):
            self.tri((pts[k], pts[(k + 1) % len(pts)], (cx, cy)), c)

    # ------------------------------------------------------------ text
    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def draw_text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for ry in range(7):
                row = g[ry]
                for rx in range(5):
                    if row[rx] == "#":
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, c):
        return self.draw_text(cx - self.text_w(s, scale) // 2, y, s, scale, c)

    def wrap(self, s, scale, maxw):
        lines, cur = [], ""
        for wd in s.split():
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= maxw:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


# ------------------------------------------------------------ type tools
# The base 5x7 bitmap font only ships one weight and no tracking, so the
# display treatments below are built on top of it: bold = a second pass
# offset by 1px (thickens strokes at scale >= 2), tracking = extra px
# between glyphs. Type scale: 4 masthead date, 3 masthead title and hero
# headline, 2 headlines/kickers/stats/facts, 1 tracked labels.


def tw(s, scale, tracking=0):
    return len(s) * 6 * scale - scale + max(0, len(s) - 1) * tracking


def draw_text2(c, x, y, s, scale, color, tracking=0, bold=False):
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for ry in range(7):
            row = g[ry]
            for rx in range(5):
                if row[rx] == "#":
                    c.rect(cx + rx * scale, y + ry * scale, scale, scale,
                           color)
                    if bold:
                        c.rect(cx + rx * scale + 1, y + ry * scale,
                               scale, scale, color)
        cx += 6 * scale + tracking
    return cx


def text_center2(c, cx, y, s, scale, color, tracking=0, bold=False):
    return draw_text2(c, cx - tw(s, scale, tracking) // 2, y, s, scale,
                      color, tracking, bold)


def wrap2(s, scale, maxw, tracking=0):
    lines, cur = [], ""
    for wd in s.split():
        trial = (cur + " " + wd).strip()
        if tw(trial, scale, tracking) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ world map
# Equirectangular world map. Longitude -180..180 across MAP_W,
# latitude 85..-60 down MAP_H (Antarctica omitted, as usual).
MAP_X0, MAP_Y0, MAP_W, MAP_H = 24, 104, 976, 280
LAT_TOP, LAT_BOT = 85, -60


def project(lon, lat):
    x = MAP_X0 + (lon + 180.0) / 360.0 * MAP_W
    y = MAP_Y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H
    return int(x), int(y)


# Simplified (lon, lat) coastlines, hand-drawn for a 1024px map.
NORTH_AMERICA = [
    (-168, 66), (-158, 58), (-152, 60), (-140, 60), (-135, 57),
    (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29),
    (-110, 24), (-105, 20), (-97, 16), (-94, 17), (-90, 14),
    (-86, 12), (-83, 9), (-79, 9), (-80, 13), (-84, 16),
    (-87, 21), (-90, 21), (-91, 19), (-97, 26), (-93, 30),
    (-89, 30), (-84, 30), (-81, 25), (-80, 32), (-76, 35),
    (-74, 40), (-70, 42), (-68, 45), (-65, 44), (-60, 47),
    (-55, 47), (-60, 52), (-64, 58), (-68, 58), (-72, 62),
    (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68),
    (-125, 70), (-140, 70), (-155, 71), (-165, 68),
]
GREENLAND = [
    (-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68),
    (-22, 70), (-20, 74), (-25, 76), (-35, 78), (-50, 76),
    (-58, 74), (-62, 70),
]
SOUTH_AMERICA = [
    (-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
    (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-73, -44),
    (-74, -50), (-70, -54), (-66, -55), (-68, -50), (-65, -45),
    (-62, -41), (-58, -35), (-52, -32), (-48, -28), (-41, -23),
    (-39, -17), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
    (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11),
    (-72, 12), (-76, 10),
]
AFRICA = [
    (-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35),
    (0, 36), (10, 37), (11, 34), (20, 32), (25, 32),
    (32, 31), (35, 28), (37, 22), (39, 18), (43, 12),
    (48, 11), (51, 12), (46, 5), (41, 0), (40, -5),
    (40, -10), (36, -18), (33, -26), (28, -33), (20, -35),
    (17, -32), (14, -22), (12, -15), (13, -10), (9, -1),
    (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12),
]
EUROPE = [
    (-10, 36), (-9, 43), (-2, 48), (2, 51), (7, 55),
    (8, 58), (5, 60), (10, 62), (14, 67), (20, 70),
    (29, 71), (32, 68), (30, 65), (25, 65), (23, 60),
    (21, 56), (18, 55), (13, 54), (8, 54), (8, 57),
    (5, 57), (3, 53), (1, 51), (-2, 50), (-4, 48),
    (-1, 44), (-2, 43), (-9, 43), (-9, 37), (-6, 36),
    (-2, 37), (0, 38), (3, 42), (7, 44), (10, 44),
    (12, 45), (14, 45), (18, 44), (19, 42), (16, 40),
    (15, 38), (12, 38), (10, 37), (8, 39), (3, 38),
    (0, 36),
]
ASIA = [
    (32, 68), (40, 68), (50, 69), (60, 69), (70, 72),
    (80, 73), (90, 75), (100, 77), (110, 74), (120, 72),
    (130, 71), (140, 72), (150, 70), (158, 68), (162, 64),
    (158, 60), (156, 52), (150, 59), (142, 55), (140, 50),
    (135, 44), (130, 42), (127, 40), (122, 39), (120, 35),
    (122, 31), (120, 28), (115, 23), (110, 20), (108, 18),
    (105, 10), (103, 8), (100, 7), (98, 10), (95, 16),
    (92, 21), (89, 22), (86, 20), (82, 17), (80, 13),
    (77, 8), (75, 12), (72, 20), (68, 23), (66, 25),
    (62, 25), (58, 26), (56, 27), (52, 28), (50, 29),
    (48, 30), (44, 29), (42, 25), (40, 20), (39, 21),
    (35, 28), (34, 29), (32, 31), (30, 36), (28, 38),
    (27, 40), (26, 42), (23, 40), (22, 37), (26, 36),
    (30, 36), (30, 41), (28, 45), (28, 48), (30, 52),
    (32, 55), (30, 58), (30, 62), (30, 66),
]
AUSTRALIA = [
    (113, -22), (114, -30), (115, -35), (118, -35), (124, -33),
    (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
    (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
    (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
    (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
]
BRITAIN = [
    (-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
]
JAPAN = [
    (130, 31), (132, 33), (135, 34), (137, 35), (139, 36),
    (140, 38), (141, 40), (143, 42), (145, 44), (143, 44),
    (141, 42), (139, 38), (137, 35), (134, 34), (131, 32),
]
NEW_GUINEA = [
    (131, -1), (136, -2), (141, -3), (146, -6), (150, -8),
    (147, -9), (142, -8), (138, -7), (134, -4), (131, -1),
]
CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE,
              ASIA, AUSTRALIA, BRITAIN, JAPAN, NEW_GUINEA]


def _fill_poly(c, pts, color):
    """Scanline fill of a polygon given as pixel points."""
    ys = [p[1] for p in pts]
    for yy in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
            if ay == by:
                continue
            if min(ay, by) <= yy < max(ay, by):
                xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            c.rect(int(xs[k]), yy, int(xs[k + 1]) - int(xs[k]) + 1, 1, color)


def draw_map(c, markers):
    """Dark ocean, graticule, sage-teal continents, numbered markers."""
    c.rect(MAP_X0, MAP_Y0, MAP_W, MAP_H, OCEAN)
    # graticule every 30 degrees
    for lon in range(-180, 181, 30):
        gx, _ = project(lon, 0)
        c.vline(gx, MAP_Y0, MAP_H, GRAT, 1)
    for lat in range(-60, 86, 30):
        _, gy = project(0, lat)
        c.hline(MAP_X0, gy, MAP_W, GRAT, 1)
    # equator, slightly brighter
    _, eq = project(0, 0)
    c.hline(MAP_X0, eq, MAP_W, (70, 110, 150), 1)
    # continents: fill + coastline stroke
    for poly in CONTINENTS:
        px = [project(lon, lat) for lon, lat in poly]
        _fill_poly(c, px, LAND)
        for i in range(len(px)):
            c.line(px[i][0], px[i][1], px[(i + 1) % len(px)][0],
                   px[(i + 1) % len(px)][1], LAND_EDGE, 1)
    # ocean labels
    draw_text2(c, 390, 262, "ATLANTIC OCEAN", 1, OCEAN_LABEL, tracking=2)
    draw_text2(c, 80, 200, "PACIFIC OCEAN", 1, OCEAN_LABEL, tracking=2)
    draw_text2(c, 640, 300, "INDIAN OCEAN", 1, OCEAN_LABEL, tracking=2)
    # north arrow, bottom-left open ocean
    nx, ny = 60, 350
    c.tri(((nx, ny - 14), (nx - 6, ny + 6), (nx + 6, ny + 6)), WHITE)
    draw_text2(c, nx - 3, ny + 10, "N", 1, WHITE, bold=True)
    # numbered markers
    for m in markers:
        mx, my = project(m["lon"], m["lat"])
        draw_marker(c, mx, my, m["n"], m["color"])


def halo_of(color):
    return tuple(v * 11 // 20 for v in color)


def draw_marker(c, cx, cy, n, color=GOLD):
    c.disc(cx, cy, 16, halo_of(color))
    c.disc(cx, cy, 12, color)
    c.ring(cx, cy, 14, WHITE, 2)
    s = str(n)
    draw_text2(c, cx - tw(s, 2) // 2, cy - 7, s, 2, NAVY_D, bold=True)


# ------------------------------------------------------------ stories
# Each story carries its own accent colour: the map marker, the number
# badge, the illustration band, the place kicker, the stat line and the
# card's top rule all use the same colour, so a reader can match a card
# to its marker at a glance.
ACCENT = {
    1: (201, 162, 39),   # gold     - Hodeidah (hero, port strikes)
    2: (90, 165, 225),   # sky blue - Jiuquan (Shenzhou-24)
    3: (224, 82, 66),    # red      - Washington (CIA hack)
    4: (232, 142, 44),   # orange   - Jakarta (VP resigns)
    5: (64, 178, 168),   # teal     - Madrid (Real rout PSV)
    6: (168, 130, 220),  # violet   - Geneva (UN femicide report)
    7: (232, 64, 160),   # magenta  - Hanoi (blast kills six)
}

# Darker versions of the accents, for text and rules on cream: the
# bright accents are too light to read on a pale background.
ACCENT_DARK = {
    1: (150, 115, 20),   # dark gold
    2: (35, 105, 165),   # deep blue
    3: (175, 45, 35),    # brick red
    4: (185, 105, 15),   # dark amber
    5: (20, 110, 100),   # deep teal
    6: (115, 80, 175),   # deep violet
    7: (180, 40, 120),   # deep magenta
}

# Dark tinted backgrounds for the illustration band on top of each
# card (and the hero panel): the accent colour pulled down to navy.
BAND = {
    1: (12, 24, 48),     # hero panel: deep navy
    2: (16, 44, 74),     # dark blue
    3: (74, 18, 14),     # dark red
    4: (74, 40, 12),     # dark amber
    5: (10, 44, 44),     # dark teal
    6: (44, 28, 74),     # dark violet
    7: (74, 16, 52),     # dark magenta
}

# Seven stories, each checked against the 25 Nov 2026 news cycle
# (see NEWS.md). Story 1 is the hero; stories 2-7 are the grid cards.
# Fields: place, region tag, headline, fact, stat, source, map position.
STORIES = [
    {"n": 1, "lon": 42.9, "lat": 14.8, "place": "Hodeidah, Yemen",
     "region": "Middle East",
     "headline": "SAUDI-LED STRIKES HIT HODEIDAH PORT",
     "fact": "Port hit after an evacuation order. Houthi drone hits "
             "Riyadh tower, 11 hurt.",
     "stat": "Port struck; 11 hurt in Riyadh",
     "source": "WireMinute - AP"},
    {"n": 2, "lon": 98.5, "lat": 39.7, "place": "Jiuquan, China",
     "region": "Space",
     "headline": "SHENZHOU-24 LIFTS OFF",
     "fact": "Zeeshan Ali, Pakistan's first astronaut.",
     "stat": "First Pakistani in space",
     "source": "Paris Times - WireMinute"},
    {"n": 3, "lon": -77.0, "lat": 38.9, "place": "Washington, USA",
     "region": "Security",
     "headline": "CIA AND SPY OFFICE HIT BY CYBERATTACK",
     "fact": "Hack hits unclassified systems only.",
     "stat": "Unclassified systems hit",
     "source": "WireMinute - CuriousCats"},
    {"n": 4, "lon": 106.8, "lat": -6.2, "place": "Jakarta, Indonesia",
     "region": "Politics",
     "headline": "INDONESIA'S VICE-PRESIDENT RESIGNS",
     "fact": "Vice-president quits amid political strain.",
     "stat": "Vice-president quits",
     "source": "Starlit Daily"},
    {"n": 5, "lon": -5.5, "lat": 40.4, "place": "Madrid, Spain",
     "region": "Sport",
     "headline": "REAL MADRID ROUT PSV 5-1",
     "fact": "Bellingham's stunner, Mbappe's brace sink PSV.",
     "stat": "Real Madrid win 5-1",
     "source": "WireMinute - Starlit Daily"},
    {"n": 6, "lon": 9.0, "lat": 46.2, "place": "Geneva, Switzerland",
     "region": "Society",
     "headline": "FIVE WOMEN KILLED EVERY HOUR, UN SAYS",
     "fact": "Relatives behind most 2025 killings, UN says.",
     "stat": "Five an hour in 2025",
     "source": "UN - WireMinute"},
    {"n": 7, "lon": 105.8, "lat": 21.0, "place": "Hanoi, Vietnam",
     "region": "Asia",
     "headline": "BLAST IN HANOI KILLS SIX",
     "fact": "Gas suspected. Ten hurt in a residential area.",
     "stat": "Six killed, 10 injured",
     "source": "WireMinute"},
]


# ------------------------------------------------------------ illustrations
# Small hand-drawn scenes for the card bands. Each takes the canvas, a
# bounding box (x, y, w, h) and the story's accent colour, and draws
# only with the primitives above: a colour-block panel, not a photo.


def _arc(c, x0, y0, x1, y1, lift, color, t=2):
    """A curved trail from (x0, y0) to (x1, y1), arched upward by lift."""
    steps = 24
    px, py = x0, y0
    for k in range(1, steps + 1):
        f = k / steps
        x = int(x0 + (x1 - x0) * f)
        y = int(y0 + (y1 - y0) * f - 4 * lift * f * (1 - f))
        c.line(px, py, x, y, color, t)
        px, py = x, y


def illu_rocket(c, x, y, w, h, ac):
    """Shenzhou-24: a rocket climbing past stars on an orbit arc."""
    _arc(c, x + 30, y + h - 8, x + w - 30, y + 14, 18, (120, 160, 210), 2)
    for sx, sy in ((x + 40, y + 12), (x + 90, y + 8), (x + 250, y + 10),
                   (x + 280, y + 22), (x + 60, y + 30)):
        c.disc(sx, sy, 2, WHITE)
    cx = x + w // 2
    c.rect(cx - 7, y + 12, 14, 26, WHITE)
    c.tri(((cx - 7, y + 12), (cx + 7, y + 12), (cx, y + 2)), RED)
    c.tri(((cx - 7, y + 38), (cx - 16, y + 46), (cx - 7, y + 44)), ORANGE)
    c.tri(((cx + 7, y + 38), (cx + 16, y + 46), (cx + 7, y + 44)), ORANGE)
    c.starburst(cx, y + h - 6, 4, 10, 8, GOLD)
    c.disc(cx, y + h - 6, 3, WHITE)


def illu_hack(c, x, y, w, h, ac):
    """A breached screen: a monitor with a lightning bolt warning."""
    cx = x + w // 2
    c.rect(cx - 70, y + 8, 140, 34, (10, 20, 38))
    c.rect(cx - 70, y + 8, 140, 34, WHITE)
    c.rect(cx - 66, y + 12, 132, 26, (10, 20, 38))
    c.vline(cx, y + 42, 8, WHITE, 3)
    c.hline(cx - 24, y + 50, 48, WHITE, 2)
    # lightning bolt, gold
    pts = [(cx + 8, y + 14), (cx - 6, y + 28), (cx + 2, y + 28),
           (cx - 8, y + 40), (cx + 10, y + 24), (cx + 2, y + 24)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GOLD, 3)
    c.disc(x + 40, y + 14, 3, RED)
    c.disc(x + w - 40, y + 20, 3, RED)


def illu_desk(c, x, y, w, h, ac):
    """A resignation: a desk, a signed paper, a downward arrow."""
    c.hline(x + 30, y + h - 14, w - 60, (200, 210, 230), 3)
    c.vline(x + 44, y + h - 14, 10, (200, 210, 230), 3)
    c.vline(x + w - 44, y + h - 14, 10, (200, 210, 230), 3)
    c.rect(x + 90, y + 18, 70, 26, WHITE)
    c.hline(x + 98, y + 26, 54, INK, 2)
    c.hline(x + 98, y + 32, 40, INK, 2)
    c.hline(x + 98, y + 38, 48, INK, 2)
    c.line(x + 180, y + 22, x + 196, y + 30, GOLD, 2)
    # downward arrow on the right
    ax = x + w - 60
    c.vline(ax, y + 8, 30, RED, 3)
    c.tri(((ax - 8, y + 34), (ax + 8, y + 34), (ax + 1, y + 46)), RED)


def illu_ball(c, x, y, w, h, ac):
    """A football goal and a ball flying into the top corner."""
    c.hline(x + 30, y + 10, w - 60, WHITE, 3)
    c.vline(x + 30, y + 10, 38, WHITE, 3)
    c.vline(x + w - 30, y + 10, 38, WHITE, 3)
    for gx in range(x + 30, x + w - 30, 18):
        c.vline(gx, y + 10, 38, (200, 210, 230), 1)
    c.hline(x + 20, y + h - 8, w - 40, (94, 138, 122), 3)
    bx, by = x + w - 70, y + 20
    c.disc(bx, by, 12, WHITE)
    c.disc(bx, by, 4, INK)
    for dx, dy in ((-8, -6), (8, -6), (-9, 5), (9, 5), (0, 9)):
        c.disc(bx + dx, by + dy, 2, INK)
    _arc(c, x + 50, y + h - 10, bx - 10, by + 8, 14, (214, 222, 232), 2)


def illu_candle(c, x, y, w, h, ac):
    """A remembrance candle: white candle, gold flame, soft glow."""
    cx = x + w // 2
    c.disc(cx, y + 16, 14, halo_of(GOLD))
    c.starburst(cx, y + 16, 3, 9, 8, GOLD)
    c.disc(cx, y + 16, 3, WHITE)
    c.rect(cx - 8, y + 26, 16, 22, WHITE)
    c.hline(cx - 8, y + 26, 16, (200, 210, 230), 1)
    c.hline(cx - 12, y + 48, 24, (200, 210, 230), 2)
    for sx in (x + 40, x + 90, x + w - 90, x + w - 40):
        c.disc(sx, y + 18, 2, (214, 222, 232))


def illu_blast(c, x, y, w, h, ac):
    """A blast in a residential block: tilted slabs, fire, smoke."""
    c.rect(x + 30, y + 30, 60, 20, (120, 120, 118))
    c.rect(x + 70, y + 14, 70, 16, (150, 150, 148))
    c.rect(x + 120, y + 34, 80, 16, (120, 120, 118))
    c.starburst(x + 210, y + 22, 6, 16, 8, ORANGE)
    c.starburst(x + 240, y + 30, 5, 12, 8, GOLD)
    c.disc(x + 210, y + 22, 4, WHITE)
    c.disc(x + 240, y + 30, 3, WHITE)
    c.disc(x + 100, y + 10, 8, (60, 60, 60))
    c.disc(x + 260, y + 12, 6, (60, 60, 60))
    c.hline(x + 20, y + h - 6, w - 40, (200, 210, 230), 2)


ILLU = {2: illu_rocket, 3: illu_hack, 4: illu_desk, 5: illu_ball,
        6: illu_candle, 7: illu_blast}


def ghosted(c, x, y, w, h, line_c):
    """Ghosted newspaper background: column dividers + rows of short
    horizontal 'text' lines, drawn in a colour only just above the
    background (barely visible, never fights the real copy on top)."""
    cols = 4 if w > 500 else 2
    for k in range(1, cols):
        c.vline(x + k * w // cols, y + 6, h - 12, line_c, 1)
    row = 0
    yy = y + 8
    while yy + 2 <= y + h - 6:
        for k in range(cols):
            cx0 = x + k * w // cols + 6
            cx1 = x + (k + 1) * w // cols - 6
            frac = 0.55 + 0.4 * ((row * 7 + k * 13) % 10) / 10.0
            lw = int((cx1 - cx0) * frac)
            if row == 0:
                c.hline(cx0, yy, int((cx1 - cx0) * 0.7), line_c, 4)
            elif lw > 8:
                c.hline(cx0, yy, lw, line_c, 2)
        yy += 6
        row += 1


def story_card(c, x, y, w, h, st):
    c.rect(x, y, w, h, CARD)
    ac = ACCENT[st["n"]]
    acd = ACCENT_DARK[st["n"]]
    c.hline(x, y, w, acd, 3)
    c.hline(x, y + h - 1, w, CARD_LINE, 1)
    c.vline(x, y, h, CARD_LINE, 1)
    c.vline(x + w - 1, y, h, CARD_LINE, 1)
    # illustration band on top (56px): a small hand-drawn scene in the
    # story's colours, not a photo
    c.rect(x + 1, y + 1, w - 2, 56, BAND[st["n"]])
    ILLU[st["n"]](c, x + 1, y + 1, w - 2, 56, ac)
    # ghosted newspaper background behind the copy
    ghosted(c, x + 6, y + 62, w - 12, h - 68, (215, 205, 180))
    # number badge + place kicker (bold, in the story's colour) + region
    draw_marker(c, x + 22, y + 78, st["n"], ac)
    draw_text2(c, x + 42, y + 70, st["place"], 2, acd, bold=True)
    draw_text2(c, x + 42, y + 88, st["region"], 1, (110, 105, 90),
               tracking=2)
    # headline, bold, up to 2 lines
    lines = wrap2(st["headline"], 2, w - 28)[:2]
    hy = y + 100
    for ln in lines:
        draw_text2(c, x + 14, hy, ln, 2, INK, bold=True)
        hy += 18
    # fact, up to 2 lines
    flines = wrap2(st["fact"], 2, w - 28)[:2]
    fy = y + 136
    for ln in flines:
        draw_text2(c, x + 14, fy, ln, 2, FACT_D)
        fy += 16
    # stat highlight + source line at the foot of the card
    c.hline(x + 14, y + h - 28, w - 28, CARD_LINE, 1)
    draw_text2(c, x + 14, y + h - 22, st["stat"], 2, acd, bold=True)
    draw_text2(c, x + 14, y + h - 8, "Source: " + st["source"], 1,
               (110, 105, 90), tracking=1)


# ------------------------------------------------------------- layout
def build():
    c = Canvas(W, H, NAVY_D)

    # ---- masthead: dark navy, gold rules, white title, gold date
    text_center2(c, 512, 26, "THE WORLD IN ONE DAY", 3, WHITE, tracking=3)
    text_center2(c, 512, 58, "WEDNESDAY 25 NOVEMBER 2026", 4, DATE_GOLD,
                 bold=True)
    c.hline(24, 96, 976, GOLD, 2)

    # ---- map: ocean, continents, 7 numbered markers
    markers = [{"n": st["n"], "lon": st["lon"], "lat": st["lat"],
                "color": ACCENT[st["n"]]} for st in STORIES]
    draw_map(c, markers)
    c.hline(24, 104, 976, GOLD, 2)
    c.hline(24, 382, 976, GOLD, 2)
    c.vline(24, 104, 280, GOLD, 2)
    c.vline(998, 104, 280, GOLD, 2)

    # ---- hero: story 1 on a dark navy panel with a gold frame
    st = STORIES[0]
    hx, hy, hw, hh = 24, 396, 976, 140
    c.rect(hx, hy, hw, hh, BAND[1])
    c.hline(hx, hy, hw, GOLD, 3)
    c.hline(hx, hy + hh - 3, hw, GOLD, 3)
    c.vline(hx, hy, hh, GOLD, 3)
    c.vline(hx + hw - 3, hy, hh, GOLD, 3)
    draw_marker(c, hx + 30, hy + 32, 1, GOLD)
    draw_text2(c, hx + 56, hy + 24, st["place"], 2, GOLD, bold=True)
    draw_text2(c, hx + 56 + tw(st["place"], 2) + 16, hy + 26,
               st["region"], 1, MUTED, tracking=2)
    hlines = wrap2(st["headline"], 3, 920)[:1]
    hyy = hy + 56
    for ln in hlines:
        draw_text2(c, hx + 24, hyy, ln, 3, WHITE, bold=True)
        hyy += 28
    flines = wrap2(st["fact"], 2, 920)[:1]
    fy = hy + 88
    for ln in flines:
        draw_text2(c, hx + 24, fy, ln, 2, (214, 222, 232))
        fy += 18
    c.hline(hx + 24, hy + 110, 620, GRAT, 1)
    draw_text2(c, hx + 24, hy + 116, st["stat"], 2, GOLD, bold=True)
    draw_text2(c, hx + 660, hy + 116, "Source: " + st["source"], 1,
               MUTED, tracking=1)

    # ---- story cards: 2 rows x 3 columns (stories 2-7)
    cw, ch, gap = 317, 198, 12
    for i, st in enumerate(STORIES[1:]):
        col, row = i % 3, i // 3
        x = 24 + col * (cw + gap)
        y = 548 + row * (ch + gap)
        story_card(c, x, y, cw, ch, st)

    # ---- footer
    text_center2(c, 512, 970,
                 "7 STORIES - VERIFIED AGAINST WIREMINUTE, STARLIT DAILY, PARIS TIMES AND OTHERS - 25 NOVEMBER 2026",
                 1, MUTED, tracking=1)
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    c = build()
    path = os.path.join(outdir, "entry.png")
    write_png(path, c.px, W, H)
    print("WROTE", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
