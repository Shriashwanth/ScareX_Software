from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'scarex_ros'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ashwanth',
    maintainer_email='user@todo.todo',
    description='ScareX Real-Time Bird Detection and Deterrence ROS 2 Package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detection_node = scarex_ros.detection_node:main',
            'decision_node = scarex_ros.decision_node:main',
            'actuator_node = scarex_ros.actuator_node:main',
        ],
    },
)
