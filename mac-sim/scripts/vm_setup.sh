#!/usr/bin/env bash
# Provision the "roboracer" OrbStack VM (Ubuntu 22.04 arm64):
# minimal ROS 2 Humble + RViz, f1tenth_gym (dev-humble), f1tenth_gym_ros, noVNC for RViz.
# Safe to re-run. Run from the Mac with:  rr setup
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DEBIAN_FRONTEND=noninteractive

echo "==> apt basics"
sudo apt-get update -q
sudo apt-get install -y -q --no-install-recommends \
  curl gnupg lsb-release software-properties-common locales \
  git tmux nano python3-pip python3-dev libeigen3-dev build-essential

sudo locale-gen en_US.UTF-8 >/dev/null

echo "==> ROS 2 Humble apt repo"
if [ ! -f /etc/apt/sources.list.d/ros2.list ]; then
  sudo add-apt-repository -y universe
  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
  sudo apt-get update -q
fi

echo "==> ROS 2 Humble (ros-base + rviz2, not the full desktop)"
sudo apt-get install -y -q --no-install-recommends \
  ros-humble-ros-base ros-humble-rviz2 \
  ros-dev-tools python3-colcon-common-extensions python3-rosdep \
  ros-humble-teleop-twist-keyboard

echo "==> noVNC so RViz shows up in a Mac browser"
sudo apt-get install -y -q --no-install-recommends \
  tigervnc-standalone-server novnc websockify openbox x11-xserver-utils libgl1-mesa-dri

echo "==> f1tenth_gym (dev-humble) into user site-packages, numpy kept <2 for ROS"
printf 'numpy<2\npyqt6==6.7.1; platform_machine == "aarch64"\n' > /tmp/rr-constraints.txt
# Ubuntu's pip 22 can't build f1tenth_gym's uv_build backend, so get a newer pip first.
python3 -m pip install -q --user --upgrade pip
PIP="$HOME/.local/bin/pip3"
"$PIP" install -q --user -c /tmp/rr-constraints.txt transforms3d
"$PIP" install -q --user -c /tmp/rr-constraints.txt -e "$ROOT/f1tenth_gym"

echo "==> rosdep + build workspace"
set +u; source /opt/ros/humble/setup.bash; set -u
[ -f /etc/ros/rosdep/sources.list.d/20-default.list ] || sudo rosdep init
rosdep update -q
cd "$ROOT/ws"
rosdep install -i -y -q --from-paths src --rosdistro humble
colcon build --symlink-install

echo "==> shell setup"
if ! grep -q roboracer-env ~/.bashrc; then
  printf '# roboracer-env\nsource "%s/scripts/env.sh"\ncd "%s/ws"\n' "$ROOT" "$ROOT" >> ~/.bashrc
fi

echo "==> done"
