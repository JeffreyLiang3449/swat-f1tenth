#!/usr/bin/env python3
"""Import a real (lidar-mapped or hand-drawn) race track map into tracks/<Name>/.

  python3 scripts/import_real.py <Name> <map.yaml>          step 1: clean map + start pose
  python3 scripts/import_real.py --centerline <Name>        step 2 (after rr forza addmap): centerline + start line

Real maps come with extras the sim would treat as drivable (grey "unknown" areas, labels, the floor outside
the track). Step 1 keeps only the drivable loop (the largest white region that encloses an infield), makes
everything else wall, and picks a start pose in the widest part of the track, pointing along it. Step 2 copies
ForzaETH's computed centerline back so the gym can time laps from a proper start line.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
TRACKS = ROOT / 'tracks'
FMAPS = ROOT / 'forzaeth/ws/src/race_stack/stack_master/maps'


def read_yaml(path):
    spec, lines = {}, Path(path).read_text().splitlines()
    for i, line in enumerate(lines):
        if ':' in line and not line.lstrip().startswith('#'):
            k, v = line.split(':', 1)
            v = v.strip()
            if not v:                                   # block list: "origin:\n- x\n- y\n- 0"
                items = []
                for nxt in lines[i + 1:]:
                    if not nxt.strip().startswith('-'):
                        break
                    items.append(nxt.strip()[1:].strip())
                v = '[' + ', '.join(items) + ']'
            spec[k.strip()] = v
    origin = [float(x) for x in spec['origin'].strip('[]').split(',')]
    return spec['image'], float(spec['resolution']), origin, int(float(spec.get('negate', 0)))


def encloses_infield(mask):
    """mask: True = candidate track. True if it has a hole (an infield), i.e. it's a loop."""
    img = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8))
    img = Image.fromarray(np.pad(np.array(img), 1))          # guarantee (0,0) is outside
    ImageDraw.floodfill(img, (0, 0), 128)
    return (np.array(img) == 0).sum() > 200


def track_region(a):
    """Largest white connected region that forms a loop."""
    free = a >= 250
    img = Image.fromarray(np.where(free, 255, 0).astype(np.uint8))
    seen = np.zeros_like(free)
    best, best_n = None, 0
    ys, xs = np.nonzero(free)
    for k in range(0, len(ys), max(1, len(ys) // 4000)):
        y, x = ys[k], xs[k]
        if seen[y, x]:
            continue
        work = img.copy()
        ImageDraw.floodfill(work, (int(x), int(y)), 100)
        comp = np.array(work) == 100
        seen |= comp
        n = comp.sum()
        if n > best_n and n > 2000 and encloses_infield(comp):
            best, best_n = comp, n
    if best is None:
        raise SystemExit('no closed loop found in this map')
    return best


def start_pose(comp, res, origin):
    """Point with the most room around it, heading along the track there."""
    img = Image.fromarray(np.where(comp, 255, 0).astype(np.uint8))
    last = np.array(img) > 0
    for _ in range(200):                       # erode until only the widest part is left
        img = img.filter(ImageFilter.MinFilter(3))
        cur = np.array(img) > 0
        if cur.sum() < 30:
            break
        last = cur
    ys, xs = np.nonzero(last)
    i = len(ys) // 2
    y0, x0 = ys[i], xs[i]
    # heading = main direction of the free space within ~1.5 m
    r = int(1.5 / res)
    yy, xx = np.nonzero(comp[max(0, y0 - r):y0 + r, max(0, x0 - r):x0 + r])
    pts = np.stack([xx, -yy], 1).astype(float)
    pts -= pts.mean(0)
    _, _, vt = np.linalg.svd(pts, full_matrices=False)
    yaw = math.atan2(vt[0][1], vt[0][0])
    H = comp.shape[0]
    return origin[0] + x0 * res, origin[1] + (H - 1 - y0) * res, yaw


def step1(name, yaml_path):
    image, res, origin, negate = read_yaml(yaml_path)
    a = np.array(Image.open(Path(yaml_path).parent / image).convert('L'))
    if negate:
        a = 255 - a
    comp = track_region(a)
    out = TRACKS / name
    out.mkdir(parents=True, exist_ok=True)
    clean = Image.fromarray(np.where(comp, 255, 0).astype(np.uint8))
    clean.save(out / f'{name}.png')
    clean.save(out / f'{name}_clean.png')
    x, y, yaw = start_pose(comp, res, origin)
    spec = (f'resolution: {res}\norigin: [{origin[0]:.4f}, {origin[1]:.4f}, 0.0]\n'
            'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    (out / f'{name}.yaml').write_text(f'image: {name}.png\n' + spec)
    (out / 'forza.yaml').write_text(f'image: {name}.png\n' + spec + f'initial_pose: [{x:.4f}, {y:.4f}, {yaw:.4f}]\n')
    (out / 'start_pose.txt').write_text(f'{x:.4f} {y:.4f} {yaw:.4f}\n')
    print(f'{name}: track area {comp.sum() * res * res:.0f} m^2, start ({x:.1f}, {y:.1f})')


def step2(name):
    d = json.loads((FMAPS / name / 'global_waypoints.json').read_text())
    w = d['centerline_waypoints']['wpnts']
    out = TRACKS / name
    np.savetxt(out / f'{name}_centerline.csv',
               np.array([[p['x_m'], p['y_m'], p['d_right'], p['d_left']] for p in w]),
               delimiter=', ', fmt='%.4f', header='x_m, y_m, w_tr_right_m, w_tr_left_m')
    p0, p1 = w[0], w[1]
    yaw = math.atan2(p1['y_m'] - p0['y_m'], p1['x_m'] - p0['x_m'])
    (out / 'start_pose.txt').write_text(f"{p0['x_m']:.4f} {p0['y_m']:.4f} {yaw:.4f}\n")
    lap = w[-1]['s_m']
    widths = [p['d_left'] + p['d_right'] for p in w]
    print(f'{name}: {lap:.0f} m lap, width {min(widths):.1f}-{max(widths):.1f} m')


if __name__ == '__main__':
    if sys.argv[1] == '--centerline':
        step2(sys.argv[2])
    else:
        step1(sys.argv[1], sys.argv[2])
