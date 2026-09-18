import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool
from ackermann_msgs.msg import AckermannDriveStamped

class DriveNode(Node):
    def __init__(self):
        super().__init__('drive_node')
        
        self.aeb_active = False
        self.nav_cmd = AckermannDriveStamped()
        
        self.aeb_sub = self.create_subscription(
            Bool,
            '/aeb',
            self.aeb_callback,
            10)
        self.pid_sub = self.create_subscription(
            AckermannDriveStamped,
            '/pid_drive',
            self.drive_callback,
            10)
        self.drive = self.create_publisher(AckermannDriveStamped, '/drive', 10)
        self.get_logger().info('Driver node initialized')
        
    def aeb_callback(self, msg: Bool):
        self.aeb_active = msg.data
    
    def drive_callback(self, msg: AckermannDriveStamped):
        self.nav_cmd = msg
        if self.aeb_active:
            stop_msg = AckermannDriveStamped()
            stop_msg.drive.speed = 0.0
            stop_msg.drive.steering_angle = 0.0
            self.drive.publish(stop_msg)
        else:
            self.drive.publish(self.nav_cmd)

def main(args=None):
    rclpy.init(args=args)
    drive = DriveNode()
    rclpy.spin(drive)
    drive.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
