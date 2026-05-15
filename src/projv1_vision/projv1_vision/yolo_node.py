import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped

from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO


class YoloNode(Node):
    def __init__(self):
        super().__init__('yolo_node')

        self.bridge = CvBridge()
        self.model = YOLO("/home/user/projv1/models/best.pt")

        self.depth_image = None
        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None

        # Store latest transformed coordinate from /target_base
        self.latest_target_base = None

        self.publisher_ = self.create_publisher(
            PointStamped,
            '/detected_target',
            10
        )

        self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.image_callback,
            10
        )

        self.create_subscription(
            Image,
            '/camera/camera/aligned_depth_to_color/image_raw',
            self.depth_callback,
            10
        )

        self.create_subscription(
            CameraInfo,
            '/camera/camera/color/camera_info',
            self.camera_info_callback,
            10
        )

        # Subscribe to transformed robot-base coordinate
        self.create_subscription(
            PointStamped,
            '/target_base',
            self.target_base_callback,
            10
        )

        self.get_logger().info(f"Model classes: {self.model.names}")
        self.get_logger().info("YOLO depth node started")

    def target_base_callback(self, msg):
        self.latest_target_base = msg

    def depth_callback(self, msg):
        self.depth_image = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding="passthrough"
        )

    def camera_info_callback(self, msg):
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def image_callback(self, msg):
        if self.depth_image is None:
            self.get_logger().warn("Waiting for depth image...")
            return

        if self.fx is None:
            self.get_logger().warn("Waiting for camera info...")
            return

        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        results = self.model(frame, conf=0.4)

        annotated = results[0].plot()

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0]

            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            if (
                v < 3 or v >= self.depth_image.shape[0] - 3 or
                u < 3 or u >= self.depth_image.shape[1] - 3
            ):
                continue

            depth_crop = self.depth_image[v-3:v+4, u-3:u+4]
            valid_depths = depth_crop[depth_crop > 0]

            if valid_depths.size == 0:
                self.get_logger().warn("No valid depth, skipping")
                continue

            depth_raw = np.median(valid_depths)

            if depth_raw == 0:
                self.get_logger().warn("Depth is 0, skipping")
                continue

            depth_m = float(depth_raw) / 1000.0

            x = (u - self.cx) * depth_m / self.fx
            y = (v - self.cy) * depth_m / self.fy
            z = depth_m

            # Publish camera-frame coordinate for target_transform_node
            target = PointStamped()
            target.header.stamp = self.get_clock().now().to_msg()
            target.header.frame_id = "camera_color_optical_frame"
            target.point.x = x
            target.point.y = y
            target.point.z = z

            self.publisher_.publish(target)

            self.get_logger().info(
                f"3D camera XYZ: X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
            )

            cv2.circle(annotated, (u, v), 5, (0, 255, 0), -1)

            # Display /target_base coordinate on bounding box if available
            if self.latest_target_base is not None:
                bx = self.latest_target_base.point.x
                by = self.latest_target_base.point.y
                bz = self.latest_target_base.point.z

                label = f"Base X:{bx:.2f} Y:{by:.2f} Z:{bz:.2f}m"
            else:
                label = "Waiting for /target_base"

            cv2.putText(
                annotated,
                label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        cv2.imshow("YOLO 3D Detection", annotated)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = YoloNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
