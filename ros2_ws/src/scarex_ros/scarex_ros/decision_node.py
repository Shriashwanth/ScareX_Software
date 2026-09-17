import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import json

class DecisionNode(Node):
    def __init__(self):
        super().__init__('decision_node')
        
        self.declare_parameter('required_consecutive_detections', 3)
        self.declare_parameter('lost_detection_frames', 5)
        
        self.req_consecutive = self.get_parameter('required_consecutive_detections').value
        self.max_lost = self.get_parameter('lost_detection_frames').value
        
        self.consecutive_detections = 0
        self.lost_frames = 0
        self.deterrence_active = False

        self.subscription = self.create_subscription(
            String,
            '/bird_detection',
            self.detection_callback,
            10
        )
        self.publisher_ = self.create_publisher(Bool, '/deterrence_command', 10)
        self.get_logger().info("Decision node started. Enforcing NO BIRD = NO SOUND.")

    def detection_callback(self, msg):
        try:
            data = json.loads(msg.data)
            status = data.get("status", "")
        except json.JSONDecodeError:
            self.get_logger().error("Invalid JSON received on /bird_detection")
            return

        if status == "Bird detected":
            self.consecutive_detections += 1
            self.lost_frames = 0
            
            if self.consecutive_detections >= self.req_consecutive:
                if not self.deterrence_active:
                    self.deterrence_active = True
                    self.get_logger().info(f"Bird confirmed ({data.get('class')}). Activating deterrence.")
                
                # Continuously publish True to keep sound active
                cmd = Bool()
                cmd.data = True
                self.publisher_.publish(cmd)
        else:
            self.consecutive_detections = 0
            
            if self.deterrence_active:
                self.lost_frames += 1
                if self.lost_frames >= self.max_lost:
                    self.get_logger().info("Bird lost. Deactivating deterrence.")
                    self.deterrence_active = False
                    cmd = Bool()
                    cmd.data = False
                    self.publisher_.publish(cmd)
                else:
                    # Keep publishing true during the grace period
                    cmd = Bool()
                    cmd.data = True
                    self.publisher_.publish(cmd)
            else:
                # Continuously publish false
                cmd = Bool()
                cmd.data = False
                self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = DecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
