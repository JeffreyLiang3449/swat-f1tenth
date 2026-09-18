import rclpy
from rclpy.node import Node
import math
import time

from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from pid_msgs.msg import PIDInput

class Dist_Finder_Node(Node):
    def __init__(self):
        super().__init__('dist_finder_node')
        
        self.speed = 0.0
        self.time_stamp_before = time.time()
        self.kp = 1
        self.ki = 0.01
        self.kd = 0.09
        self.angle = 0.0
        self.integral = 0.0
        self.prev_error = 0.0
        self.error = 0.0
        self.delta_t = 0.0
        
        self.laser_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10)
        self.odom_sub = self.create_subscription(
            Odometry,
            '/ego_racecar/odom',
            self.odom_callback,
            10)
        self.pid_pub = self.create_publisher(PIDInput, '/pid_calc', 10)
        self.get_logger().info('Distance finder node initialized')
        
    def laser_callback(self, msg: LaserScan):
        t = time.time()
        self.delta_t = t - self.time_stamp_before
        self.time_stamp_before = t
        a_index = int((math.radians(-90) - msg.angle_min) / msg.angle_increment)
        b_index = int((math.radians(-65) - msg.angle_min) / msg.angle_increment)
        a = msg.ranges[a_index]
        b = msg.ranges[b_index]
        if not math.isfinite(a) or not math.isfinite(b):
            return
        theta = math.radians(25)
        alpha = math.atan2(
	    a * math.cos(theta) - b,
    	a * math.sin(theta)
        )
        AB = b * math.cos(alpha)
        AC = self.speed * self.delta_t
        CD = AB + AC * math.sin(alpha)
        self.error = 1 - CD
        self.calculate_pid()

    def odom_callback(self, msg: Odometry):
        self.speed = msg.twist.twist.linear.x

    def calculate_pid(self):
        derivative = 0.0 if self.delta_t <= 1e-6 else (self.error - self.prev_error) / self.delta_t
        self.integral += (self.error * self.delta_t)
        self.theta = self.kp * self.error + self.kd * derivative + self.ki * self.integral
        self.prev_error = self.error
        msg = PIDInput()
        msg.theta = self.theta
        self.pid_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    dist_finder = Dist_Finder_Node()
    try:
        rclpy.spin(dist_finder)
    except KeyboardInterrupt:
        dist_finder.get_logger().info("Distance finder node shutting down.")
    finally:
        dist_finder.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
