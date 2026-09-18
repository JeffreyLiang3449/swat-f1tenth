from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='auto',
            executable='disparity_extender_node'
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
