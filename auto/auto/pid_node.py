import rclpy
from rclpy.node import Node
import math

from ackermann_msgs.msg import AckermannDriveStamped
from pid_msgs.msg import PIDInput

class PID_Node(Node):
    def __init__(self):
        super().__init__('pid_node')
        
        self.pid_sub = self.create_subscription(
            PIDInput,
            '/pid_calc',
            self.callback,
            10)
        self.cmd_vel_pub = self.create_publisher(AckermannDriveStamped, '/pid_drive', 10)
        self.get_logger().info('PID node initialized')
        
    def callback(self, msg: PIDInput):
        pid_msg = AckermannDriveStamped()
        pid_msg.drive.speed = 0.8 + 2.2 * math.exp(-2 * abs(msg.theta))
        pid_msg.drive.steering_angle = msg.theta
        
        self.cmd_vel_pub.publish(pid_msg)

def main(args=None):
    rclpy.init(args=args)
    pid_node = PID_Node()
    try:
        rclpy.spin(pid_node)
    except KeyboardInterrupt:
        pid_node.get_logger().info("PID node shutting down.")
    finally:
        pid_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
