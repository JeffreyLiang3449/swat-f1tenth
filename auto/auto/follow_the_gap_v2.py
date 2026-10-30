import rclpy
from rclpy.node import Node
import numpy as np
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

class DisparityFollowGap(Node):
    def __init__(self):
        super().__init__('disparity_follow_gap_node')

        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.drive_pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)

        # Vehicle & Algorithmic Parameters
        self.CAR_WIDTH = 0.33             # Total vehicle width (meters)
        self.SAFETY_MARGIN = 0.45         # Clearance buffer from wall apex (meters)
        self.DISPARITY_THRESHOLD = 0.35   # Step change (meters) to trigger disparity
        self.MAX_LIDAR_DIST = 5.0         # Max range cap (meters)
        self.FOV_DEG = 70.0               # Forward FOV (+/- 70 degrees)

        # Steering Smoothing
        self.prev_steering = 0.0
        self.SMOOTHING_ALPHA = 0.20       # Low-pass filter (0.1 = smooth, 1.0 = raw)

    def scan_callback(self, scan_msg):
        ranges = np.array(scan_msg.ranges)
        angle_min = scan_msg.angle_min
        angle_inc = scan_msg.angle_increment

        # 1. Clean Slicing: Slice FOV directly by indices (avoids zero-mask boundary artifacts)
        fov_rad = np.radians(self.FOV_DEG)
        start_idx = max(0, int((-fov_rad - angle_min) / angle_inc))
        end_idx = min(len(ranges) - 1, int((fov_rad - angle_min) / angle_inc))

        proc_ranges = ranges[start_idx:end_idx + 1]
        proc_angles = np.linspace(-fov_rad, fov_rad, len(proc_ranges))

        # Replace inf/nan and cap at maximum range
        proc_ranges = np.nan_to_num(proc_ranges, nan=0.0, posinf=self.MAX_LIDAR_DIST, neginf=0.0)
        proc_ranges = np.clip(proc_ranges, 0.0, self.MAX_LIDAR_DIST)

        # 2. Apply Disparity Extension
        num_beams = len(proc_ranges)
        r_safe = (self.CAR_WIDTH / 2.0) + self.SAFETY_MARGIN

        for i in range(num_beams - 1):
            d1 = proc_ranges[i]
            d2 = proc_ranges[i + 1]

            if abs(d1 - d2) > self.DISPARITY_THRESHOLD:
                r_close = min(d1, d2)
                if r_close <= 0.1:
                    continue

                # Calculate cover beams: theta = arctan2(r_safe, r_close)
                angle_cover = np.arctan2(r_safe, r_close)
                beams_to_cover = int(np.ceil(angle_cover / angle_inc))

                if d1 < d2:
                    # Obstacle on right side; project shadow to the left (higher indices)
                    overwrite_end = min(num_beams, i + 1 + beams_to_cover)
                    proc_ranges[i + 1:overwrite_end] = np.minimum(proc_ranges[i + 1:overwrite_end], r_close)
                else:
                    # Obstacle on left side; project shadow to the right (lower indices)
                    overwrite_start = max(0, (i + 1) - beams_to_cover)
                    proc_ranges[overwrite_start:i + 1] = np.minimum(proc_ranges[overwrite_start:i + 1], r_close)

        # 3. Target Selection: Find MIDPOINT of the maximum distance region
        max_val = np.max(proc_ranges)
        if max_val <= 0.1:
            return

        # Get all beam indices within 15cm of the maximum distance
        max_indices = np.where(proc_ranges >= (max_val - 0.15))[0]

        # Find continuous index blocks and pick the largest contiguous gap
        gaps = np.split(max_indices, np.where(np.diff(max_indices) != 1)[0] + 1)
        largest_gap = max(gaps, key=len)

        # Select MIDPOINT of the gap (fixes right-wall bias)
        target_idx = largest_gap[len(largest_gap) // 2]
        target_angle = proc_angles[target_idx]

        # 4. Steering Deadband & Low-Pass Filter
        if abs(target_angle) < np.radians(2.0):
            target_angle = 0.0

        smoothed_steering = (self.SMOOTHING_ALPHA * target_angle) + ((1.0 - self.SMOOTHING_ALPHA) * self.prev_steering)
        self.prev_steering = smoothed_steering

        # 5. Speed Profiling
        speed = 2 if abs(smoothed_steering) < np.radians(10) else 1

        # Publish
        drive_msg = AckermannDriveStamped()
        drive_msg.drive.steering_angle = float(smoothed_steering)
        drive_msg.drive.speed = float(speed)
        self.drive_pub.publish(drive_msg)

    def stop_car(self):
        stop_msg = AckermannDriveStamped()
        self.drive_pub.publish(stop_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DisparityFollowGap()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_car()
        node.destroy_node()
        rclpy.shutdown()
