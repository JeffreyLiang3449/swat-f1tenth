#!/usr/bin/env python3
"""Generate closed race circuits that a real F1TENTH car could run.

  python3 scripts/gen_track.py random [seed]   -> tracks/Random<seed>/
  python3 scripts/gen_track.py squiggle        -> tracks/Squiggle/

A random track is built like procedural racing-game tracks (random points, their outline, edge
midpoints pushed in/out to make hairpins and S-bends, smoothed by a spline), scaled to a lap length, and only kept if it passes the checks F1TENTH venues follow:
  - never crosses itself, and walls of different parts of the track stay >= WALL_GAP apart
  - every corner has centerline radius >= MIN_RADIUS (the car's tightest turn is ~0.75 m)
  - width 1.3-1.9 m, lap 35-80 m (small, tight, fast: typical F1TENTH venue size)
The start line is put on the straightest part of the lap.
"""
import sys

import numpy as np

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from make_tracks import render  # noqa: E402

MIN_RADIUS = 1.2   # m, centerline
WALL_GAP = 0.6     # m of solid wall between neighbouring stretches of track
SPACING = 0.1      # m between centerline points


def resample(xy, spacing=SPACING):
    """Evenly spaced points along a closed curve."""
    closed = np.vstack([xy, xy[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = int(s[-1] / spacing)
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])], axis=1)


def curvature(xy):
    d1 = (np.roll(xy, -1, 0) - np.roll(xy, 1, 0)) / 2
    d2 = np.roll(xy, -1, 0) - 2 * xy + np.roll(xy, 1, 0)
    return np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.linalg.norm(d1, axis=1) ** 3


def valid(xy, width, min_radius=MIN_RADIUS):
    """Why the track fails, or None if it's good."""
    k = curvature(xy)
    if k.max() > 1 / min_radius:
        return f'corner too tight (radius {1 / k.max():.2f} m)'
    # Any two points far apart along the lap must be far apart in space too.
    sub = xy[::5]
    n = len(sub)
    d = np.linalg.norm(sub[:, None] - sub[None], axis=2)
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
    along = np.minimum(abs(i - j), n - abs(i - j)) * 5 * SPACING
    need = width + WALL_GAP
    close = (along > need * 2.5) & (d < need)
    if close.any():
        return 'two parts of the track too close / crossing'
    return None


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def hull(p):
    """Convex hull, counter-clockwise (monotone chain)."""
    p = p[np.lexsort((p[:, 1], p[:, 0]))]
    def half(pts):
        h = []
        for q in pts:
            while len(h) >= 2 and _cross(h[-1] - h[-2], q - h[-2]) <= 0:
                h.pop()
            h.append(q)
        return h[:-1]
    return np.array(half(p) + half(p[::-1]))


def catmull_rom(ctrl, per_seg=60):
    """Smooth closed curve through the control points."""
    out = []
    n = len(ctrl)
    for i in range(n):
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[(i + 1) % n], ctrl[(i + 2) % n]
        t = np.linspace(0, 1, per_seg, endpoint=False)[:, None]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.vstack(out)


def random_track(seed):
    """Procedural circuit: random points -> hull -> push edge midpoints in/out (hairpins, S-bends) -> spline."""
    rng = np.random.default_rng(seed)
    for attempt in range(20000):
        pts = rng.uniform(0, 1, size=(rng.integers(10, 20), 2)) * [1.0, rng.uniform(0.5, 0.9)]
        ctrl = hull(pts)
        displaced = []
        for i in range(len(ctrl)):
            a, b = ctrl[i], ctrl[(i + 1) % len(ctrl)]
            edge = b - a
            normal = np.array([edge[1], -edge[0]])      # points outward for a CCW hull
            mid = (a + b) / 2 + normal * rng.uniform(-0.75, 0.3)   # mostly inward = hairpins
            displaced += [a, mid]
        xy = catmull_rom(np.array(displaced))
        lap = rng.uniform(35, 80)
        xy *= lap / np.linalg.norm(np.diff(np.vstack([xy, xy[:1]]), axis=0), axis=1).sum()
        xy = resample(xy)
        width = round(rng.uniform(1.3, 1.9), 2)
        if valid(xy, width) is None:
            return xy, width, attempt + 1
    raise SystemExit(f'no valid track found for seed {seed}')


def count_corners(xy, radius=5.0):
    """Number of separate stretches tighter than `radius` m."""
    tight = curvature(xy) > 1 / radius
    return int(np.sum(tight & ~np.roll(tight, 1)))


SQUIGGLE = [  # hand-placed control points (m): start straight, S-bend, top dip, left chicane
    (0, 0), (7, 0), (13, 0), (16.5, 1.5), (17, 4.5), (14.5, 6.5), (13, 8.5), (14.5, 10.5),
    (17.5, 12), (16.5, 15), (11.5, 15.5), (8, 13.2), (4.5, 15.5), (0, 15.5), (-3, 13.5), (-3.5, 10.5),
    (-1.6, 8), (-3.5, 5.5), (-3.5, 2), (-2, 0.3),
]


def squiggle():
    """Small fixed practice circuit with lots of different turns."""
    xy = resample(catmull_rom(1.2 * np.array(SQUIGGLE, dtype=float)))
    k = np.exp(-0.5 * (np.arange(-15, 16) * SPACING / 0.5) ** 2)   # round off kinks (0.5 m gaussian)
    k /= k.sum()
    xy = np.stack([np.convolve(np.concatenate([xy[-15:, i], xy[:, i], xy[:15, i]]), k, 'valid')
                   for i in range(2)], axis=1)
    xy = resample(xy)
    width = 1.6
    problem = valid(xy, width, min_radius=1.0)   # one real hairpin; the car can do ~0.75 m
    if problem:
        raise SystemExit(f'squiggle invalid: {problem}')
    return xy, width


def start_on_straight(xy):
    """Rotate the point order so index 0 sits in the middle of the straightest 4 m."""
    k = curvature(xy)
    win = int(4 / SPACING)
    smooth = np.convolve(np.concatenate([k, k[:win]]), np.ones(win), 'valid')[:len(k)]
    return np.roll(xy, -(int(np.argmin(smooth)) + win // 2), axis=0)


def save(name, xy, width):
    xy = start_on_straight(xy)
    half = np.full(len(xy), width / 2)
    out = render(name, xy, half, half)
    np.savetxt(out / f'{name}_centerline.csv', np.column_stack([xy, half, half]),
               delimiter=', ', fmt='%.4f', header='x_m, y_m, w_tr_right_m, w_tr_left_m')
    print(f'  width {width} m, {count_corners(xy)} corners, tightest radius {1 / curvature(xy).max():.1f} m')


if __name__ == '__main__':
    kind = sys.argv[1] if len(sys.argv) > 1 else 'random'
    if kind == 'squiggle':
        xy, width = squiggle()
        save('Squiggle', xy, width)
    else:
        seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(np.random.default_rng().integers(1, 10000))
        xy, width, tries = random_track(seed)
        save(f'Random{seed}', xy, width)
        print(f'  seed {seed} (valid after {tries} tries)')
