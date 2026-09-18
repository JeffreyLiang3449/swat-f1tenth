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
    maintainer='swatrobotics',
    maintainer_email='swatrobotics@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'aeb_node = auto.aeb_node:main',
            'dist_finder_node = auto.dist_finder_node:main',
            'pid_node = auto.pid_node:main',
            'disparity_extender_node = auto.disparity_extender_node:main',
            'drive_node = auto.drive:main',
        ],
    },
)
