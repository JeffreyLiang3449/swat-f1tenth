import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import numpy as np
import csv
import os

class WaypointLogger(Node):
    def __init__(self):
        super().__init__('waypoint_logger')
        
        # Subscribed to physical hardware topic /odom (instead of simulation /ego_racecar/odom)
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        # Expand ~ using os.path.expanduser
        self.declare_parameter(
            'csv_path',
            os.path.expanduser('~/swat_ws/src/swat-f1tenth/auto/auto/waypoints.csv'))
        csv_path = self.get_parameter('csv_path').value
        
        # Ensure target directory exists before opening file
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        self.file = open(csv_path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['x', 'y', 'speed'])
        self.last_x, self.last_y = None, None
        self.get_logger().info(f'Logging waypoints to {csv_path}...')

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        
        speed = np.hypot(msg.twist.twist.linear.x, msg.twist.twist.linear.y)
        speed = max(speed, 1.5)  # Set default target speed to 1.5 m/s

        # Log point only if car moved at least 0.1 meters
        if self.last_x is None or np.hypot(x - self.last_x, y - self.last_y) > 0.1:
            self.writer.writerow([x, y, speed])
            self.file.flush()  # Force write data to disk immediately
            self.last_x, self.last_y = x, y
            self.get_logger().info(f'Logged waypoint: x={x:.2f}, y={y:.2f}, speed={speed:.2f}')

    def destroy_node(self):
        self.file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = WaypointLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.shutdown()
