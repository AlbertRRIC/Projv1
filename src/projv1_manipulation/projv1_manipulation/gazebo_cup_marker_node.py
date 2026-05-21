import math
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PointStamped
from gazebo_msgs.srv import SpawnEntity, DeleteEntity


class GazeboCupMarkerNode(Node):

    def __init__(self):
        super().__init__('gazebo_cup_marker_node')

        self.latest_target = None
        self.last_target_time = None

        self.marker_name = "detected_cup_marker"

        self.spawned = False
        self.spawn_in_progress = False
        self.delete_in_progress = False

        self.spawned_position = None

        self.pending_respawn = False
        self.pending_target = None

        self.target_timeout_sec = 5.0
        self.respawn_distance = 0.10

        self.create_subscription(
            PointStamped,
            '/target_base',
            self.target_callback,
            10
        )

        self.spawn_client = self.create_client(
            SpawnEntity,
            '/spawn_entity'
        )

        self.delete_client = self.create_client(
            DeleteEntity,
            '/delete_entity'
        )

        self.get_logger().info("Waiting for /spawn_entity...")
        self.spawn_client.wait_for_service()

        self.get_logger().info("Waiting for /delete_entity...")
        self.delete_client.wait_for_service()

        self.create_timer(1.0, self.timer_callback)

        self.get_logger().info("Gazebo cup marker node started")

    def target_callback(self, msg):
        self.latest_target = msg
        self.last_target_time = time.monotonic()

    def timer_callback(self):
        if self.latest_target is None or self.last_target_time is None:
            return

        age = time.monotonic() - self.last_target_time

        if age > self.target_timeout_sec:
            if self.spawned and not self.delete_in_progress:
                self.get_logger().warn(
                    f"No /target_base for {age:.1f}s. Deleting marker."
                )
                self.pending_respawn = False
                self.pending_target = None
                self.delete_marker()
            return

        x = self.latest_target.point.x
        y = self.latest_target.point.y
        z = self.latest_target.point.z

        if not self.valid_target(x, y, z):
            if self.spawned and not self.delete_in_progress:
                self.pending_respawn = False
                self.pending_target = None
                self.delete_marker()
            return

        current_target = (x, y, z)

        if not self.spawned and not self.spawn_in_progress:
            self.spawn_marker(x, y, z)
            return

        if self.spawned and self.spawned_position is not None:
            dist = self.distance(self.spawned_position, current_target)

            if dist > self.respawn_distance:
                if not self.delete_in_progress and not self.spawn_in_progress:
                    self.get_logger().info(
                        f"Cup moved {dist:.3f} m. Updating marker."
                    )

                    self.pending_respawn = True
                    self.pending_target = current_target

                    self.delete_marker()

    def valid_target(self, x, y, z):
        if x < 0.10 or x > 0.80:
            self.get_logger().warn(f"Rejected X: {x:.3f}")
            return False

        if y < -0.40 or y > 0.40:
            self.get_logger().warn(f"Rejected Y: {y:.3f}")
            return False

        if z < 0.02 or z > 0.60:
            self.get_logger().warn(f"Rejected Z: {z:.3f}")
            return False

        return True

    def distance(self, p1, p2):
        return math.sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2 +
            (p1[2] - p2[2]) ** 2
        )

    def spawn_marker(self, x, y, z):
        self.spawn_in_progress = True

        cup_sdf = """
        <sdf version="1.6">
          <model name="detected_cup_marker">
            <static>true</static>
            <link name="link">
              <visual name="visual">
                <geometry>
                  <cylinder>
                    <radius>0.04</radius>
                    <length>0.10</length>
                  </cylinder>
                </geometry>
                <material>
                  <ambient>0 1 0 1</ambient>
                  <diffuse>0 1 0 1</diffuse>
                </material>
              </visual>
            </link>
          </model>
        </sdf>
        """

        req = SpawnEntity.Request()
        req.name = self.marker_name
        req.xml = cup_sdf
        req.robot_namespace = ""
        req.reference_frame = "world"

        req.initial_pose.position.x = x
        req.initial_pose.position.y = y
        req.initial_pose.position.z = z
        req.initial_pose.orientation.w = 1.0

        self.get_logger().info(
            f"Spawning marker at X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        future = self.spawn_client.call_async(req)
        future.add_done_callback(
            lambda future: self.spawn_done_callback(future, x, y, z)
        )

    def spawn_done_callback(self, future, x, y, z):
        self.spawn_in_progress = False

        try:
            result = future.result()

            if result.success:
                self.spawned = True
                self.spawned_position = (x, y, z)
                self.get_logger().info("Cup marker spawned successfully")
            else:
                msg = result.status_message.lower()

                if "already" in msg:
                    self.spawned = True
                    self.spawned_position = (x, y, z)
                    self.get_logger().warn(
                        "Marker already exists. Treating as spawned."
                    )
                else:
                    self.spawned = False
                    self.spawned_position = None
                    self.get_logger().warn(
                        f"Spawn failed: {result.status_message}"
                    )

        except Exception as e:
            self.spawned = False
            self.spawned_position = None
            self.get_logger().warn(f"Spawn exception: {e}")

    def delete_marker(self):
        self.delete_in_progress = True

        req = DeleteEntity.Request()
        req.name = self.marker_name

        self.get_logger().info("Deleting cup marker")

        future = self.delete_client.call_async(req)
        future.add_done_callback(self.delete_done_callback)

    def delete_done_callback(self, future):
        self.delete_in_progress = False
        self.spawned = False
        self.spawned_position = None

        try:
            result = future.result()
            self.get_logger().info(
                f"Delete result: {result.status_message}"
            )

        except Exception as e:
            self.get_logger().warn(f"Delete exception: {e}")

        if self.pending_respawn and self.pending_target is not None:
            x, y, z = self.pending_target

            self.pending_respawn = False
            self.pending_target = None

            self.get_logger().info("Respawning marker at updated cup position")
            self.spawn_marker(x, y, z)


def main(args=None):
    rclpy.init(args=args)

    node = GazeboCupMarkerNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
