#!/usr/bin/env bash
# Runs ON THE CAR: start drivers + odometry + SLAM in a tmux session that survives SSH drops.
#   car_session.sh start|stop|status
# Started from the Mac with `rr car-start` / `rr car-stop-all` / `rr car-check`.
S=rr
set -o pipefail
# CYCLONEDDS_URI: keep ROS traffic on wlan0. Left alone, it picks eth0, the lidar's private wired
# link, where discovery is unreliable and nodes silently fail to see each other.
R="export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp; source /opt/ros/foxy/setup.bash; source ~/f1tenth_ws/install/setup.bash 2>/dev/null"

case "${1:-start}" in
start)
  tmux kill-session -t $S 2>/dev/null
  # pkill -x matches only the first 15 characters of a name, so it silently missed things like
  # static_transform_publisher and left duplicates running. Match the full command line instead.
  for pat in '[v]esc_driver_node' '[u]rg_node_driver' '[a]ckermann_mux' '[j]oy_node' '[j]oy_teleop' \
             '[a]sync_slam_toolbox_node' '[a]ckermann_to_vesc_node' '[v]esc_to_odom_node' \
             '[s]tatic_transform_publisher' '[e]kf_node' '[r]f2o_laser_odometry_node' '[s]can_relay.py' \
             '[r]os2 launch f1tenth_stack' '[r]os2 launch slam_toolbox'; do
    pkill -f "$pat"
  done
  sleep 2

  tmux new-session -d -s $S -n drivers "$R; ros2 launch f1tenth_stack bringup_launch.py 2>&1 | tee /tmp/bu.log"
  sleep 8
  tmux new-window -t $S -n odom "$R; bash /tmp/car_odom.sh /tmp/ekf.yaml 2>&1 | tee /tmp/odom.log"
  sleep 6
  cfg=~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config/f1tenth_online_async.yaml
  # run the node, not their launch file: the launch file ignored the config and fell back to its own
  # defaults (base_footprint), which is why SLAM dropped every scan
  tmux new-window -t $S -n slam "$R; ros2 run slam_toolbox async_slam_toolbox_node --ros-args --params-file $cfg -p base_frame:=base_link -p transform_timeout:=0.5 -p tf_buffer_duration:=30.0 2>&1 | tee /tmp/slam.log"
  sleep 10
  echo "session '$S' running: $(tmux list-windows -t $S | wc -l) windows"
  ;;
stop)
  tmux kill-session -t $S 2>/dev/null
  # pkill -x matches only the first 15 characters of a name, so it silently missed things like
  # static_transform_publisher and left duplicates running. Match the full command line instead.
  for pat in '[v]esc_driver_node' '[u]rg_node_driver' '[a]ckermann_mux' '[j]oy_node' '[j]oy_teleop' \
             '[a]sync_slam_toolbox_node' '[a]ckermann_to_vesc_node' '[v]esc_to_odom_node' \
             '[s]tatic_transform_publisher' '[e]kf_node' '[r]f2o_laser_odometry_node' '[s]can_relay.py' \
             '[r]os2 launch f1tenth_stack' '[r]os2 launch slam_toolbox'; do
    pkill -f "$pat"
  done
  sleep 1; echo "stopped"
  ;;
status)
  tmux has-session -t $S 2>/dev/null && tmux list-windows -t $S || echo "no session"
  ;;
esac
