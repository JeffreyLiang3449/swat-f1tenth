"""Follow-the-Gap: bubble out the closest obstacle, drive toward the deepest point of the widest free gap.

Run:  rr run follow_the_gap
Tune live:  ros2 param set /follow_the_gap bubble_radius 0.4
"""
import numpy as np

from racer_algos._base import RacerNode, spin, deg


class FollowTheGap(RacerNode):
    def __init__(self):
        super().__init__('follow_the_gap',
                         fov_deg=90.0,          # look +/- this many degrees
                         clip_range=3.0,        # m, ignore anything farther (keeps it from chasing long hallways)
                         smooth_window=5,       # beams in moving average
                         bubble_radius=0.3,     # m, cleared around the closest point
                         gap_threshold=1.0,     # m, a beam counts as free if farther than this
                         speed_straight=2.0,
                         speed_corner=1.0,
                         corner_angle_deg=10.0)

    def on_scan(self, ranges, angles, scan):
        front = np.abs(angles) <= deg(self.p('fov_deg'))
        r = np.clip(ranges[front], 0.0, self.p('clip_range'))
        a = angles[front]

        w = int(self.p('smooth_window'))
        if w > 1:
            r = np.convolve(r, np.ones(w) / w, mode='same')

        # Zero out a bubble around the closest point.
        closest = int(np.argmin(np.where(r > 0.0, r, np.inf)))
        d = max(r[closest], 0.05)
        half_width = np.arctan2(self.p('bubble_radius'), d)
        r = r.copy()
        r[np.abs(a - a[closest]) <= half_width] = 0.0

        # Widest run of free beams.
        free = r > self.p('gap_threshold')
        if not free.any():
            return 0.0, 0.0
        edges = np.diff(np.concatenate(([0], free.astype(int), [0])))
        starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
        i = int(np.argmax(ends - starts))
        s, e = starts[i], ends[i]

        # Aim at the deepest point in the gap (ties broken toward the gap center).
        gap = r[s:e]
        deepest = np.flatnonzero(gap >= gap.max() - 0.05)
        target = s + deepest[np.argmin(np.abs(deepest - len(gap) / 2))]
        steer = float(a[target])

        corner = abs(steer) > deg(self.p('corner_angle_deg'))
        return (self.p('speed_corner') if corner else self.p('speed_straight')), steer


def main():
    spin(FollowTheGap)


if __name__ == '__main__':
    main()
