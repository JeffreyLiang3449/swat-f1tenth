import rclpy
from rclpy.node import Node
import math

from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped

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
        self.move = self.create_publisher(AckermannDriveStamped, '/disp_drive', 10)
        self.get_logger().info('Disparity extender node initialized')

    def laser_callback(self, msg: LaserScan):
        read_ranges = list(msg.ranges)
        write_ranges = list(msg.ranges)
        read_ranges = read_ranges[::-1]
        write_ranges = write_ranges[::-1]
        print(read_ranges[:20])
        
        for i in range(len(read_ranges)):
            if not math.isfinite(read_ranges[i]):
                read_ranges[i] = msg.range_max
            if read_ranges[i] <= 1.25:
                read_ranges[i] = 0
                write_ranges[i] = 0
        
        num_rays = 10
        for j in range(1, len(read_ranges)):
            if abs(read_ranges[j] - read_ranges[j-1]) > 2.0:
                if read_ranges[j] < read_ranges[j-1]:
                    num_rays = math.ceil(math.asin(min(1.0, 0.205 / max(read_ranges[j], 1e-6))) / msg.angle_increment)
                    for k in range(j-1, max([-1, j-num_rays]), -1):
                        write_ranges[k] = 0
                else:
                    num_rays = math.ceil(math.asin(min(1.0, 0.205 / max(read_ranges[j], 1e-6))) / msg.angle_increment)
                    for k in range(j, min([len(read_ranges), j+num_rays])):
                        write_ranges[k] = 0
        ranges = write_ranges
        
        was_in_gap = False
        gap_start = -1
        gap_indices = []
        for m in range(180, 901):
            if ranges[m] == 0:
                if was_in_gap:
                    was_in_gap = False
                    gap_indices.append((gap_start, m - 1))
                continue
            if not was_in_gap:
                gap_start = m
                was_in_gap = True
        if was_in_gap:
            gap_indices.append((gap_start, 900))
        gap_indices = [(c, d) for c, d in gap_indices if d - c > num_rays]
        print(gap_indices)
        if len(gap_indices) == 0:
            stop_msg = AckermannDriveStamped()
            stop_msg.drive.steering_angle = 0.0
            stop_msg.drive.speed = 0.0
            self.move.publish(stop_msg)
            return
        
        gap_length_averages = [(sum(ranges[a:b]) / (b - a)) for a, b in gap_indices]
        max_dist_rep_indices = [index for index, value in enumerate(gap_length_averages) if value == max(gap_length_averages)]
        if len(max_dist_rep_indices) == 1:
            best_gap = gap_length_averages.index(max(gap_length_averages))
        else:
            far_gap_widths = [b - a for a, b in max_dist_rep_indices]
            best_gap = max_dist_rep_indices[far_gap_widths.index(max(far_gap_widths))]
        best_gap_indices = gap_indices[best_gap]
        print(f'gap start and end angles: ({math.degrees(best_gap_indices[0] * msg.angle_increment + msg.angle_min):.2f}, {math.degrees(best_gap_indices[1] * msg.angle_increment + msg.angle_min):.2f})')
        self.theta = ((best_gap_indices[0] + best_gap_indices[1]) // 2 * msg.angle_increment + msg.angle_min) * 1.2
        print(f'steering angle: {math.degrees(self.theta):.2f}')
        
        drive_msg = AckermannDriveStamped()
        drive_msg.drive.steering_angle = -self.theta
        drive_msg.drive.speed = 0.8 * min(read_ranges[520:560])
        self.move.publish(drive_msg)

def main(args=None):
    rclpy.init(args=args)
    de_node = DisparityExtender()
    rclpy.spin(de_node)
    de_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
