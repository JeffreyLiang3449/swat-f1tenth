#!/usr/bin/env python3
"""Republish /scan so nodes that expect "reliable" delivery can read it.

The lidar publishes best-effort (normal for sensors). rf2o subscribes reliable-only, so it never
receives anything and sits at "Waiting for laser_scans". This relays best-effort -> reliable.
"""
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

rclpy.init()
node = rclpy.create_node('scan_relay')
pub = node.create_publisher(LaserScan, '/scan_reliable', 10)
node.create_subscription(LaserScan, '/scan', lambda m: pub.publish(m), qos_profile_sensor_data)
node.get_logger().info('relaying /scan (best effort) -> /scan_reliable (reliable)')
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    pass
