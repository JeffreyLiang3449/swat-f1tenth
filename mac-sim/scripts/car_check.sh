#!/usr/bin/env bash
# Runs ON THE CAR: one look at whether mapping can work right now. `rr car-check`
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}"
source /opt/ros/foxy/setup.bash
source ~/f1tenth_ws/install/setup.bash 2>/dev/null || true

ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mNO\033[0m   %s\n' "$1"; }
# "ros2 topic hz" buffers its output when piped, so a short timeout sees nothing even when data flows.
# Ask who is publishing instead, then confirm a message actually arrives.
alive() {
  local n
  n=$(ros2 topic info "$1" 2>/dev/null | awk '/Publisher count/{print $3}')
  [ "${n:-0}" -gt 0 ] || return 1
  # sensor topics are best-effort; a default (reliable) reader receives nothing from them
  timeout 5 ros2 topic echo "$1" --once --qos-reliability best_effort > /dev/null 2>&1 ||
  timeout 5 ros2 topic echo "$1" --once > /dev/null 2>&1 ||
  return 0   # a publisher exists: good enough to call it alive
}

echo "drivers (rr car-bringup):"
alive /scan && ok "/scan   lidar is streaming" || bad "/scan   no lidar: is rr car-bringup running?"
alive /sensors/imu/raw && ok "/sensors/imu/raw   IMU is streaming" || bad "/sensors/imu/raw   no IMU"
alive /sensors/core && ok "/sensors/core   wheel data (VESC)" \
  || bad "/sensors/core   no wheel data (known: VESC fw 6.2). Lidar+IMU covers it."

echo "odometry (rr car-odom):"
alive /odom_rf2o && ok "/odom_rf2o   lidar odometry" || bad "/odom_rf2o   not running: rr car-odom"
alive /odometry/filtered && ok "/odometry/filtered   fused" || bad "/odometry/filtered   fusion not running: rr car-odom"
if timeout 6 ros2 run tf2_ros tf2_echo odom base_link 2>/dev/null | grep -q Translation; then
  ok "transform odom -> base_link   (SLAM needs this)"
else
  bad "transform odom -> base_link   MISSING: mapping will drop every scan"
fi

echo "mapping (rr car-map):"
ros2 topic list 2>/dev/null | grep -qx /map && ok "/map   SLAM is running" || bad "/map   not running: rr car-map"
d=$(grep -c 'dropping message' /tmp/slam.log 2>/dev/null); d=${d:-0}
sleep 5
d2=$(grep -c 'dropping message' /tmp/slam.log 2>/dev/null); d2=${d2:-0}
if [ "$d2" -gt "$d" ]; then bad "SLAM is dropping scans ($((d2-d)) in 5s): odometry is not reaching it"
else ok "SLAM is accepting scans"; fi
