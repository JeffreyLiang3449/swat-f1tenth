"""Shared plumbing so each algorithm file only has to implement `on_scan`.

Topics match both the f1tenth_gym_ros sim and the real car (f1tenth_system):
  in:  /scan (LaserScan)          out: /drive (AckermannDriveStamped)
  in:  odom  (Odometry) -- /ego_racecar/odom in sim, /odom on the car; set with -p odom_topic:=...
"""
import math

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped

MAX_STEER = 0.4189  # rad, F1TENTH steering limit


class RacerNode(Node):
    def __init__(self, name, **defaults):
        super().__init__(name)
        params = {'scan_topic': '/scan', 'drive_topic': '/drive',
                  'odom_topic': '/ego_racecar/odom', 'max_speed': 2.0, **defaults}
        for key, value in params.items():
            self.declare_parameter(key, value)

        self.odom = None
        self.drive_pub = self.create_publisher(AckermannDriveStamped, self.p('drive_topic'), 10)
        self.create_subscription(LaserScan, self.p('scan_topic'), self._scan_cb, 10)
        self.create_subscription(Odometry, self.p('odom_topic'), self._odom_cb, 10)
        self.get_logger().info(f'{name} up: {self.p("scan_topic")} -> {self.p("drive_topic")}')

    def p(self, key):
        """Read a parameter live, so `ros2 param set` tunes the running node."""
        return self.get_parameter(key).value

    def _odom_cb(self, msg):
        self.odom = msg

    def _scan_cb(self, scan):
        ranges = np.nan_to_num(np.asarray(scan.ranges, dtype=float),
                               nan=0.0, posinf=scan.range_max, neginf=0.0)
        angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
        result = self.on_scan(ranges, angles, scan)
        if result is not None:
            self.drive(*result)

    def on_scan(self, ranges, angles, scan):
        """Return (speed m/s, steering rad), or None to publish nothing. Angle 0 = straight ahead, + = left."""
        raise NotImplementedError

    def drive(self, speed, steer):
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.drive.speed = float(np.clip(speed, -self.p('max_speed'), self.p('max_speed')))
        msg.drive.steering_angle = float(np.clip(steer, -MAX_STEER, MAX_STEER))
        self.drive_pub.publish(msg)

    def range_at(self, ranges, angles, angle):
        """Range of the beam closest to `angle` (rad)."""
        return float(ranges[int(np.argmin(np.abs(angles - angle)))])


def spin(node_cls):
    rclpy.init()
    node = node_cls()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.drive(0.0, 0.0)  # stop the car on Ctrl-C
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


deg = math.radians
