import rclpy
from rclpy.node import Node
import numpy as np
import csv
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped

def euler_from_quaternion(q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return np.arctan2(siny_cosp, cosy_cosp)

class PurePursuit(Node):
    def __init__(self):
        super().__init__('pure_pursuit_node')
        self.sub = self.create_subscription(Odometry, '/ego_racecar/odom', self.odom_callback, 10)
        self.pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)
        
        # Pure Pursuit Tuning Parameters
        self.LWB = 0.33             # Wheelbase (meters)
        self.K_V = 0.35            # Lookahead velocity gain
        self.MIN_LOOKAHEAD = 0.60  # Tight tracking in sharp turns
        self.MAX_LOOKAHEAD = 1.50  # High-speed straightaway stability
        self.LOOKAHEAD = 0.9        # Lookahead distance Ld (meters)

        # Load Map Waypoints
        waypoints_path = 'src/auto/auto/waypoints.csv'
        self.waypoints = np.loadtxt(waypoints_path, delimiter=',', skiprows=1)
        self.get_logger().info(f'Loaded {len(self.waypoints)} waypoints.')

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        yaw = euler_from_quaternion(msg.pose.pose.orientation)

        num_pts = len(self.waypoints)
        dx = self.waypoints[:, 0] - x
        dy = self.waypoints[:, 1] - y

        # 1. Find the index of the waypoint CLOSEST to the car
        distances_all = np.hypot(dx, dy)
        nearest_idx = np.argmin(distances_all)

        # dynamically adjust lookahead distance based on current speed
        current_speed = msg.twist.twist.linear.x
        self.LOOKAHEAD = np.clip(self.K_V * current_speed, self.MIN_LOOKAHEAD, self.MAX_LOOKAHEAD)

        # 2. Look FORWARD along the track loop for the lookahead point
        target_idx = nearest_idx
        for i in range(num_pts):
            idx = (nearest_idx + i) % num_pts
            if distances_all[idx] >= self.LOOKAHEAD:
                target_idx = idx
                break

        # 3. Transform ONLY the selected target point to local vehicle coordinates
        target_dx = self.waypoints[target_idx, 0] - x
        target_dy = self.waypoints[target_idx, 1] - y
        local_x = target_dx * np.cos(-yaw) - target_dy * np.sin(-yaw)
        local_y = target_dx * np.sin(-yaw) + target_dy * np.cos(-yaw)

        # 4. Compute curvature-based steering: delta = 2 * Lwb * y / (Ld^2)
        L_d = max(distances_all[target_idx], 0.1)  # Real distance to target
        steering_angle = np.arctan2(2.0 * self.LWB * local_y, L_d**2)

        # 5. Speed Profiling
        target_speed = self.waypoints[target_idx, 2]
        
        drive_msg = AckermannDriveStamped()
        drive_msg.drive.steering_angle = float(steering_angle)
        drive_msg.drive.speed = float(target_speed)
        self.pub.publish(drive_msg)
    def stop_car(self):
        stop_msg = AckermannDriveStamped()
        self.pub.publish(stop_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PurePursuit()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_car()
        node.destroy_node()
        rclpy.shutdown()
