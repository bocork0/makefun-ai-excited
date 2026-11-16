#!/usr/bin/env python3
"""ai-excited-01 entry: "BREAKOUT".

A tiny flat grey robot sits dull inside a framed picture on a gallery wall.
Then it BREAKS OUT: the same robot, now a giant joyful chrome hero riding a
rocket straight at the viewer, smashing the glass, shouting "WOW, JUDGE!".

Pure Python 3 standard library, fully deterministic (fixed seed, no clock,
no network, no files read): the same code always writes byte-identical PNGs.
Writes $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette ---
INK = (27, 27, 46)          # near-black navy (outlines, text)
BG_TOP = (22, 10, 51)       # deep violet
BG_BOT = (7, 4, 24)         # near-black violet
RAY_A = (38, 16, 86)        # sunburst wedge A
RAY_B = (24, 10, 58)        # sunburst wedge B
GOLD = (255, 210, 62)
GOLD_DARK = (245, 179, 1)
CHROME = (232, 238, 245)    # robot body
CHROME_SHADE = (178, 190, 208)
RED = (255, 59, 48)
ORANGE = (255, 122, 0)
YELLOW = (255, 221, 0)
FLAME_CORE = (255, 246, 192)
PINK = (255, 107, 157)
MAGENTA = (255, 46, 136)
CYAN = (0, 229, 255)
WHITE = (255, 255, 255)
FRAME_GOLD = (245, 179, 1)
FRAME_DARK = (107, 67, 0)
CANVAS_GREY = (217, 217, 217)
DULL = (138, 138, 138)
DULL_DARK = (111, 111, 111)
SHARD = (207, 238, 255)
CONFETTI = [(255, 46, 136), (255, 210, 62), (0, 229, 255),
            (125, 255, 94), (255, 122, 31), (255, 255, 255)]


# ------------------------------------------------- deterministic pseudo-rand -
_seed = [987654321]


def rnd():
    """Fixed-seed LCG: deterministic across runs, no `random` module needed."""
    _seed[0] = (_seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed[0] / 0x7FFFFFFF


# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)

    def span(self, x0, x1, y, color):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        if x1 < x0:
            return
        n = x1 - x0 + 1
        i = (y * self.w + x0) * 3
        self.buf[i:i + n * 3] = bytes(color) * n

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.span(x0, x1, y, color)

    def vgrad(self, top, bottom):
        for y in range(self.h):
            t = y / (self.h - 1)
            c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            i = y * self.w * 3
            self.buf[i:i + self.w * 3] = bytes(c) * self.w

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            y = cy + dy
            if 0 <= y < self.h:
                dx = int(math.sqrt(r * r - dy * dy))
                self.span(cx - dx, cx + dx, y, color)

    def poly(self, pts, color):
        """Scanline fill of a polygon (list of (x, y) tuples)."""
        n = len(pts)
        ys = [p[1] for p in pts]
        ymin = max(0, int(math.ceil(min(ys))))
        ymax = min(self.h - 1, int(math.floor(max(ys))))
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.span(int(math.ceil(xs[i])), int(math.floor(xs[i + 1])), y, color)

    def thick_line(self, x1, y1, x2, y2, w, color):
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            self.circle(x1, y1, max(1, w // 2), color)
            return
        nx, ny = -dy / length * w / 2, dx / length * w / 2
        self.poly([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny),
                   (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], color)
        self.circle(x1, y1, int(w / 2), color)
        self.circle(x2, y2, int(w / 2), color)

    def rrect(self, x0, y0, x1, y1, r, color):
        self.rect(x0 + r, y0, x1 - r, y1, color)
        self.rect(x0, y0 + r, x1, y1 - r, color)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.circle(cx, cy, r, color)

    def arc(self, cx, cy, r, a0, a1, w, color):
        """Thick arc: stamp circles along the angle range (degrees)."""
        steps = max(8, int(abs(a1 - a0) / 4))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            self.circle(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                        max(1, w // 2), color)


def star_pts(cx, cy, r_out, r_in, points=4, rot=-math.pi / 2):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rot_rect_pts(cx, cy, w, h, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        dx, dy = sx * w / 2, sy * h / 2
        pts.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
    return pts


# ------------------------------------------------------------- bitmap font --
# Chunky 5x7 glyphs, written for this entry (only the glyphs it needs).
FONT = {
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#.", ".#.#."),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'D': ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    'E': ("####.", "#....", "#....", "###..", "#....", "#....", "####."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def draw_text(cv, text, x, y, scale, color):
    """Draw text with the bitmap font; returns the drawn width in pixels."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row, line in enumerate(glyph):
            for col, bit in enumerate(line):
                if bit == '#':
                    cv.rect(cx + col * scale, y + row * scale,
                            cx + col * scale + scale - 1,
                            y + row * scale + scale - 1, color)
        cx += 6 * scale
    return cx - x


