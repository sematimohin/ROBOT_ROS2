import os
from glob import glob
from setuptools import setup

package_name = 'my_robot_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'),   glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'maps'),   glob('maps/*')),
        (os.path.join('share', package_name, 'rviz'),   glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='you@example.com',
    description='Robot model, map and RViz config',
    license='MIT',
    entry_points={
        'console_scripts': [
        'uwb_anchors = my_robot_pkg.uwb_anchors:main',
        'trajectory_publisher = my_robot_pkg.trajectory_publisher:main',
        'fake_clock = my_robot_pkg.fake_clock:main',
    ],
},
)
