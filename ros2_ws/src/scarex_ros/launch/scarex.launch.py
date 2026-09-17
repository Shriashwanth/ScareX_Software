import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Assuming we run this from the project root (where yolo11n.pt and assets/ reside)
    project_root = os.getcwd()

    return LaunchDescription([
        Node(
            package='scarex_ros',
            executable='detection_node',
            name='detection_node',
            output='screen',
            parameters=[
                {'camera_index': 0},
                {'model_path': os.path.join(project_root, 'yolo11n.pt')},
                {'confidence_threshold': 0.5},
                {'display_enabled': True}
            ]
        ),
        Node(
            package='scarex_ros',
            executable='decision_node',
            name='decision_node',
            output='screen',
            parameters=[
                {'required_consecutive_detections': 3},
                {'lost_detection_frames': 5}
            ]
        ),
        Node(
            package='scarex_ros',
            executable='actuator_node',
            name='actuator_node',
            output='screen',
            parameters=[
                {'audio_path': os.path.join(project_root, 'assets', 'audio', 'hawk_eagle.mp3')},
                {'speaker_volume': 1.0}
            ]
        )
    ])
