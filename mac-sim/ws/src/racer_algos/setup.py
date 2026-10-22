from pathlib import Path
from setuptools import setup

package_name = 'racer_algos'

# Every racer_algos/<name>.py that doesn't start with "_" becomes `ros2 run racer_algos <name>`.
# So adding an algorithm is just: drop in a file with a main(), then `rr build`.
modules = sorted(p.stem for p in (Path(__file__).parent / package_name).glob('*.py')
                 if not p.stem.startswith('_'))

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', [str(p) for p in Path('config').glob('*.yaml')]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={'console_scripts': [f'{m} = {package_name}.{m}:main' for m in modules]},
)
