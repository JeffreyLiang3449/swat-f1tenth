# Swarthmore Roboracer (F1TENTH)

Team ROS 2 (Foxy) code. `auto/` holds all driving algorithms; `pid_msgs/` is
the message used by wall following (dist_finder -> pid).

## Set up the car (Jetson)
    mkdir -p ~/swat_ws/src && cd ~/swat_ws/src
    git clone https://github.com/ORG/swat-f1tenth.git
    vcs import < swat-f1tenth/car.repos
    git -C f1tenth_system submodule update --init --recursive
    cd ~/swat_ws
    rosdep install --from-paths src --ignore-src -y
    colcon build --symlink-install
    source install/setup.bash

Our car-specific changes (VESC calibration, joystick/lidar config, bringup
launch, odometry fix in vesc_to_odom) live on the `swat-foxy` branch of our
forks of f1tenth_system and vesc.

## Set up a laptop (simulator)
    mkdir -p ~/swat_ws/src && cd ~/swat_ws/src
    git clone https://github.com/ORG/swat-f1tenth.git
    vcs import < swat-f1tenth/sim.repos
    cd ~/swat_ws
    rosdep install --from-paths src --ignore-src -y
    colcon build --symlink-install

## Daily workflow
    cd ~/swat_ws/src/swat-f1tenth && git pull
    cd ~/swat_ws && colcon build --symlink-install

## Rules
- Never push to main directly; open a pull request.
- Don't edit code on the Jetson; develop on a laptop, then pull.
