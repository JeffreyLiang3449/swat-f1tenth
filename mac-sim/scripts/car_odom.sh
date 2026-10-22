#!/usr/bin/env bash
# Runs ON THE CAR: lidar odometry + IMU fused into one odometry estimate, with the odom->base_link
# transform that SLAM needs. Started from the Mac with `rr car-odom`. Ctrl-C stops everything.
#
# rf2o alone would do, but the VESC's IMU is working (only its wheel-speed packets are missing), and
# fusing it gives much steadier heading through fast turns, where scan matching alone slips.
set -o pipefail   # no -u: ROS setup.bash trips on it
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}"
source /opt/ros/foxy/setup.bash
source ~/f1tenth_ws/install/setup.bash 2>/dev/null || true
EKF_CFG="${1:?usage: car_odom.sh <path to ekf.yaml>}"

cleanup() { kill $(jobs -p) 2>/dev/null; sleep 1; }
trap cleanup EXIT INT TERM

# The IMU's own frame must exist in the transform tree or the EKF ignores it. The car's bringup only
# publishes base_link -> laser, so add an identity base_link -> imu.
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link imu > /dev/null 2>&1 &

# The lidar publishes best-effort; rf2o only listens for reliable, so bridge the two.
python3 /tmp/scan_relay.py > /tmp/relay.log 2>&1 &
sleep 2

# Lidar odometry. Run the node directly: their launch file ignores arguments passed like this, which
# left it publishing its own base_footprint transform and fighting the EKF.
ros2 run rf2o_laser_odometry rf2o_laser_odometry_node --ros-args \
     -p laser_scan_topic:=/scan_reliable -p odom_topic:=/odom_rf2o -p publish_tf:=false \
     -p base_frame_id:=base_link -p odom_frame_id:=odom -p freq:=20.0 \
     > /tmp/rf2o.log 2>&1 &
sleep 3

# The fusion itself.
ros2 run robot_localization ekf_node --ros-args --params-file "$EKF_CFG" > /tmp/ekf.log 2>&1 &
sleep 3

echo "odometry running:"
echo "  /odom_rf2o          lidar only"
echo "  /odometry/filtered  lidar + IMU, fused  <- what SLAM uses (via the odom->base_link transform)"
echo "logs on the car: /tmp/rf2o.log  /tmp/ekf.log"
echo "leave this running, then start mapping in another tab: rr car-map"
wait
