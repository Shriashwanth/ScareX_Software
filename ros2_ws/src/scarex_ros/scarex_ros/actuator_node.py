import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import os
import pygame

class ActuatorNode(Node):
    def __init__(self):
        super().__init__('actuator_node')
        
        self.declare_parameter('audio_path', 'assets/audio/hawk_eagle.mp3')
        self.declare_parameter('speaker_volume', 1.0)
        
        self.audio_path = self.get_parameter('audio_path').value
        self.speaker_volume = self.get_parameter('speaker_volume').value
        
        # Determine absolute path relative to workspace if necessary
        # Usually ros2 run executes from the workspace root or we can just pass an absolute path via config
        if not os.path.isabs(self.audio_path):
            # Assuming we run from the project root containing assets/
            self.audio_path = os.path.abspath(self.audio_path)
            
        self.initialized = False
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(max(0.0, min(1.0, self.speaker_volume)))
            self.initialized = True
            self.get_logger().info(f"Actuator node started. Audio path: {self.audio_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize pygame mixer: {e}")

        self.subscription = self.create_subscription(
            Bool,
            '/deterrence_command',
            self.command_callback,
            10
        )
        self.is_playing = False

    def command_callback(self, msg):
        if not self.initialized:
            return
            
        should_play = msg.data
        
        if should_play and not self.is_playing:
            if not os.path.exists(self.audio_path):
                self.get_logger().error(f"Deterrence audio file not found: {self.audio_path}")
                return
                
            try:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(self.audio_path)
                    pygame.mixer.music.play(-1) # Loop indefinitely
                    self.is_playing = True
                    self.get_logger().info("BIRD DETECTED - Sound ON")
            except Exception as e:
                self.get_logger().error(f"Error playing audio: {e}")
                
        elif not should_play and self.is_playing:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.is_playing = False
            self.get_logger().info("BIRD LOST - Sound OFF")

    def destroy_node(self):
        self.get_logger().info("Shutting down actuator node...")
        if self.initialized and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ActuatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
