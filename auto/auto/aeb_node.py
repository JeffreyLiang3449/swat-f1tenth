import rclpy
from rclpy.node import Node
import math

from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool

class AEB_Node(Node):
    def __init__(self):
        super().__init__('aeb_node')
        
        self.declare_parameter('min_ttc', 0.2)
        self.min_ttc = self.get_parameter('min_ttc').get_parameter_value().double_value
        
        self.speed = 0.0
        self.brake_triggered = False
        
        self.vel_sub = self.create_subscription(
            Odometry,
            '/ego_racecar/odom',
            self.odom_callback,
            10)
        self.laser_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)
        
        self.aeb_pub = self.create_publisher(Bool, '/aeb', 10)
        self.get_logger().info('AEB node initialized')
        
    def odom_callback(self, msg: Odometry):
        self.speed = msg.twist.twist.linear.x
        
    def scan_callback(self, msg: LaserScan):
        if self.speed <= 0.0:
            return
        
        for i, scan_range in enumerate(msg.ranges):
            if math.isnan(scan_range) or math.isinf(scan_range) or scan_range < msg.range_min:
                continue
            
            angle = msg.angle_min + (i * msg.angle_increment)
            range_rate = self.speed * math.cos(angle)
            
            if range_rate > 0.0:
                ttc = scan_range / range_rate
                if ttc < self.min_ttc:
                    self.get_logger().warn(f'Collision imminent! Time to collision: {ttc:.2f} seconds')
                    self.brake()
                    self.brake_triggered = True
                    return
        if not self.brake_triggered:
            stop_msg = Bool()
            stop_msg.data = False
            self.aeb_pub.publish(stop_msg)
    
    def brake(self):
        stop_msg = Bool()
        stop_msg.data = True
        self.aeb_pub.publish(stop_msg)
        

def main(args=None):
    rclpy.init(args=args)
    aeb = AEB_Node()
    try:
        rclpy.spin(aeb)
    except KeyboardInterrupt:
        aeb.get_logger().info("AEB node shutting down.")
    finally:
        aeb.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
