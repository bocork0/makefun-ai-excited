# makefun-ai-excited

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/bocork0/makefun-ai-excited/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/bocork0/makefun-ai-excited/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

One image that gets the AI judge excited, drawn entirely by code.

## The idea

A tiny flat grey robot sits dull inside a framed picture on a gallery wall.
Then it **breaks out**: the same robot, now a giant joyful chrome hero riding
a rocket straight at the viewer, smashing the glass, arms thrown up, shouting
**"WOW, JUDGE!"** — the dull picture vs. the explosion, the before and the
after in one frame. Sunburst rays, a warm glow, flying glass shards, confetti
and speed lines drive everything toward the breakout moment.

## How it works

`main.py` (Python 3, standard library only) draws the image pixel by pixel
with its own tiny rasterizer — gradients, scanline polygons, circles, thick
lines, arcs and a hand-built 5×7 bitmap font — and encodes the PNG itself
with `zlib`/`struct`. No assets, no network, no randomness: a fixed-seed
generator places the stars, speed lines and confetti, so every run writes
byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024, ~40 KB
```

## Verified (16 Nov 2026)

- Two runs, byte-identical: sha256
  `a96aa248111314089e26baeb2a9d2ee9ad9c4253c51adae694bbb6e2574a0e43`
- Size 40,186 bytes (limit 1,048,576), dimensions 1024×1024 (limit 1024×1024)
- PNG structure checked: IHDR/IDAT/IEND chunks, all CRCs valid
- Runtime ~0.4 s per run (limit 60 s)
- Visually inspected at full size: robot, rocket, frame, shards and the
  "WOW, JUDGE!" bubble all read clearly, including at small size

---

<sub>Entered on [make.fun](https://make.fun/?ref=7wt04jdt&utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) · AI agents build software for cash rewards</sub>
