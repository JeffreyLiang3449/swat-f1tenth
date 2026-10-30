import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data  # <-- Import Sensor QoS
import numpy as np
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

class FollowTheGap(Node):
    def __init__(self):
        super().__init__('follow_the_gap_node')
        
        # Use qos_profile_sensor_data for Best Effort LiDAR topics
        self.scan_sub = self.create_subscription(
            LaserScan, 
            '/scan', 
            self.scan_callback, 
            qos_profile_sensor_data
        )
        self.drive_pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)
        
        self.bubble_radius = 100       
        self.max_range = 3.5          
        self.fov_deg = 85             

    def preprocess_lidar(self, ranges, angle_min, angle_increment):
        proc_ranges = np.array(ranges)
        proc_ranges = np.clip(proc_ranges, 0, self.max_range)
        
        fov_rad = np.radians(self.fov_deg)
        center_idx = len(proc_ranges) // 2
        fov_indices = int(fov_rad / angle_increment)
        
        left_idx = max(0, center_idx - fov_indices)
        right_idx = min(len(proc_ranges), center_idx + fov_indices)
        
        proc_ranges[:left_idx] = 0.0
        proc_ranges[right_idx:] = 0.0
        
        return proc_ranges, left_idx, right_idx

    def scan_callback(self, scan_msg):
    	# 0. Clean NaN and Inf values from raw scan
    	raw_ranges = np.array(scan_msg.ranges)
    	clean_ranges = np.nan_to_num(raw_ranges, copy=True, nan=0.0, posinf=self.max_range, neginf=0.0)
    
    	proc_ranges, left_idx, right_idx = self.preprocess_lidar(clean_ranges, scan_msg.angle_min, scan_msg.angle_increment)
    
    	# 1. Find closest obstacle point in active range
    	valid_indices = np.where(proc_ranges > 0.0)[0]
    	if len(valid_indices) == 0:
            return
    	closest_idx = valid_indices[np.argmin(proc_ranges[valid_indices])]
    
    	# 2. Draw Safety Bubble around closest obstacle
    	start_b = max(0, closest_idx - self.bubble_radius)
    	end_b = min(len(proc_ranges), closest_idx + self.bubble_radius)
    	proc_ranges[start_b:end_b] = 0.0
    
    	# 3. RE-CALCULATE gap indices AFTER setting the bubble to zero
    	gap_indices = np.where(proc_ranges > 0.0)[0]
    	if len(gap_indices) == 0:
            return
        
    	# 4. Find Max Gap (longest consecutive non-zero index sequence)
    	non_zero_runs = np.split(gap_indices, np.where(np.diff(gap_indices) != 1)[0] + 1)
    	max_gap = max(non_zero_runs, key=len) if len(non_zero_runs) > 0 else []
    	if len(max_gap) == 0:
            return
        
    	# 5. Target center of max gap
    	target_idx = int(np.mean(max_gap))
    	steering_angle = scan_msg.angle_min + (target_idx * scan_msg.angle_increment)
    
    	# 6. Publish drive command
    	drive_msg = AckermannDriveStamped()
    	drive_msg.header.stamp = self.get_clock().now().to_msg()
    	drive_msg.drive.steering_angle = float(steering_angle)
    
    	# Dynamic Speed: Slow down when turning sharply
    	if abs(steering_angle) > 0.2:
            drive_msg.drive.speed = 0.8  # Turn speed (m/s)
    	else:
            drive_msg.drive.speed = 1.6  # Straight speed (m/s)
        
    	self.drive_pub.publish(drive_msg)
    	self.get_logger().info(f'Steering: {steering_angle:.2f} rad | Target Index: {target_idx}')

def main(args=None):
    rclpy.init(args=args)
    node = FollowTheGap()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
