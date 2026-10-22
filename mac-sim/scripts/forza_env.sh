# Sourced inside the forzaeth VM by `rr forza ...` (mirrors their .bashrc_forzaeth).
export USERNAME=$USER ROS_DISTRO=humble RACECAR_VERSION=SIM RMW_IMPLEMENTATION=rmw_zenoh_cpp
export DISPLAY=:1 PATH="$HOME/.local/bin:$PATH"
source /opt/ros/humble/setup.bash
[ -f ~/ws/install/setup.bash ] && source ~/ws/install/setup.bash
