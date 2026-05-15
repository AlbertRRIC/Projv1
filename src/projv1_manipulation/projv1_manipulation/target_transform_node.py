import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PointStamped

import tf2_ros
from tf2_geometry_msgs import do_transform_point


class TargetTransformNode(Node):
    def __init__(self):
        super().__init__('target_transform_node')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.sub = self.create_subscription(
            PointStamped,
            '/detected_target',
            self.target_callback,
            10
        )

        self.pub = self.create_publisher(
            PointStamped,
            '/target_base',
            10
        )

        self.get_logger().info("Target transform node started")

    def target_callback(self, msg):
        try:
            transform = self.tf_buffer.lookup_transform(
                'link_base',
                msg.header.frame_id,
                
                rclpy.time.Time()
            )

            target_base = do_transform_point(msg, transform)
            target_base.header.frame_id = 'link_base'

            self.pub.publish(target_base)

            self.get_logger().info(
                f"Target in link_base: "
                f"X={target_base.point.x:.3f}, "
                f"Y={target_base.point.y:.3f}, "
                f"Z={target_base.point.z:.3f}"
            )

        except Exception as e:
            self.get_logger().warn(f"TF transform failed: {e}")


def main(args=None):
    rclpy.init(args=args)

    node = TargetTransformNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
