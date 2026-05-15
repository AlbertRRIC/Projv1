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

        self.pub_base = self.create_publisher(
            PointStamped,
            '/target_base',
            10
        )

        self.pub_table = self.create_publisher(
            PointStamped,
            '/target_table',
            10
        )

        self.get_logger().info("Target transform node started")
        self.get_logger().info("Publishing /target_base and /target_table")

    def transform_point(self, msg, target_frame):
        transform = self.tf_buffer.lookup_transform(
            target_frame,
            msg.header.frame_id,
            rclpy.time.Time()
        )

        transformed = do_transform_point(msg, transform)
        transformed.header.frame_id = target_frame

        return transformed

    def target_callback(self, msg):
        try:
            target_base = self.transform_point(msg, 'link_base')
            self.pub_base.publish(target_base)

            self.get_logger().info(
                f"Target in link_base: "
                f"X={target_base.point.x:.3f}, "
                f"Y={target_base.point.y:.3f}, "
                f"Z={target_base.point.z:.3f}"
            )

        except Exception as e:
            self.get_logger().warn(f"TF to link_base failed: {e}")

        try:
            target_table = self.transform_point(msg, 'table_top')
            self.pub_table.publish(target_table)

            self.get_logger().info(
                f"Target in table_top: "
                f"X={target_table.point.x:.3f}, "
                f"Y={target_table.point.y:.3f}, "
                f"Z={target_table.point.z:.3f}"
            )

        except Exception as e:
            self.get_logger().warn(f"TF to table_top failed: {e}")


def main(args=None):
    rclpy.init(args=args)

    node = TargetTransformNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
