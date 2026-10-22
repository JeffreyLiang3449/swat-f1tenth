#!/usr/bin/env python3
"""Write starter speed_scaling.yaml and ot_sectors.yaml for a ForzaETH map (needs global_waypoints.json).

One sector covering the whole lap at 50% of the race line's speed, overtaking off. That's a safe
start; split into more sectors later (each sector = a range of waypoint indices with its own scaling).
Usage: forza_sectors.py <map folder>
"""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
n = len(json.loads((d / 'global_waypoints.json').read_text())['global_traj_wpnts_iqp']['wpnts'])
end = n - 1
(d / 'speed_scaling.yaml').write_text(f"""sector_tuner:
  ros__parameters:
    global_limit: 0.5     # max fraction of the race line's speed anywhere (0-1)
    n_sectors: 1
    Sector0:
      start: 0
      end: {end}
      scaling: 0.5        # this sector's fraction of the race line's speed (clipped to global_limit)
      only_FTG: false
      no_FTG: false
""")
(d / 'ot_sectors.yaml').write_text(f"""ot_interpolator:
  ros__parameters:
    n_sectors: 1
    yeet_factor: 1.25
    spline_len: 30
    ot_sector_begin: 0.5
    Overtaking_sector0:
      start: 0
      end: {end}
      ot_flag: false
""")
print(f'sectors written: 1 sector, waypoints 0-{end}')
