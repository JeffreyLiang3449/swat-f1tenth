#!/usr/bin/env python3
"""Put the sim car back on the start line whenever it crashes, and time laps (started by `rr sim`).

The gym only reports collisions on /ego_racecar/collision; it doesn't stop the car, so without this a
crashed car drives through the wall. Usage: auto_reset.py X Y YAW [--once]
  --once   reset right now and exit (that's `rr reset`)
Laps are timed from the start line (through the start pose, across the track) and printed as
"lap #N in X s"; `rr laps` reads them. A crash abandons the lap in progress.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


def pose_msg(node, x, y, yaw):
    m = PoseWithCovarianceStamped()
    m.header.frame_id = 'map'
    m.header.stamp = node.get_clock().now().to_msg()
    m.pose.pose.position.x, m.pose.pose.position.y = x, y
    m.pose.pose.orientation.z, m.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    return m


def main():
    x, y, yaw = (float(v) for v in sys.argv[1:4])
    rclpy.init()
    node = rclpy.create_node('auto_reset')
    pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)

    if '--once' in sys.argv:
        for _ in range(20):             # wait for the bridge to be listening
            if pub.get_subscription_count():
                break
            rclpy.spin_once(node, timeout_sec=0.1)
        pub.publish(pose_msg(node, x, y, yaw))
        rclpy.spin_once(node, timeout_sec=0.2)
        print('car reset to start')
        return

    now = lambda: node.get_clock().now().nanoseconds * 1e-9
    state = {'crashes': 0, 'last': 0.0, 'laps': 0, 'lap_start': None, 'prev_d': None, 'best': None}
    hx, hy = math.cos(yaw), math.sin(yaw)

    def on_collision(msg):
        if msg.data and now() - state['last'] > 1.0:
            state['crashes'] += 1
            state['last'] = now()
            state['lap_start'], state['prev_d'] = None, None      # lap in progress doesn't count
            node.get_logger().warn(f'crash #{state["crashes"]}: back to the start line')
            pub.publish(pose_msg(node, x, y, yaw))

    def on_odom(msg):
        px, py = msg.pose.pose.position.x - x, msg.pose.pose.position.y - y
        d = px * hx + py * hy                    # distance past the start line along the start heading
        side = abs(px * hy - py * hx)            # distance from the start point across the track
        t = now()
        if state['lap_start'] is None:           # just started or reset: clock starts when the car moves
            if abs(msg.twist.twist.linear.x) > 0.1:
                state['lap_start'] = t
        elif state['prev_d'] is not None and state['prev_d'] < 0 <= d and side < 2.0:
            lap = t - state['lap_start']
            if lap > 2.0:
                state['laps'] += 1
                state['best'] = lap if state['best'] is None else min(state['best'], lap)
                node.get_logger().info(f'lap #{state["laps"]} in {lap:.3f} s (best {state["best"]:.3f} s)')
            state['lap_start'] = t
        state['prev_d'] = d

    node.create_subscription(Bool, '/ego_racecar/collision', on_collision, 10)
    node.create_subscription(Odometry, '/ego_racecar/odom', on_odom, 10)
    node.get_logger().info(f'auto-reset on: crashes return the car to ({x:.1f}, {y:.1f})')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
