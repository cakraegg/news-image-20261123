#!/usr/bin/env python3
"""THE WORLD — 23 November 2026 in one picture.

A front page drawn from scratch in pure Python (stdlib only): a broadsheet
front page for Monday 23 November 2026. Hero story: tankers burning in the
Strait of Hormuz. Below it, six more stories from the same day — Libya,
Kyiv, the collapsed COP31 climate talks, BepiColombo at Mercury, the
Cikande factory fire, and markets in turmoil — plus the day's sport.

Deterministic: no randomness, no clock, no network. Two runs write the
same bytes to /output/entry.png (1024 x 1024, PNG, under 1 MiB).
"""

import binascii
import os
import struct
import zlib
from math import isqrt

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 232, 198)
PAPER_DK = (232, 212, 168)
INK = (26, 26, 26)
RED = (178, 38, 30)
RED_DK = (140, 26, 20)
BLUE = (31, 78, 121)
TEAL = (15, 118, 110)
GOLD = (196, 141, 26)
GOLD_LT = (232, 181, 74)
SKY_TOP = (226, 128, 64)
SKY_BOT = (250, 204, 128)
SEA_TOP = (30, 70, 100)
SEA_BOT = (14, 44, 70)
GREY = (120, 116, 108)
GREY_DK = (74, 70, 64)
GREY_LT = (196, 190, 178)
WHITE = (252, 250, 244)
ORANGE = (232, 110, 24)
YELLOW = (248, 196, 64)
GREEN = (46, 125, 50)

# ------------------------------------------------------------- 5x7 font
# Uppercase, digits and punctuation. One glyph = 7 rows of 5 cells.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
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
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "\u2022": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}

