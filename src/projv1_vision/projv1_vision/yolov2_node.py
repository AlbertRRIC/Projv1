import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped
from std_msgs.msg import String

from cv_bridge import CvBridge

import cv2
import numpy as np

from ultralytics import YOLO


class YoloNode(Node):

    def __init__(self):
        super().__init__('yolo_node')

        self.bridge = CvBridge()

        # Custom cup model
        self.model = YOLO(
            "/home/user/projv1/models/best.pt"
        )

        # Person detection model
        self.person_model = YOLO(
            "yolov8n.pt"
        )

        self.depth_image = None

        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None

        self.latest_target_base = None

        self.selected_class = None

        # Publisher
        self.publisher_ = self.create_publisher(
            PointStamped,
            '/detected_target',
            10
        )

        # RGB image subscriber
        self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.image_callback,
            10
        )

        # Depth image subscriber
        self.create_subscription(
            Image,
            '/camera/camera/aligned_depth_to_color/image_raw',
            self.depth_callback,
            10
        )

        # Camera info subscriber
        self.create_subscription(
            CameraInfo,
            '/camera/camera/color/camera_info',
            self.camera_info_callback,
            10
        )

        # Robot base coordinate subscriber
        self.create_subscription(
            PointStamped,
            '/target_base',
            self.target_base_callback,
            10
        )

        # Selected class subscriber
        self.create_subscription(
            String,
            '/selected_class',
            self.selected_class_callback,
            10
        )

        self.get_logger().info(
            f"Model classes: {self.model.names}"
        )

        self.get_logger().info(
            "YOLO + FULL BODY CENSOR Node Started"
        )

    def target_base_callback(self, msg):

        self.latest_target_base = msg

    def selected_class_callback(self, msg):

        class_name = msg.data.strip()

        if class_name in ["Browncup", "Whitecup"]:

            self.selected_class = class_name

            self.get_logger().info(
                f"Selected class updated: "
                f"{self.selected_class}"
            )

        else:

            self.get_logger().warn(
                f"Invalid class selected: "
                f"{class_name}"
            )

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

    def censor_people(self, image):

        # Detect persons using COCO model
        results = self.person_model(
            image,
            conf=0.4,
            classes=[0]   # class 0 = person
        )

        for box in results[0].boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # Safety clamp
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(image.shape[1], x2)
            y2 = min(image.shape[0], y2)

            # FULL opaque black box
            cv2.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                (0, 0, 0),
                -1
            )

        return image

    def image_callback(self, msg):

        if self.depth_image is None:

            self.get_logger().warn(
                "Waiting for depth image..."
            )

            return

        if self.fx is None:

            self.get_logger().warn(
                "Waiting for camera info..."
            )

            return

        if self.selected_class is None:

            self.get_logger().warn(
                "Waiting for selected class "
                "from /selected_class..."
            )

            return

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            "bgr8"
        )

        # Run cup YOLO
        results = self.model(
            frame,
            conf=0.4
        )

        # Create display image
        annotated = frame.copy()

        # FULL BODY censor
        annotated = self.censor_people(
            annotated
        )

        # Cup detections
        for box in results[0].boxes:

            detected_class_id = int(box.cls[0])

            detected_class_name = (
                self.model.names[detected_class_id]
            )

            # FILTER selected cup
            if detected_class_name != self.selected_class:
                continue

            # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]

            cv2.rectangle(
                annotated,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (0, 255, 0),
                2
            )

            # Center point
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            # Bounds check
            if (
                v < 3 or
                v >= self.depth_image.shape[0] - 3 or
                u < 3 or
                u >= self.depth_image.shape[1] - 3
            ):
                continue

            # Get nearby depth
            depth_crop = self.depth_image[
                v-3:v+4,
                u-3:u+4
            ]

            valid_depths = (
                depth_crop[depth_crop > 0]
            )

            if valid_depths.size == 0:

                self.get_logger().warn(
                    "No valid depth"
                )

                continue

            depth_raw = np.median(valid_depths)

            if depth_raw == 0:

                self.get_logger().warn(
                    "Depth is 0"
                )

                continue

            depth_m = float(depth_raw) / 1000.0

            # Camera coordinates
            x = (
                (u - self.cx)
                * depth_m
                / self.fx
            )

            y = (
                (v - self.cy)
                * depth_m
                / self.fy
            )

            z = depth_m

            # Publish target point
            target = PointStamped()

            target.header.stamp = (
                self.get_clock().now().to_msg()
            )

            target.header.frame_id = (
                "camera_color_optical_frame"
            )

            target.point.x = x
            target.point.y = y
            target.point.z = z

            self.publisher_.publish(target)

            self.get_logger().info(
                f"{self.selected_class} -> "
                f"X={x:.3f}, "
                f"Y={y:.3f}, "
                f"Z={z:.3f}"
            )

            # Draw center point
            cv2.circle(
                annotated,
                (u, v),
                5,
                (0, 255, 0),
                -1
            )

            # Robot base coordinate
            if self.latest_target_base is not None:

                bx = self.latest_target_base.point.x
                by = self.latest_target_base.point.y
                bz = self.latest_target_base.point.z

                label = (
                    f"{self.selected_class} "
                    f"Base "
                    f"X:{bx:.2f} "
                    f"Y:{by:.2f} "
                    f"Z:{bz:.2f}"
                )

            else:

                label = (
                    "Waiting for /target_base"
                )

            cv2.putText(
                annotated,
                label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        # Show image
        cv2.imshow(
            "YOLO 3D Detection",
            annotated
        )

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = YoloNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
