import rclpy
from rclpy.node import Node
import math

from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

def double_list_dump(var_name, array):
    print_str = var_name + f' is: [['
    for i in range(len(array)):
        for j in range(len(array[i])):
            print_str += f'{array[i][j]}'
            if not j == len(array[i]) - 1:
                print_str += f', '
        if not i == len(array) - 1:
            print_str += f', '
        print_str += f' ]'
    print_str += f' ]'
    print(print_str)

def single_list_dump(var_name, array):
    print_str = var_name + f' is: [['
    for i in range(len(array)):
        print_str += f'{array[i]}'
        if not i == len(array) - 1:
            print_str += f', '
    print_str += f' ]'
    print(print_str)

class DisparityExtender(Node):
    def __init__(self):
        super().__init__('disparity_extender_node')

        self.theta = 0.0

        self.laser_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10
        )
        self.move = self.create_publisher(AckermannDriveStamped, '/drive', 10)
        self.get_logger().info('Disparity extender node initialized')

    def laser_callback(self, msg: LaserScan):
        blocked = True
        pre_processed_ranges = [msg.ranges[0]]
        processed_ranges = []
        ranges = list(msg.ranges)
        single_list_dump('before inf processing, ranges', ranges)                                                                 # 50
        for i in range(len(ranges)):
            if not math.isfinite(ranges[i]):
                ranges[i] = msg.range_max
        i = 1
        single_list_dump('after inf processing, ranges', ranges)                                                                  # 55
        while i < len(ranges):
            if abs(ranges[i] - ranges[i - 1]) <= 0.7:
                i += 1
                continue
            disparity = min(ranges[i - 1], ranges[i])
            num_rays = math.ceil(math.atan2(0.155, disparity) / msg.angle_increment)
            if disparity == ranges[i - 1]:
                for j in range(i, min(i + num_rays, len(ranges))):
                    ranges[j] = disparity
                i += num_rays
            else:
                for j in range(i - 1, max(0, i - num_rays - 1), -1):
                    ranges[j] = disparity
                i += 1

        for index, dist in enumerate(ranges):
            if dist < 0.5:
                blocked = True
                continue
            if blocked:
                end_index = index
                processed_ranges.append([index, end_index])
            processed_ranges[len(processed_ranges) - 1][1] += 1
            blocked = False
        if not processed_ranges:
            return
        widest_gap_length = processed_ranges[0][1] - processed_ranges[0][0]
        widest_index_start = 0
        widest_index_end = 0
        for a, b in processed_ranges:
            if b - a > widest_gap_length:
                widest_gap_length = b - a
                widest_index_start = a
                widest_index_end = b
        best = widest_index_start
        for k in range(widest_index_start, widest_index_end + 1):
            if k == len(ranges):
                break
            if ranges[k] > ranges[best]:
                best = k
        widest_index = (best + (widest_index_start + widest_index_end) // 2) // 2
        self.theta = widest_index * msg.angle_increment + msg.angle_min
        move_msg = AckermannDriveStamped()
        move_msg.drive.speed = 0.8 + 2.2 * math.exp(-2 * abs(self.theta))
        move_msg.drive.steering_angle = self.theta * 0.1
        self.move.publish(move_msg)

def main(args=None):
    rclpy.init(args=args)
    de_node = DisparityExtender()
    rclpy.spin(de_node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
