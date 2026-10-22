"""PID wall following (the classic F1TENTH lab). Holds `target_dist` from the left wall.

Run:  rr run wall_follow
Tune live:  ros2 param set /wall_follow kp 1.5
"""
import math

from racer_algos._base import RacerNode, spin, deg


class WallFollow(RacerNode):
    def __init__(self):
        super().__init__('wall_follow',
                         target_dist=1.0,   # m from the left wall
                         lookahead=1.0,     # m, projects the error forward
                         theta_deg=50.0,    # angle between the two beams
                         kp=1.0, ki=0.0, kd=0.1)
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_t = None

    def on_scan(self, ranges, angles, scan):
        theta = deg(self.p('theta_deg'))
        b = self.range_at(ranges, angles, deg(90.0))           # straight left
        a = self.range_at(ranges, angles, deg(90.0) - theta)   # left and ahead
        if a <= 0.0 or b <= 0.0:
            return None

        alpha = math.atan2(a * math.cos(theta) - b, a * math.sin(theta))
        dist = b * math.cos(alpha) + self.p('lookahead') * math.sin(alpha)
        error = self.p('target_dist') - dist   # > 0 means too close to the wall

        t = self.get_clock().now().nanoseconds * 1e-9
        dt = (t - self.prev_t) if self.prev_t else 0.0
        self.prev_t = t
        if dt > 0:
            self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error

        steer = -(self.p('kp') * error + self.p('ki') * self.integral + self.p('kd') * derivative)
        s = abs(steer)
        speed = 1.5 if s < deg(10) else 1.0 if s < deg(20) else 0.5
        return speed, steer


def main():
    spin(WallFollow)


if __name__ == '__main__':
    main()
