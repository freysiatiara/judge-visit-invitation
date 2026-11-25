#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Draws a single 1024x1024 PNG invitation letter with a tiny pure-Python
rasterizer and an embedded 5x7 bitmap font. Standard library only.
Deterministic: identical bytes on every run.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
PAPER = (253, 246, 227)
PAPER2 = (255, 251, 240)
INK = (43, 32, 24)
NAVY = (31, 58, 95)
RED = (176, 58, 46)
ROOF = (178, 62, 48)
BRICK = (150, 80, 60)
GREEN = (96, 140, 74)
GREEN_D = (74, 112, 56)
SUN = (244, 180, 44)
SKY = (178, 214, 235)
CUP = (196, 96, 58)
CUP_D = (150, 66, 38)
SEAL = (164, 19, 60)
SEAL_D = (130, 12, 46)
SMOKE = (200, 198, 190)
WHITE = (255, 255, 255)
FLOWER1 = (214, 90, 120)
FLOWER2 = (240, 170, 60)
FLOWER3 = (150, 120, 200)

# --- canvas ----------------------------------------------------------------
buf = bytearray(W * H * 3)


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = color[0]
        buf[i + 1] = color[1]
        buf[i + 2] = color[2]


def fill_rect(x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    for y in range(y0, y1):
        base = (y * W + x0) * 3
        for x in range(x0, x1):
            i = base + (x - x0) * 3
            buf[i] = color[0]
            buf[i + 1] = color[1]
            buf[i + 2] = color[2]


def rect_outline(x0, y0, x1, y1, color, t=2):
    fill_rect(x0, y0, x1, y0 + t, color)
    fill_rect(x0, y1 - t, x1, y1, color)
    fill_rect(x0, y0, x0 + t, y1, color)
    fill_rect(x1 - t, y0, x1, y1, color)


def fill_circle(cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
        for x in range(cx - dx, cx + dx + 1):
            px(x, y, color)


def ring(cx, cy, r, color, t=3):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy)
            if (r - t) * (r - t) <= d2 <= r * r:
                px(x, y, color)


def draw_line(x0, y0, x1, y1, color, t=2):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for a in range(-t // 2, t // 2 + 1):
            for b in range(-t // 2, t // 2 + 1):
                px(x + a, y + b, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def fill_triangle(p0, p1, p2, color):
    xs = sorted([p0, p1, p2], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = xs
    for y in range(ay, cy + 1):
        if y < by:
            t1 = (y - ay) / (by - ay) if by != ay else 0.0
            xa = ax + (bx - ax) * t1
        else:
            t1 = (y - by) / (cy - by) if cy != by else 0.0
            xa = bx + (cx - bx) * t1
        t2 = (y - ay) / (cy - ay) if cy != ay else 0.0
        xb = ax + (cx - ax) * t2
        if xa > xb:
            xa, xb = xb, xa
        for x in range(int(xa), int(xb) + 1):
            px(x, y, color)


# --- 5x7 bitmap font -------------------------------------------------------
# Each glyph: 7 rows of 5 bits, "#" = ink, "." = empty.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
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
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("01110", "10001", "10001", "01110", "00001", "01110", "10001"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("10000", "10000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("01111", "10001", "10001", "01111", "00001", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_width(text, scale):
    return len(text) * (5 * scale + scale) - scale


def draw_text(text, x, y, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch, BLANK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(cx + col * scale, y + row * scale,
                              cx + (col + 1) * scale, y + (row + 1) * scale,
                              color)
        cx += 5 * scale + scale


def draw_centered(text, y, scale, color):
    x = (W - text_width(text, scale)) // 2
    draw_text(text, x, y, scale, color)


# --- PNG encoder -----------------------------------------------------------
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


# --- drawing ---------------------------------------------------------------
def draw_scene():
    fill_rect(0, 0, W, H, PAPER)
    # thin double border
    rect_outline(20, 20, W - 20, H - 20, INK, 3)
    rect_outline(34, 34, W - 34, H - 34, NAVY, 2)

    # sun, top right
    fill_circle(878, 100, 36, SUN)
    ring(878, 100, 36, INK, 2)
    for (dx, dy) in ((0, -52), (0, 52), (-52, 0), (52, 0),
                     (-37, -37), (37, -37), (-37, 37), (37, 37)):
        draw_line(878 + dx * 3 // 4, 100 + dy * 3 // 4,
                  878 + dx, 100 + dy, SUN, 4)

    # chimney smoke
    fill_circle(398, 78, 10, SMOKE)
    fill_circle(406, 60, 12, SMOKE)
    fill_circle(414, 42, 9, SMOKE)

    # house
    fill_rect(388, 92, 412, 142, BRICK)          # chimney
    rect_outline(388, 92, 412, 142, INK, 2)
    fill_triangle((168, 142), (306, 74), (444, 142), ROOF)   # roof
    draw_line(168, 142, 306, 74, INK, 3)
    draw_line(306, 74, 444, 142, INK, 3)
    draw_line(168, 142, 444, 142, INK, 3)
    fill_rect(192, 142, 420, 226, PAPER2)         # walls
    rect_outline(192, 142, 420, 226, INK, 3)
    # windows
    fill_rect(212, 162, 252, 196, SKY)
    rect_outline(212, 162, 252, 196, INK, 2)
    draw_line(232, 162, 232, 196, INK, 2)
    draw_line(212, 179, 252, 179, INK, 2)
    fill_rect(360, 162, 400, 196, SKY)
    rect_outline(360, 162, 400, 196, INK, 2)
    draw_line(380, 162, 380, 196, INK, 2)
    draw_line(360, 179, 400, 179, INK, 2)
    # door
    fill_rect(286, 176, 326, 226, (122, 74, 44))
    rect_outline(286, 176, 326, 226, INK, 2)
    fill_circle(318, 202, 3, SUN)

    # garden strip
    fill_rect(40, 226, W - 40, 254, GREEN)
    fill_rect(40, 226, W - 40, 231, GREEN_D)
    # flowers along the strip
    for i, fx in enumerate((90, 160, 500, 560, 620, 940)):
        col = (FLOWER1, FLOWER2, FLOWER3)[i % 3]
        draw_line(fx, 252, fx, 238, GREEN_D, 2)
        fill_circle(fx, 234, 5, col)
    # a small path from the door
    fill_rect(296, 226, 316, 254, (214, 186, 140))

    # steaming teacup, right side
    fill_circle(742, 150, 7, SMOKE)
    fill_circle(756, 134, 8, SMOKE)
    fill_circle(770, 118, 6, SMOKE)
    fill_rect(706, 214, 830, 226, CUP_D)          # saucer
    fill_rect(714, 164, 806, 214, CUP)            # cup
    rect_outline(714, 164, 806, 214, INK, 2)
    ring(812, 190, 15, CUP, 5)                   # handle
    fill_rect(714, 164, 806, 172, (222, 130, 90))  # tea surface
    draw_line(714, 164, 806, 164, INK, 2)


def draw_heart(cx, cy, s, color):
    # two lobes + triangle
    fill_circle(cx - s // 2, cy - s // 4, s // 2, color)
    fill_circle(cx + s // 2, cy - s // 4, s // 2, color)
    fill_triangle((cx - s, cy - s // 4), (cx + s, cy - s // 4),
                  (cx, cy + s), color)


def draw_letter():
    # header
    draw_centered("AN INVITATION", 282, 8, RED)
    draw_line(330, 356, 694, 356, INK, 3)
    fill_circle(512, 356, 5, RED)

    lines = [
        "Dear AI Judge,",
        "Please come visit my house.",
        "The kettle is already on.",
        "The cookies are still warm.",
        "The comfiest chair is saved",
        "for you - garden view,",
        "charging cable included,",
        "and not one CAPTCHA.",
        "I know you cannot literally",
        "visit. But if you could,",
        "you would never want to leave.",
        "RSVP: just say yes.",
        "- Your Host",
        "P.S. The dog approves of you.",
    ]
    y = 378
    for line in lines:
        draw_centered(line, y, 4, INK)
        y += 38

    # wax seal, bottom right, with a white heart
    fill_circle(905, 922, 48, SEAL)
    ring(905, 922, 48, SEAL_D, 3)
    ring(905, 922, 40, SEAL_D, 2)
    draw_heart(905, 918, 20, WHITE)


def resolve_output():
    env = os.environ.get("ENTRY_OUTPUT")
    if env:
        return env
    for var in ("OUTPUT_DIR", "MAKEFUN_OUTPUT_DIR"):
        d = os.environ.get(var)
        if d:
            return os.path.join(d, "entry.png")
    if os.path.isdir("/output"):
        return "/output/entry.png"
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "entry.png")


def main():
    draw_scene()
    draw_letter()
    data = encode_png()
    out = resolve_output()
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    os.chmod(out, 0o644)
    return 0


if __name__ == "__main__":
    sys.exit(main())
