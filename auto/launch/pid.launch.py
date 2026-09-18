from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='auto',
            executable='dist_finder_node'
        ),
        Node(
            package='auto',
            executable='pid_node'
        ),
        Node(
            package='auto',
            executable='aeb_node'
        ),
        Node(
            package='auto',
            executable='drive_node'
        )
    ])
