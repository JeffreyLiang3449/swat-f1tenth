"""NAME: describe the idea here.

Created by `rr new NAME`. Run with `rr run NAME` after `rr build`.
"""
from racer_algos._base import RacerNode, spin, deg


class Algo(RacerNode):
    def __init__(self):
        # Every keyword here becomes a ROS parameter you can change live with `ros2 param set`.
        super().__init__('NAME', speed=1.0, gain=1.0)

    def on_scan(self, ranges, angles, scan):
        # ranges/angles are numpy arrays; angle 0 = straight ahead, + = left.
        # self.odom holds the latest Odometry (or None).
        ahead = self.range_at(ranges, angles, 0.0)
        left = self.range_at(ranges, angles, deg(90))
        right = self.range_at(ranges, angles, deg(-90))
        steer = self.p('gain') * (left - right) * 0.1
        speed = self.p('speed') if ahead > 1.0 else 0.3
        return speed, steer   # (m/s, rad)


def main():
    spin(Algo)


if __name__ == '__main__':
    main()
