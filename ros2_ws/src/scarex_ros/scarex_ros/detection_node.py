import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import os
import json
from ultralytics import YOLO

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')
        
        # Declare parameters
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('model_path', 'yolo11n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('display_enabled', True)
        self.declare_parameter('target_fps', 15.0)

        # Get parameters
        self.camera_index = self.get_parameter('camera_index').value
        self.model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value
        self.display_enabled = self.get_parameter('display_enabled').value
        self.target_fps = self.get_parameter('target_fps').value

        self.publisher_ = self.create_publisher(String, '/bird_detection', 10)
        
        # Initialize YOLO
        self.get_logger().info(f"Loading YOLO model from {self.model_path}")
        if not os.path.exists(self.model_path):
            self.get_logger().error(f"Model path {self.model_path} does not exist!")
            self.model = None
        else:
            self.model = YOLO(self.model_path)
            self.get_logger().info("YOLO model loaded.")
            
        # These classes would normally be verified dynamically, but standard fallback is here
        self.target_birds = ["crow", "common myna", "rose ringed parakeet", "peacock", "pigeon", "parrot", "hen", "sparrow", "dove", "koel", "duck", "goose", "turkey", "bird"]

        # Initialize Camera
        self.get_logger().info(f"Opening camera {self.camera_index}")
        if os.name == 'nt':
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
            
        if not self.cap.isOpened():
            self.get_logger().error(f"ERROR: USB camera {self.camera_index} unavailable.")
        else:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Timer for inference loop
        timer_period = 1.0 / self.target_fps
        self.timer = self.create_timer(timer_period, self.timer_callback)

        if self.display_enabled:
            cv2.namedWindow("ScareX - Detection", cv2.WINDOW_NORMAL)

    def timer_callback(self):
        if self.model is None or not self.cap.isOpened():
            msg = String()
            msg.data = "Error: Camera or Model unavailable"
            self.publisher_.publish(msg)
            return

        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error("Failed to capture frame")
            return

        highest_conf = 0.0
        best_bird = "None"

        results = self.model(frame, verbose=False)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = self.model.names[cls]

                if class_name.lower() in self.target_birds and conf >= self.conf_threshold:
                    if conf > highest_conf:
                        highest_conf = conf
                        best_bird = class_name
                    
                    if self.display_enabled:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, max(y1-10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Publish detection
        msg = String()
        if best_bird != "None":
            # The prompt requested exactly "Bird detected" and "No bird detected" or a JSON format.
            # Using JSON allows the decision node to have more data.
            payload = {"status": "Bird detected", "class": best_bird, "confidence": highest_conf}
        else:
            payload = {"status": "No bird detected", "class": "None", "confidence": 0.0}
            
        msg.data = json.dumps(payload)
        self.publisher_.publish(msg)

        if self.display_enabled:
            status_text = "BIRD DETECTED" if best_bird != "None" else "NO BIRD DETECTED"
            color = (0, 0, 255) if best_bird != "None" else (0, 255, 0)
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imshow("ScareX - Detection", frame)
            cv2.waitKey(1)

    def destroy_node(self):
        self.get_logger().info("Shutting down detection node...")
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        if self.display_enabled:
            cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
