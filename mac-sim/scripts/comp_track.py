#!/usr/bin/env python3
"""Competition-style RoboRacer tracks, built the way the real ones are laid out.

  python3 scripts/comp_track.py [seed]      -> tracks/Comp<seed>/

Modeled on the official rules (section 2.2) and on ForzaETH's lidar maps of real race tracks:
  - small and blocky: straight runs of air duct joined at corners, 25-50 m laps, few long straights
  - width varies run by run: choke points at the 1.2 m minimum (4 car widths), normal 1.3-1.8 m,
    wide runs 2.2-3 m; corners come out extra wide (round outside wall, sharp inside corner)
  - sharp corners and hairpins are allowed, but a sharp turn forces enough width for the car
    (min turning radius ~0.75 m) to get around it
  - walls are 33 cm ducts with small gaps the lidar sees through but the car can't fit through

Files in tracks/Comp<seed>/ (same layout as every other track, so `rr sim Comp<seed>` just works):
  Comp<seed>.png / .yaml        sim map: open floor, duct walls with gaps, track
  Comp<seed>_clean.png          track white, everything else black (ForzaETH's planner needs this)
  forza.yaml, start_pose.txt, Comp<seed>_centerline.csv
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / 'tracks'
RES = 0.05           # m per pixel
DUCT = 0.33          # wall thickness, rule 2.2.2
MIN_WIDTH = 1.2      # rule 2.2.4
MARGIN = 2.0         # m of open floor around the outside wall
SPACING = 0.1


def polygon(rng):
    """Star-shaped corner polygon; ~45% of corners pulled in toward the middle make hairpins."""
    while True:
        n = int(rng.integers(7, 12))
        ang = np.sort(rng.uniform(0, 2 * np.pi, n))
        if np.min(np.diff(np.concatenate([ang, ang[:1] + 2 * np.pi]))) < 0.35:
            continue
        r = rng.uniform(0.6, 1.0, n)
        dips = rng.random(n) < 0.45
        r[dips] = rng.uniform(0.25, 0.5, dips.sum())
        p = np.stack([r * np.cos(ang), rng.uniform(0.5, 1.0) * r * np.sin(ang)], 1)
        lap = rng.uniform(25, 50)
        p *= lap / np.linalg.norm(p - np.roll(p, -1, 0), axis=1).sum()
        if np.linalg.norm(p - np.roll(p, -1, 0), axis=1).min() >= 1.5:
            return p


def turn_angles(p):
    u_in = p - np.roll(p, 1, 0)
    u_out = np.roll(p, -1, 0) - p
    cross = u_in[:, 0] * u_out[:, 1] - u_in[:, 1] * u_out[:, 0]
    return np.abs(np.arctan2(cross, (u_in * u_out).sum(1)))   # 0 = straight on, pi = full reversal


def run_widths(p, rng):
    """Width of each straight run (run i goes from corner i to corner i+1)."""
    n = len(p)
    w = rng.uniform(1.3, 1.8, n)
    kind = rng.random(n)
    w[kind < 0.15] = rng.uniform(MIN_WIDTH, 1.3, (kind < 0.15).sum())      # choke points
    w[kind > 0.75] = rng.uniform(2.2, 3.0, (kind > 0.75).sum())            # wide runs
    # a sharp corner needs room for the car to turn: >100 deg needs 1.6 m, >135 deg needs 2.0 m
    th = np.degrees(turn_angles(p))
    need = np.where(th > 135, 2.0, np.where(th > 100, 1.6, MIN_WIDTH))
    w = np.maximum(w, need)                              # run leaving the corner
    w = np.maximum(w, np.roll(need, -1))                 # run arriving at the next corner
    return w


def band(p, w, lo, H, grow=0.0, img=None, fill=255):
    """Draw the track surface: each run a thick line, round joints at corners (outer wall sweeps wide)."""
    px = lambda q: ((q[0] - lo[0]) / RES, H - 1 - (q[1] - lo[1]) / RES)
    d = ImageDraw.Draw(img)
    n = len(p)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        width = (w[i] + grow) / RES
        d.line([px(a), px(b)], fill=fill, width=max(1, int(round(width))))
        for c in (a, b):
            r = width / 2
            x, y = px(c)
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    return img


def is_one_loop(mask):
    """True if the white band splits the image into exactly outside + one infield (a single clean loop)."""
    img = mask.copy()
    ImageDraw.floodfill(img, (0, 0), 128)                # outside floor
    a = np.array(img)
    holes = np.argwhere(a == 0)
    if len(holes) < 400:                                 # no infield at all
        return False
    y, x = holes[0]
    ImageDraw.floodfill(img, (int(x), int(y)), 64)
    return not (np.array(img) == 0).any()                # a second, separate infield = track crosses itself


def build(seed):
    rng = np.random.default_rng(seed)
    for attempt in range(5000):
        p = polygon(rng)
        w = run_widths(p, rng)
        lo = p.min(0) - (w.max() / 2 + DUCT + MARGIN)
        hi = p.max(0) + (w.max() / 2 + DUCT + MARGIN)
        W, H = np.ceil((hi - lo) / RES).astype(int)
        # neighbouring sections must be separated by at least one duct: grow each side by half a duct
        test = band(p, w, lo, H, grow=DUCT + 0.1, img=Image.new('L', (int(W), int(H)), 0))
        if is_one_loop(test) and is_one_loop(band(p, w, lo, H, img=Image.new('L', (int(W), int(H)), 0))):
            return p, w, lo, (int(W), int(H)), attempt + 1
    raise SystemExit(f'no valid track for seed {seed}')


def centerline(p, w):
    """Dense centerline starting mid-way along the longest run, with that run's width at every point."""
    n = len(p)
    seg = np.linalg.norm(np.roll(p, -1, 0) - p, axis=1)
    start = int(np.argmax(seg))
    pts, ws = [], []
    for k in range(n):
        i = (start + k) % n
        a, b = p[i], p[(i + 1) % n]
        m = max(2, int(seg[i] / SPACING))
        t = np.linspace(0, 1, m, endpoint=False)[:, None]
        pts.append(a + (b - a) * t)
        ws.append(np.full(m, w[i]))
    xy, ww = np.vstack(pts), np.concatenate(ws)
    shift = int(seg[start] / SPACING / 2)               # start line in the middle of the longest straight
    return np.roll(xy, -shift, 0), np.roll(ww, -shift)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else int(np.random.default_rng().integers(1, 10000))
    p, w, lo, (W, H), tries = build(seed)
    rng = np.random.default_rng(seed + 1)
    name = f'Comp{seed}'
    out = OUT / name
    out.mkdir(parents=True, exist_ok=True)

    # sim map: open floor (white), duct walls (black), track (white), gaps cut through the walls
    sim = Image.new('L', (W, H), 255)
    band(p, w, lo, H, grow=2 * DUCT, img=sim, fill=0)
    band(p, w, lo, H, img=sim, fill=255)
    d = ImageDraw.Draw(sim)
    px = lambda q: ((q[0] - lo[0]) / RES, H - 1 - (q[1] - lo[1]) / RES)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        L = np.linalg.norm(b - a)
        u = (b - a) / L
        nrm = np.array([-u[1], u[0]])
        s = rng.uniform(0.8, 2.5)
        while s < L - 0.8:                                # a gap every 2.5-4.5 m, both sides
            for side in (1, -1):
                c = a + u * s
                x0 = c + side * nrm * (w[i] / 2 - 0.05)
                x1 = c + side * nrm * (w[i] / 2 + DUCT + 0.05)
                d.line([px(x0), px(x1)], fill=255, width=max(1, int(round(rng.uniform(0.05, 0.10) / RES))))
            s += rng.uniform(2.5, 4.5)
    sim.save(out / f'{name}.png')
    band(p, w, lo, H, img=Image.new('L', (W, H), 0)).save(out / f'{name}_clean.png')

    xy, ww = centerline(p, w)
    yaw = math.atan2(xy[1, 1] - xy[0, 1], xy[1, 0] - xy[0, 0])
    spec = (f'resolution: {RES}\norigin: [{lo[0]:.4f}, {lo[1]:.4f}, 0.0]\n'
            'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    (out / f'{name}.yaml').write_text(f'image: {name}.png\n' + spec)
    (out / 'forza.yaml').write_text(f'image: {name}.png\n' + spec +
                                    f'initial_pose: [{xy[0, 0]:.4f}, {xy[0, 1]:.4f}, {yaw:.4f}]\n')
    (out / 'start_pose.txt').write_text(f'{xy[0, 0]:.4f} {xy[0, 1]:.4f} {yaw:.4f}\n')
    np.savetxt(out / f'{name}_centerline.csv', np.column_stack([xy, ww / 2, ww / 2]),
               delimiter=', ', fmt='%.4f', header='x_m, y_m, w_tr_right_m, w_tr_left_m')

    th = np.degrees(turn_angles(p))
    print(f'{name}  {len(xy) * SPACING:.0f} m lap, {len(p)} corners ({int((th > 100).sum())} sharp), '
          f'width {w.min():.1f}-{w.max():.1f} m  (valid after {tries} tries)')


if __name__ == '__main__':
    main()
