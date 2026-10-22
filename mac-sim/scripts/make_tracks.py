#!/usr/bin/env python3
"""Turn f1tenth_racetracks (tracks/src) into clean closed-circuit maps in tracks/<Name>/.

Each track is re-rendered from its centerline + widths: track = white, everything else = black,
so the car can't leave and ForzaETH's planner can skeletonize it. Writes per track:
  <Name>.png, <Name>.yaml            gym map (plain map_server yaml)
  <Name>_centerline.csv, _raceline.csv   copied, so the gym counts laps
  forza.yaml                         same map + initial_pose, for ForzaETH's planner
  start_pose.txt                     "x y yaw" for the sim's spawn point
Run on the Mac:  python3 scripts/make_tracks.py [Name ...]
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'tracks' / 'src'
OUT = ROOT / 'tracks'
RES = 0.05     # m/pixel, matches the F1TENTH maps
MARGIN = 2.0   # m of black border


def build(name):
    d = SRC / name
    cl = next(d.glob('*_centerline.csv'))
    name = cl.name[:-len('_centerline.csv')]   # file prefix can differ from the folder ("Mexico City")
    c = np.loadtxt(cl, delimiter=',', comments='#')
    out = render(name.replace(' ', ''), c[:, :2], c[:, 2], c[:, 3])
    for kind in ('centerline', 'raceline'):
        if (d / f'{name}_{kind}.csv').exists():
            shutil.copy(d / f'{name}_{kind}.csv', out / f'{out.name}_{kind}.csv')


def render(clean, xy, w_right, w_left):
    """Draw a closed-loop track (centerline + widths) into tracks/<clean>/ and write its yaml files."""
    # Closed loop: tangent from neighbors on both sides, left normal = tangent rotated +90 deg.
    t = np.roll(xy, -1, axis=0) - np.roll(xy, 1, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = np.stack([-t[:, 1], t[:, 0]], axis=1)
    left = xy + n * w_left[:, None]
    right = xy - n * w_right[:, None]

    pts = np.vstack([left, right])
    lo = pts.min(axis=0) - MARGIN
    hi = pts.max(axis=0) + MARGIN
    w, h = np.ceil((hi - lo) / RES).astype(int)

    def px(p):  # world -> image pixel (row 0 is the top = max y)
        return [((x - lo[0]) / RES, h - 1 - (y - lo[1]) / RES) for x, y in p]

    def area(p):
        x, y = p[:, 0], p[:, 1]
        return abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2

    outer, inner = (left, right) if area(left) > area(right) else (right, left)
    img = Image.new('L', (int(w), int(h)), 0)
    draw = ImageDraw.Draw(img)
    draw.polygon(px(outer), fill=255)
    draw.polygon(px(inner), fill=0)

    out = OUT / clean
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / f'{clean}.png')
    yaw = math.atan2(xy[1, 1] - xy[0, 1], xy[1, 0] - xy[0, 0])
    base = (f'image: {clean}.png\nresolution: {RES}\norigin: [{lo[0]:.4f}, {lo[1]:.4f}, 0.0]\n'
            'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    (out / f'{clean}.yaml').write_text(base)
    (out / 'forza.yaml').write_text(base + f'initial_pose: [{xy[0, 0]:.4f}, {xy[0, 1]:.4f}, {yaw:.4f}]\n')
    (out / 'start_pose.txt').write_text(f'{xy[0, 0]:.4f} {xy[0, 1]:.4f} {yaw:.4f}\n')
    length = np.linalg.norm(np.diff(xy, axis=0), axis=1).sum()
    print(f'{clean:14s} {length:6.0f} m lap, {w}x{h} px')
    return out


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(p.name for p in SRC.iterdir()
                                   if p.is_dir() and any(p.glob('*_centerline.csv')))
    for name in names:
        build(name)
