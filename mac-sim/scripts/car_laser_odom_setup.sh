#!/usr/bin/env bash
# Runs ON THE CAR: install laser odometry (rf2o), so mapping works without the VESC.
# From the Mac:  rr car-odom-setup
#
# Why: this car's VESC (firmware 6.2) publishes no /sensors/core with the driver installed, so there is
# no wheel odometry, no odom->base_link transform, and slam_toolbox drops every scan. rf2o works out the
# car's motion by comparing one lidar scan to the next, and publishes /odom plus that transform.
# Nothing about the VESC or its firmware is touched.
set -euo pipefail
WS=~/f1tenth_ws
SRC="$WS/src/rf2o_laser_odometry"

echo "=== get rf2o"
if [ -d "$SRC/.git" ]; then
  git -C "$SRC" pull --ff-only || true
else
  git clone https://github.com/MAPIRlab/rf2o_laser_odometry.git "$SRC"
  git -C "$SRC" checkout ros2 2>/dev/null || true   # ROS 2 code is on a branch in some clones
fi

echo "=== fusion package (robot_localization) + tmux"
sudo apt-get update -qq && sudo apt-get install -y -qq ros-foxy-robot-localization tmux || \
  echo "NOTE: apt failed; install ros-foxy-robot-localization by hand"

echo "=== make the source work on Foxy"
# rf2o's ROS 2 code targets Humble, where the header is tf2_geometry_msgs.hpp. Foxy ships the same
# thing as tf2_geometry_msgs.h, so point the includes at whichever one this machine actually has.
sudo apt-get install -y -qq ros-foxy-tf2-geometry-msgs >/dev/null 2>&1 || true
if [ ! -f /opt/ros/foxy/include/tf2_geometry_msgs/tf2_geometry_msgs.hpp ] \
   && [ -f /opt/ros/foxy/include/tf2_geometry_msgs/tf2_geometry_msgs.h ]; then
  grep -rl 'tf2_geometry_msgs/tf2_geometry_msgs\.hpp' "$SRC" 2>/dev/null | while read -r f; do
    sed -i 's#tf2_geometry_msgs/tf2_geometry_msgs\.hpp#tf2_geometry_msgs/tf2_geometry_msgs.h#' "$f"
    echo "  patched include in $(basename "$f")"
  done
fi

echo "=== build it"
set +u; source /opt/ros/foxy/setup.bash; set -u
cd "$WS"
rosdep install -i -y --from-paths src/rf2o_laser_odometry --rosdistro foxy 2>/dev/null || true
colcon build --symlink-install --packages-select rf2o_laser_odometry

echo "=== done"
echo "Next, from the Mac:  rr car-odom   (leave it running, then rr car-map as usual)"
echo "It fuses this lidar odometry with the VESC IMU; wheel odometry joins automatically if it ever returns."