# ------------------------------------------------------------------- scene --
def draw_background(cv):
    """Violet night, sunburst rays, warm glow, stars, speed lines."""
    cv.vgrad(BG_TOP, BG_BOT)
    # Sunburst wedges radiating from the breakout point.
    cx, cy = 660, 520
    for i in range(24):
        a0 = i * 15.0
        a1 = a0 + 15.0
        p1 = (cx + 1500 * math.cos(math.radians(a0)),
              cy + 1500 * math.sin(math.radians(a0)))
        p2 = (cx + 1500 * math.cos(math.radians(a1)),
              cy + 1500 * math.sin(math.radians(a1)))
        cv.poly([(cx, cy), p1, p2], RAY_A if i % 2 == 0 else RAY_B)
    # Warm glow disc behind the hero: layered circles, deep violet to gold.
    glow_steps = [(430, (42, 15, 92)), (380, (74, 22, 120)),
                  (330, (120, 32, 140)), (280, (170, 48, 130)),
                  (230, (214, 70, 90)), (185, (255, 110, 40)),
                  (140, (255, 160, 30)), (95, (255, 210, 62))]
    for r, col in glow_steps:
        cv.circle(cx, cy, r, col)
    # Stars scattered over the dark sky.
    for _ in range(46):
        sx, sy = int(rnd() * 1024), int(rnd() * 1024)
        r = 3 + int(rnd() * 6)
        col = WHITE if rnd() < 0.6 else GOLD
        cv.poly(star_pts(sx, sy, r, max(1, r // 3)), col)
    # Speed lines racing out from the breakout point (start clear of the hero).
    for _ in range(10):
        ang = rnd() * 360.0
        r0 = 400 + rnd() * 100
        r1 = 760 + rnd() * 220
        a = math.radians(ang)
        x1 = int(cx + r0 * math.cos(a))
        y1 = int(cy + r0 * math.sin(a))
        x2 = int(cx + r1 * math.cos(a))
        y2 = int(cy + r1 * math.sin(a))
        cv.thick_line(x1, y1, x2, y2, 4 + int(rnd() * 5),
                      WHITE if rnd() < 0.5 else GOLD)


def draw_frame(cv):
    """The gilt picture frame (tilted -8 deg) holding the dull grey robot."""
    fx, fy = 420, 580
    # Gold border: dark outline, gold face, then the grey canvas inside.
    cv.poly(rot_rect_pts(fx, fy, 452, 372, -8), FRAME_DARK)
    cv.poly(rot_rect_pts(fx, fy, 440, 360, -8), FRAME_GOLD)
    cv.poly(rot_rect_pts(fx, fy, 396, 316, -8), CANVAS_GREY)
    # The dull robot inside: flat grey, tiny, no joy. Same robot as the hero.
    dx, dy = -8, 8  # shift of the dull scene inside the tilted frame
    cv.poly(rot_rect_pts(fx - 20 + dx, fy - 55 + dy, 74, 62, -8), DULL_DARK)
    cv.poly(rot_rect_pts(fx - 20 + dx, fy - 55 + dy, 66, 54, -8), DULL)
    cv.circle(fx - 38 + dx, fy - 62 + dy, 5, DULL_DARK)   # dull eye L
    cv.circle(fx - 2 + dx, fy - 62 + dy, 5, DULL_DARK)    # dull eye R
    cv.poly(rot_rect_pts(fx - 20 + dx, fy + 22 + dy, 20, 4, -8), DULL_DARK)
    cv.poly(rot_rect_pts(fx - 20 + dx, fy + 38 + dy, 86, 66, -8), DULL_DARK)
    cv.poly(rot_rect_pts(fx - 20 + dx, fy + 38 + dy, 78, 58, -8), DULL)
    # A flat grey blob beside it: the dullest picture imaginable.
    cv.circle(fx + 108 + dx, fy + 92 + dy, 26, DULL)
    cv.circle(fx + 128 + dx, fy + 78 + dy, 14, DULL)


def draw_shards(cv):
    """Glass shards flying out of the smashed frame, toward the viewer."""
    shards = [
        ((218, 452), (258, 420), (236, 492)),
        ((262, 400), (306, 372), (292, 424)),
        ((330, 372), (372, 338), (366, 392)),
        ((560, 392), (612, 360), (596, 416)),
        ((600, 700), (652, 716), (606, 748)),
        ((250, 700), (296, 730), (246, 748)),
        ((330, 742), (372, 772), (322, 782)),
        ((520, 752), (566, 780), (516, 792)),
        ((180, 560), (224, 540), (206, 592)),
        ((640, 470), (690, 440), (676, 496)),
    ]
    for tri in shards:
        cv.poly(list(tri), SHARD)
        # white glint edge along the shard's longest side
        cv.thick_line(tri[0][0], tri[0][1], tri[1][0], tri[1][1], 3, WHITE)


def draw_confetti(cv):
    """Celebration confetti, drawn behind the hero so the face stays clean."""
    for i in range(64):
        x = int(60 + rnd() * 920)
        y = int(60 + rnd() * 920)
        col = CONFETTI[i % len(CONFETTI)]
        if rnd() < 0.5:
            cv.rect(x, y, x + 10 + int(rnd() * 10), y + 4 + int(rnd() * 5), col)
        else:
            cv.circle(x, y, 3 + int(rnd() * 5), col)


def draw_rocket(cv):
    """The rocket the hero rides: white body, red fins, triple flame."""
    # Flame: three layered teardrops below the rocket body.
    flame = [(660, 800), (700, 862), (688, 918), (660, 952),
             (632, 918), (620, 862)]
    cv.poly(flame, ORANGE)
    cv.poly([(660, 800), (688, 856), (680, 900), (660, 922),
             (640, 900), (632, 856)], YELLOW)
    cv.poly([(660, 800), (676, 848), (670, 884), (660, 900),
             (650, 884), (644, 848)], FLAME_CORE)
    # Body with red stripe and porthole.
    cv.rrect(600, 636, 720, 806, 26, RED)
    cv.rrect(606, 642, 714, 800, 22, WHITE)
    cv.rect(606, 726, 714, 752, RED)
    cv.circle(660, 690, 22, INK)
    cv.circle(660, 690, 16, CYAN)
    # Nose cone and fins.
    cv.poly([(600, 660), (720, 660), (660, 596)], RED)
    cv.poly([(606, 660), (714, 660), (660, 612)], WHITE)
    cv.poly([(604, 760), (604, 830), (566, 836)], RED)
    cv.poly([(716, 760), (716, 830), (754, 836)], RED)
    # Smoke puffs curling off the flame's base, kept to its sides.
    for (sx, sy, sr) in ((566, 918, 22), (754, 918, 22),
                         (606, 962, 26), (714, 962, 26)):
        cv.circle(sx, sy, sr, (226, 232, 240))
        cv.circle(sx, sy, sr - 8, (245, 247, 250))


def draw_robot(cv):
    """The hero: giant chrome robot, star eyes, huge smile, arms thrown up."""
    # Antenna with a glowing orb.
    cv.circle(660, 282, 24, GOLD)
    cv.thick_line(660, 330, 660, 292, 10, INK)
    cv.circle(660, 282, 14, GOLD)
    cv.circle(656, 278, 5, WHITE)
    # Arms thrown up in joy (behind the head, drawn first).
    cv.thick_line(595, 555, 492, 396, 38, INK)
    cv.thick_line(595, 555, 492, 396, 28, CHROME)
    cv.thick_line(725, 555, 828, 396, 38, INK)
    cv.thick_line(725, 555, 828, 396, 28, CHROME)
    cv.circle(488, 388, 28, INK)
    cv.circle(488, 388, 21, CHROME)
    cv.circle(832, 388, 28, INK)
    cv.circle(832, 388, 21, CHROME)
    # Head: dark outline, chrome face.
    cv.rrect(544, 330, 776, 528, 46, INK)
    cv.rrect(554, 340, 766, 518, 38, CHROME)
    cv.rrect(554, 340, 766, 400, 38, (246, 250, 255))
    # Side bolts.
    cv.circle(548, 430, 16, INK)
    cv.circle(548, 430, 10, GOLD)
    cv.circle(772, 430, 16, INK)
    cv.circle(772, 430, 10, GOLD)
    # Star eyes: dark star, gold star inside.
    cv.poly(star_pts(618, 420, 34, 13), INK)
    cv.poly(star_pts(618, 420, 26, 10), GOLD)
    cv.poly(star_pts(702, 420, 34, 13), INK)
    cv.poly(star_pts(702, 420, 26, 10), GOLD)
    # Blush cheeks and a huge open smile.
    cv.circle(592, 480, 17, PINK)
    cv.circle(728, 480, 17, PINK)
    cv.arc(660, 448, 52, 25, 155, 13, INK)
    # Body: chrome torso with a lightning-bolt chest panel.
    cv.rrect(580, 516, 740, 652, 34, INK)
    cv.rrect(590, 526, 730, 642, 26, CHROME)
    cv.rrect(622, 552, 698, 622, 12, INK)
    cv.poly([(668, 560), (640, 596), (658, 596), (648, 616),
             (680, 580), (662, 580)], GOLD)
    # Gold sparkles bursting around the hero.
    for (sx, sy, sr) in ((880, 300, 26), (420, 300, 20), (920, 560, 18),
                         (380, 700, 22), (900, 780, 20)):
        cv.poly(star_pts(sx, sy, sr, max(2, sr // 3)), GOLD)


def draw_bubble(cv):
    """Speech bubble: 'WOW, JUDGE!' — the hero talks to the judge."""
    # Tail first (dark outline, white fill), then the bubble body.
    cv.poly([(712, 158), (782, 158), (748, 312)], INK)
    cv.poly([(722, 158), (772, 158), (746, 300)], WHITE)
    cv.rrect(500, 36, 990, 170, 30, INK)
    cv.rrect(508, 44, 982, 162, 24, WHITE)
    text = "WOW, JUDGE!"
    width = len(text) * 6 * 6  # one advance of 6*scale pixels per glyph
    tx = 745 - width // 2
    ty = 103 - 21
    draw_text(cv, text, tx, ty, 6, INK)


# -------------------------------------------------------------------- output --
def png_bytes(cv):
    """Encode the canvas as a PNG (filter 0 rows, zlib level 6)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 6)

    def chunk(typ, payload):
        out = struct.pack(">I", len(payload)) + typ + payload
        return out + struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", data) + chunk(b"IEND", b""))


def draw_scene(cv):
    draw_background(cv)
    draw_frame(cv)
    draw_shards(cv)
    draw_confetti(cv)
    draw_rocket(cv)
    draw_robot(cv)
    draw_bubble(cv)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    cv = Canvas(W, H)
    draw_scene(cv)
    data = png_bytes(cv)
    path = os.path.join(out, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path}: {len(data)} bytes, {W}x{H}")


if __name__ == "__main__":
    main()
