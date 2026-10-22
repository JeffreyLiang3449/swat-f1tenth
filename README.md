# Swat Robotics F1TENTH GitHub Repository


Welcome to the GitHub repository for Swarthmore College's F1TENTH team! Below are instructions for using this repo. First, [download ROS 2 Foxy](https://docs.ros.org/en/foxy/Installation.html)
and make sure you have the [f1tenth_gym repository](https://github.com/f1tenth/f1tenth_gym_ros) installed on your computer (switch this for the [f1tenth_system repository](https://github.com/f1tenth/f1tenth_system)
if you are iterating with the F1TENTH vehicle).

Once you have that done, follow the instructions below.

2. In a bash terminal, navigate to your f1tenth workspace's src folder.
3. Clone the repo
4. Build the workspace with ```colcon build```
5. Run ```source install/setup.bash```
6. You should now be able to use our algorithms!

## ROS 2 Package Structure

Each main folder is a ROS 2 package. Any folder with the suffix _msgs is an ament cmake package with custom message types. The main folder to be used for competition algorithms is auto, and all algorithm files are in auto/auto. In the launch directory, auto.launch.py launches the best complete algorithm we have so far. Any other launch files should be marked \<algorithm_name\>.launch.py.
