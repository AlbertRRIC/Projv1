import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PointStamped
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class DirectPickPlaceNode(Node):

    def __init__(self):
        super().__init__('direct_pick_place_node')

        self.busy = False
        self.done_once = False

        self.sub = self.create_subscription(
            PointStamped,
            '/target_base',
            self.target_callback,
            10
        )

        self.action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/xarm7_traj_controller/follow_joint_trajectory'
        )

        self.get_logger().info("Waiting for trajectory action server...")
        self.action_client.wait_for_server()
        self.get_logger().info("Direct object-aware pick/place node started")

    def target_callback(self, msg):

        if self.busy or self.done_once:
            return

        x = msg.point.x
        y = msg.point.y
        z = msg.point.z

        if x < 0.15 or x > 0.65:
            self.get_logger().warn(f"Rejected X out of range: {x:.3f}")
            return

        if y < -0.35 or y > 0.35:
            self.get_logger().warn(f"Rejected Y out of range: {y:.3f}")
            return

        if z < 0.00 or z > 0.45:
            self.get_logger().warn(f"Rejected Z out of range: {z:.3f}")
            return

        self.busy = True
        self.done_once = True

        self.get_logger().info(
            f"Accepted target: X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        self.pick_place_sequence(x, y, z)

    def send_joint_goal(self, positions, duration=3):
        goal_msg = FollowJointTrajectory.Goal()

        goal_msg.trajectory.joint_names = [
          'joint1', 'joint2', 'joint3', 'joint4',
          'joint5', 'joint6', 'joint7'
        ]

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = duration

        goal_msg.trajectory.points.append(point)

        # Allow small tolerance in timing
        goal_msg.goal_time_tolerance.sec = 2

        self.get_logger().info(f"Sending joint goal: {positions}")

        future = self.action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)

        if not future.done():
            self.get_logger().warn("Goal send timed out")
            return False

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected")
            return False

        self.get_logger().info("Goal accepted, waiting for result...")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=duration + 5.0)

        if not result_future.done():
            self.get_logger().warn("Goal result timeout, continuing anyway for testing")
            time.sleep(0.5)
            return True

        result = result_future.result().result

        if result.error_code == 0:
            self.get_logger().info("Goal succeeded")
            time.sleep(0.5)
            return True

        self.get_logger().warn(f"Goal failed: {result.error_string}")
        return False

    def open_gripper(self):
        self.get_logger().info("Open gripper placeholder")
        time.sleep(1.0)

    def close_gripper(self):
        self.get_logger().info("Close gripper placeholder")
        time.sleep(1.0)

    def pick_place_sequence(self, x, y, z):

        self.open_gripper()

        self.get_logger().info(
            f"Using real target coordinates: X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        # Convert object Y into base rotation
        # If movement direction is opposite, change -y to +y
        base_angle = -y * 1.5

        # Clamp safe range
        base_angle = max(min(base_angle, 0.8), -0.8)

        # Convert X distance into arm reach
        shoulder_above = -(0.55 + x * 0.9)
        elbow_above = 0.25 + x * 0.7
        wrist_above = 0.85 + x * 0.5

        # Use Z to adjust lowering
        lower_offset = max(0.10, min(z * 0.5, 0.22))

        shoulder_pick = shoulder_above + lower_offset
        elbow_pick = elbow_above + 0.15
        wrist_pick = wrist_above + 0.10

        self.get_logger().info(
            f"Calculated joints: "
            f"base={base_angle:.2f}, "
            f"shoulder_above={shoulder_above:.2f}, "
            f"elbow_above={elbow_above:.2f}, "
            f"wrist_above={wrist_above:.2f}"
        )

        # 1. Move above object
        if not self.send_joint_goal(
            [
                base_angle,
                shoulder_above,
                elbow_above,
                wrist_above,
                0.0,
                0.7,
                0.0
            ],
            3
        ):
            self.busy = False
            return

        # 2. Lower toward object
        if not self.send_joint_goal(
            [
                base_angle,
                shoulder_pick,
                elbow_pick,
                wrist_pick,
                0.0,
                0.6,
                0.0
            ],
            3
        ):
            self.busy = False
            return

        # 3. Close gripper
        self.close_gripper()

        # 4. Lift object
        if not self.send_joint_goal(
            [
                base_angle,
                -0.70,
                0.20,
                0.70,
                0.0,
                0.8,
                0.0
            ],
            3
        ):
            self.busy = False
            return

        # 5. Move to fixed place location
        if not self.send_joint_goal(
            [
                0.65,
                -0.70,
                0.20,
                0.70,
                0.0,
                0.8,
                0.0
            ],
            3
        ):
            self.busy = False
            return

        # 6. Open gripper
        self.open_gripper()

        # 7. Return home
        if not self.send_joint_goal(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0
            ],
            3
        ):
            self.busy = False
            return

        self.get_logger().info("Object-aware pick/place sequence complete")

        self.busy = False


def main(args=None):

    rclpy.init(args=args)

    node = DirectPickPlaceNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