BLANK = (".....", ".....", ".....", ".....", ".....", ".....", ".....")


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        for i in range(w * h):
            self.buf[i * 3] = bg[0]
            self.buf[i * 3 + 1] = bg[1]
            self.buf[i * 3 + 2] = bg[2]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def outline(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c):
        if x1 < x0:
            x0, x1 = x1, x0
        for x in range(max(0, x0), min(self.w, x1 + 1)):
            self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = isqrt(max(0, r * r - dy * dy))
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            steps = max(24, rr * 6)
            for s in range(steps):
                import math as _m
                a = 2 * _m.pi * s / steps
                self.px(cx + int(rr * _m.cos(a)), cy + int(rr * _m.sin(a)), c)

    def ellipse(self, cx, cy, rx, ry, c):
        for dy in range(-ry, ry + 1):
            dx = int(rx * isqrt(max(0, ry * ry - dy * dy)) / ry) if ry else 0
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def poly(self, pts, c):
        # Even-odd scanline fill; pts = [(x, y), ...].
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(xs[k]), int(xs[k + 1]), y, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
            self.rect(x, y + yy, w, 1, c)

    # ------------------------------------------------------------ text
    def char(self, x, y, ch, s, c):
        g = FONT.get(ch, BLANK)
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == "#":
                    self.rect(x + col * s, y + r * s, s, s, c)

    def text(self, x, y, s, scale, c):
        # The bitmap font holds capitals only: fold everything to upper
        # case (and curly quotes to straight ones) so no letter vanishes.
        s = s.upper().replace("\u2019", "'").replace("\u201c", '"').replace(
            "\u201d", '"')
        for ch in s:
            self.char(x, y, ch, scale, c)
            x += 6 * scale
        return x

    def text_w(self, s, scale):
        return max(0, len(s) * 6 * scale - scale)

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - self.text_w(s, scale) // 2, y, s, scale, c)

    def wrap(self, s, max_w, scale):
        words = s.split(" ")
        lines = []
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------- PNG
def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(
        ">I", binascii.crc32(tag + data) & 0xFFFFFFFF)


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------- small helpers
def flame(cv, x, y, s, c1=ORANGE, c2=YELLOW):
    """A little flame: outer triangle + inner tongue."""
    cv.poly([(x, y), (x + s // 2, y - s), (x + s, y)], c1)
    cv.poly([(x + s // 4, y), (x + s // 2, y - s // 2),
             (x + 3 * s // 4, y)], c2)


def smoke(cv, x, y, n=4):
    for i in range(n):
        r = 7 + i * 3
        cv.circle(x + (i % 2) * 6 - 3, y - i * 12, r, GREY)
        cv.circle(x + (i % 2) * 6 - 3, y - i * 12, r - 3, GREY_LT)


def burst(cv, cx, cy, r, c1=YELLOW, c2=ORANGE):
    for k in range(8):
        import math as _m
        a = _m.pi * k / 4
        x1 = cx + int(r * 0.4 * _m.cos(a))
        y1 = cy + int(r * 0.4 * _m.sin(a))
        x2 = cx + int(r * _m.cos(a))
        y2 = cy + int(r * _m.sin(a))
        cv.line(x1, y1, x2, y2, c1 if k % 2 == 0 else c2)
    cv.circle(cx, cy, r // 3, c1)


def tanker(cv, x, y, w, h, hull, listing=False):
    """Side view of an oil tanker on the waterline y."""
    deck = y - h
    # hull: trapezoid, bow to the right
    cv.poly([(x, deck), (x + w - 18, deck), (x + w, y),
             (x + 8, y)], hull)
    # waterline stripe
    cv.rect(x + 4, y - 6, w - 14, 4, RED_DK)
    # deck containers
    cw = (w - 90) // 4
    cols = [TEAL, GOLD, BLUE, (150, 60, 60)]
    for i in range(4):
        cv.rect(x + 14 + i * (cw + 4), deck - 16, cw, 16, cols[i])
        cv.rect(x + 14 + i * (cw + 4), deck - 16, cw, 3, WHITE)
    # bridge tower + funnel
    cv.rect(x + w - 78, deck - 44, 34, 44, WHITE)
    for r in range(4):
        cv.rect(x + w - 72, deck - 40 + r * 10, 22, 6, BLUE)
    cv.rect(x + w - 40, deck - 52, 14, 52, (60, 60, 60))
    cv.rect(x + w - 40, deck - 52, 14, 8, GOLD)


def mine(cv, cx, cy, r=12):
    cv.circle(cx, cy, r, GREY_DK)
    for k in range(8):
        import math as _m
        a = _m.pi * k / 4
        cv.line(cx + int((r - 2) * _m.cos(a)), cy + int((r - 2) * _m.sin(a)),
                cx + int((r + 7) * _m.cos(a)), cy + int((r + 7) * _m.sin(a)),
                GREY_DK)
    cv.circle(cx, cy, 4, INK)


# ------------------------------------------------------- hero: Hormuz
def hero(cv, x, y, w, h):
    # dusk sky and sea
    cv.vgrad(x, y, w, 168, SKY_TOP, SKY_BOT)
    cv.vgrad(x, y + 168, w, h - 168, SEA_TOP, SEA_BOT)
    # low sun
    cv.circle(x + w - 150, y + 108, 46, GOLD_LT)
    cv.circle(x + w - 150, y + 108, 34, GOLD)
    # clouds
    for cx, cy, rx in ((150, 60, 90), (260, 44, 70), (620, 70, 110),
                       (760, 40, 60)):
        cv.ellipse(x + cx, y + cy, rx, 12, (244, 178, 130))
        cv.ellipse(x + cx, y + cy - 8, rx - 30, 9, (250, 208, 160))
    # birds
    for bx, by in ((120, 96), (150, 108), (700, 84), (730, 96)):
        cv.line(x + bx, y + by, x + bx + 8, y + by - 6, INK)
        cv.line(x + bx + 8, y + by - 6, x + bx + 16, y + by, INK)
    # waves
    for wy in range(y + 178, y + h - 78, 16):
        for wx in range(x + 10, x + w - 10, 46):
            cv.line(wx, wy, wx + 22, wy, (70, 120, 160))
    # tankers, one burning, one listing away
    tanker(cv, x + 90, y + 268, 330, 46, (122, 40, 34))
    flame(cv, x + 200, y + 206, 34)
    flame(cv, x + 258, y + 214, 24)
    flame(cv, x + 316, y + 210, 18)
    smoke(cv, x + 300, y + 190, 4)
    burst(cv, x + 232, y + 196, 26)
    tanker(cv, x + 560, y + 292, 300, 40, (52, 58, 66))
    flame(cv, x + 640, y + 238, 22)
    smoke(cv, x + 700, y + 224, 3)
    # a naval mine drifting between them
    mine(cv, x + 480, y + 306, 11)
    # headline band
    cv.rect(x, y + h - 76, w, 76, PAPER)
    cv.rect(x, y + h - 76, w, 5, RED)
    cv.text(x + 16, y + h - 66, "WAR AT SEA", 5, RED)
    sub = ("Tankers burn in the Strait of Hormuz: mines and missiles turn "
           "the world's oil artery into a battlefield.")
    lines = cv.wrap(sub, w - 32, 2)
    for i, ln in enumerate(lines[:2]):
        cv.text(x + 16, y + h - 30 + i * 15, ln, 2, INK)


# ------------------------------------------------------- story cells
def icon_libya(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (44, 74, 110), (20, 40, 66))
    # capsizing corvette: hull leaning hard to starboard
    cv.poly([(x + 40, y + 46), (x + 210, y + 30), (x + 250, y + 52),
             (x + 60, y + 66)], (96, 100, 104))
    cv.rect(x + 150, y + 8, 10, 26, (70, 74, 78))
    cv.rect(x + 120, y + 18, 60, 8, (70, 74, 78))
    flame(cv, x + 96, y + 40, 26)
    smoke(cv, x + 130, y + 26, 3)
    burst(cv, x + 190, y + 30, 18)
    # sea drone skimming in
    cv.ellipse(x + 268, y + 58, 14, 5, INK)
    cv.line(x + 254, y + 52, x + 282, y + 52, INK)
    cv.line(x + 254, y + 50, x + 254, y + 46, INK)
    cv.line(x + 282, y + 50, x + 282, y + 46, INK)
    for wx in range(x + 8, x + w - 8, 40):
        cv.line(wx, y + h - 8, wx + 20, y + h - 8, (90, 140, 180))


def icon_kyiv(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (52, 56, 68), (30, 32, 40))
    # five-storey block, top corner blown off
    cv.poly([(x + 60, y + 14), (x + 200, y + 14), (x + 200, y + 66),
             (x + 60, y + 66)], (150, 146, 136))
    cv.poly([(x + 60, y + 14), (x + 120, y + 14), (x + 96, y + 30),
             (x + 60, y + 30)], (96, 92, 84))
    for r in range(4):
        for c in range(5):
            cv.rect(x + 72 + c * 26, y + 34 + r * 8, 14, 5,
                    GOLD_LT if (r + c) % 3 else (40, 44, 52))
    # rubble and dust
    cv.poly([(x + 30, y + 66), (x + 90, y + 40), (x + 150, y + 66)],
            (110, 106, 96))
    cv.poly([(x + 130, y + 66), (x + 190, y + 48), (x + 240, y + 66)],
            (88, 84, 76))
    cv.circle(x + 210, y + 44, 12, GREY_LT)
    cv.circle(x + 226, y + 36, 9, GREY)
    # rescuers at the rubble base
    for rx in (100, 130, 168):
        cv.circle(x + rx, y + 60, 4, (200, 60, 40))
        cv.rect(x + rx - 2, y + 62, 4, 6, (200, 60, 40))


def icon_cop(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (232, 214, 178), PAPER_DK)
    # summit table with empty chairs
    cv.ellipse(x + w // 2, y + 52, 130, 16, (122, 84, 52))
    cv.rect(x + 30, y + 50, 252, 8, (96, 64, 38))
    for cx in range(x + 44, x + w - 44, 42):
        cv.rect(cx, y + 26, 22, 24, (70, 58, 44))
        cv.rect(cx + 2, y + 18, 18, 10, (70, 58, 44))
    # cracked earth
    cv.line(x + 10, y + h - 6, x + 90, y + h - 14, (120, 84, 50))
    cv.line(x + 90, y + h - 14, x + 150, y + h - 4, (120, 84, 50))
    cv.line(x + 150, y + h - 4, x + 240, y + h - 12, (120, 84, 50))
    cv.line(x + 240, y + h - 12, x + w - 10, y + h - 6, (120, 84, 50))
    # red crosses over two empty chairs: nobody agreed to anything
    for cx in (x + 55, x + 223):
        cv.line(cx, y + 20, cx + 12, y + 32, RED)
        cv.line(cx + 12, y + 20, cx, y + 32, RED)


def icon_mercury(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (16, 18, 34), (40, 36, 60))
    # Mercury, cratered
    cv.circle(x + 76, y + 40, 30, (168, 160, 148))
    for cx, cy, r in ((64, 30, 6), (86, 46, 8), (70, 54, 5), (92, 28, 4)):
        cv.circle(x + cx, y + cy, r, (138, 130, 118))
    # stars
    for sx, sy in ((180, 12), (220, 26), (260, 10), (290, 40), (200, 60),
                   (150, 16), (240, 58)):
        cv.px(x + sx, y + sy, WHITE)
        cv.px(x + sx + 1, y + sy, WHITE)
    # BepiColombo probe on its dotted path
    for i in range(12):
        cv.px(x + 120 + i * 12, y + 58 - i * 2, GOLD_LT)
        cv.px(x + 121 + i * 12, y + 58 - i * 2, GOLD_LT)
    cv.rect(x + 238, y + 26, 18, 12, (200, 200, 200))
    cv.rect(x + 218, y + 29, 18, 6, BLUE)
    cv.rect(x + 258, y + 29, 18, 6, BLUE)
    cv.line(x + 247, y + 26, x + 247, y + 16, WHITE)
    cv.circle(x + 247, y + 14, 3, GOLD)


def icon_factory(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (66, 60, 54), (38, 34, 30))
    # sawtooth factory
    cv.poly([(x + 30, y + 66), (x + 30, y + 34), (x + 80, y + 20),
             (x + 80, y + 34), (x + 130, y + 20), (x + 130, y + 34),
             (x + 180, y + 20), (x + 180, y + 34), (x + 230, y + 20),
             (x + 230, y + 66)], (120, 88, 70))
    for wx in range(x + 44, x + 220, 34):
        cv.rect(wx, y + 44, 16, 12, GOLD_LT)
    flame(cv, x + 96, y + 30, 30)
    flame(cv, x + 150, y + 34, 22)
    smoke(cv, x + 120, y + 14, 3)
    smoke(cv, x + 190, y + 18, 3)
    cv.rect(x + 240, y + 48, 44, 18, WHITE)
    cv.rect(x + 240, y + 48, 44, 5, RED)


def icon_markets(cv, x, y, w, h):
    cv.rect(x, y, w, h, WHITE)
    cv.outline(x, y, w, h, GREY, 1)
    # axes
    cv.line(x + 24, y + 8, x + 24, y + h - 14, INK)
    cv.line(x + 24, y + h - 14, x + w - 12, y + h - 14, INK)
    # falling line with arrowhead
    pts = [(36, 18), (80, 24), (120, 20), (160, 38), (196, 52),
           (226, 48), (252, 62)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0],
                y + pts[i + 1][1], RED)
    cv.poly([(x + 252, y + 62), (x + 240, y + 56), (x + 246, y + 68)],
            RED)
    # gold coin
    cv.circle(x + w - 44, y + 26, 20, GOLD)
    cv.ring(x + w - 44, y + 26, 20, GOLD_LT, 2)
    cv.circle(x + w - 44, y + 26, 13, GOLD_LT)
    cv.text(x + w - 56, y + 19, "AU", 2, (120, 82, 10))


CELLS = [
    ("LIBYA", RED, "DRONES SINK RUSSIAN WARSHIP",
     "Corvette Merkury capsizes at Benghazi.",
     icon_libya),
    ("UKRAINE", BLUE, "FLAT BLOCK HIT NEAR KYIV",
     "Two dead, eleven missing in Dymer.",
     icon_kyiv),
    ("CLIMATE", TEAL, "COP31 COLLAPSES",
     "Talks end with no fossil-fuel deal.",
     icon_cop),
    ("SPACE", (90, 70, 140), "AT MERCURY, AT LAST",
     "BepiColombo enters orbit after eight years.",
     icon_mercury),
    ("INDONESIA", ORANGE, "FACTORY FIRE: DOZENS MISSING",
     "Blaze at a Cikande candy plant.",
     icon_factory),
    ("MARKETS", GOLD, "GOLD SOARS, STOCKS SLIDE",
     "Kospi falls 4% as gold tops 3600.",
     icon_markets),
]


def cell(cv, x, y, w, h, kicker, kc, headline, deck, icon):
    cv.rect(x, y, w, h, WHITE)
    cv.outline(x, y, w, h, INK, 2)
    icon(cv, x + 2, y + 2, w - 4, 68)
    cv.rect(x, y + 74, w, 3, kc)
    cv.text(x + 10, y + 84, kicker, 2, kc)
    lines = cv.wrap(headline, w - 20, 3)
    for i, ln in enumerate(lines[:2]):
        cv.text(x + 10, y + 104 + i * 21, ln, 3, INK)
    dlines = cv.wrap(deck, w - 20, 2)
    for i, ln in enumerate(dlines[:2]):
        cv.text(x + 10, y + 154 + i * 15, ln, 2, GREY_DK)


# ------------------------------------------------------- page assembly
def build():
    cv = Canvas(W, H, PAPER)
    cv.outline(10, 10, W - 20, H - 20, INK, 3)
    cv.outline(20, 20, W - 40, H - 40, INK, 1)
    # top strip
    cv.text_c(W // 2, 30, "THE WORLD IN ONE PICTURE", 2, RED)
    # masthead
    cv.text_c(W // 2, 56, "THE WORLD", 11, INK)
    cv.rect(28, 148, W - 56, 3, INK)
    cv.text_c(W // 2, 158, "MONDAY 23 NOVEMBER 2026", 3, INK)
    # hero
    hero(cv, 28, 186, W - 56, 334)
    # story grid: 3 x 2
    cw, ch, gap = 312, 188, 12
    for i, (kicker, kc, headline, deck, icon) in enumerate(CELLS):
        cx = 28 + (i % 3) * (cw + gap)
        cy = 534 + (i // 3) * (ch + gap)
        cell(cv, cx, cy, cw, ch, kicker, kc, headline, deck, icon)
    # also in the news
    cv.rect(28, 928, W - 56, 2, INK)
    also = ("ALSO: SHURI CASTLE REOPENS  \u2022  UK TO HOST 2035 WOMEN'S "
            "WORLD CUP  \u2022  ALCARAZ WINS ATP FINALS  \u2022  LIVERPOOL "
            "BEAT MAN UNITED")
    for i, ln in enumerate(cv.wrap(also, W - 56, 2)[:2]):
        cv.text(28, 936 + i * 15, ln, 2, INK)
    # one-sentence joke + credit
    cv.text_c(W // 2, 968, "AND SOMEWHERE, MONDAY QUIETLY ASKED FOR A RECOUNT.",
              2, RED)
    cv.text_c(W // 2, 986, "THE WORLD  \u2022  23 NOVEMBER 2026", 2, GREY_DK)
    return cv


def main():
    cv = build()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
