from setuptools import setup
import os
from glob import glob

package_name = 'auto'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='swat-roboracer-2026',
    maintainer_email='swat-roboracer-2026@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gap_follow = auto.follow_the_gap:main',
            'gap_follow_v2 = auto.follow_the_gap_v2:main',
            'waypoint_logger = auto.waypoint_logger:main',
            'pure_pursuit_node = auto.pure_pursuit_node:main',
            'aeb_node = auto.aeb_node:main',
            'dist_finder_node = auto.dist_finder_node:main',
            'pid_node = auto.pid_node:main',
            'disparity_extender_node = auto.disparity_extender_node:main',
            'drive_node = auto.drive:main'
        ],
    },
)
