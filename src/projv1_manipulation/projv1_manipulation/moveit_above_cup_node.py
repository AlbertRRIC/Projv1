import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import PointStamped, PoseStamped
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import RobotState

import tf2_ros


class MoveItAboveCupNode(Node):

    def __init__(self):
        super().__init__('moveit_above_cup_node')

        self.busy = False
        self.done_once = False
        self.latest_joint_state = None

        self.callback_group = ReentrantCallbackGroup()

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(
            self.tf_buffer,
            self
        )

        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10,
            callback_group=self.callback_group
        )

        self.create_subscription(
            PointStamped,
            '/target_base',
            self.target_callback,
            10,
            callback_group=self.callback_group
        )

        self.ik_client = self.create_client(
            GetPositionIK,
            '/compute_ik',
            callback_group=self.callback_group
        )

        self.action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/xarm7_traj_controller/follow_joint_trajectory',
            callback_group=self.callback_group
        )

        self.get_logger().info("Waiting for /compute_ik service...")
        self.ik_client.wait_for_service()

        self.get_logger().info("Waiting for trajectory action server...")
        self.action_client.wait_for_server()

        self.get_logger().info("MoveIt above cup node started")

    def joint_state_callback(self, msg):
        self.latest_joint_state = msg

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

        threading.Thread(
            target=self.process_target,
            args=(x, y, z),
            daemon=True
        ).start()

    def wait_future(self, future, timeout_sec):
        start_time = time.time()

        while rclpy.ok():
            if future.done():
                return True

            if time.time() - start_time > timeout_sec:
                return False

            time.sleep(0.05)

        return False

    def process_target(self, x, y, z):
        self.get_logger().info(
            f"Accepted cup centre: X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        if self.latest_joint_state is None:
            self.get_logger().warn("No /joint_states received yet")
            self.busy = False
            return

        above_z = z + 0.12

        self.get_logger().info(
            f"Moving above cup: X={x:.3f}, Y={y:.3f}, Z={above_z:.3f}"
        )

        success = self.move_to_pose(x, y, above_z)

        if success:
            self.get_logger().info("Successfully moved above cup")
        else:
            self.get_logger().warn("Failed to move above cup")

        self.busy = False

    def get_current_eef_orientation(self):
        for i in range(20):
            try:
                transform = self.tf_buffer.lookup_transform(
                    'link_base',
                    'link_eef',
                    rclpy.time.Time()
                )

                return transform.transform.rotation

            except Exception as e:
                self.get_logger().warn(
                    f"Waiting for link_base -> link_eef TF... attempt {i + 1}/20: {e}"
                )
                time.sleep(0.2)

        return None

    def compute_ik(self, x, y, z):
        orientation = self.get_current_eef_orientation()

        if orientation is None:
            self.get_logger().warn("Could not get end-effector orientation")
            return None

        pose = PoseStamped()
        pose.header.frame_id = 'link_base'
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation = orientation

        req = GetPositionIK.Request()
        req.ik_request.group_name = 'xarm7'
        req.ik_request.ik_link_name = 'link_eef'
        req.ik_request.pose_stamped = pose
        req.ik_request.timeout.sec = 5
        req.ik_request.avoid_collisions = False

        robot_state = RobotState()
        robot_state.joint_state = self.latest_joint_state
        req.ik_request.robot_state = robot_state

        self.get_logger().info("Calling /compute_ik...")

        future = self.ik_client.call_async(req)

        if not self.wait_future(future, timeout_sec=10.0):
            self.get_logger().warn("IK service timeout")
            return None

        result = future.result()

        if result.error_code.val != 1:
            self.get_logger().warn(f"IK failed with error code: {result.error_code.val}")
            return None

        joint_state = result.solution.joint_state
        joint_map = dict(zip(joint_state.name, joint_state.position))

        joint_names = [
            'joint1',
            'joint2',
            'joint3',
            'joint4',
            'joint5',
            'joint6',
            'joint7'
        ]

        try:
            positions = [joint_map[name] for name in joint_names]
        except KeyError as e:
            self.get_logger().warn(f"IK solution missing joint: {e}")
            return None

        self.get_logger().info(f"IK joint solution: {positions}")
        return positions

    def move_to_pose(self, x, y, z):
        joint_positions = self.compute_ik(x, y, z)

        if joint_positions is None:
            return False

        return self.send_joint_goal(joint_positions, duration=4)

    def send_joint_goal(self, positions, duration=4):
        goal_msg = FollowJointTrajectory.Goal()

        goal_msg.trajectory.joint_names = [
            'joint1',
            'joint2',
            'joint3',
            'joint4',
            'joint5',
            'joint6',
            'joint7'
        ]

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = duration

        goal_msg.trajectory.points.append(point)
        goal_msg.goal_time_tolerance.sec = 2

        self.get_logger().info(f"Sending joint goal from IK: {positions}")

        future = self.action_client.send_goal_async(goal_msg)

        if not self.wait_future(future, timeout_sec=5.0):
            self.get_logger().warn("Goal send timed out")
            return False

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected")
            return False

        self.get_logger().info("Goal accepted, waiting for result...")

        result_future = goal_handle.get_result_async()

        if not self.wait_future(result_future, timeout_sec=duration + 6.0):
            self.get_logger().warn("Goal result timeout")
            return False

        result = result_future.result().result

        if result.error_code == 0:
            self.get_logger().info("Goal succeeded")
            time.sleep(0.5)
            return True

        self.get_logger().warn(f"Goal failed: {result.error_string}")
        return False


def main(args=None):
    rclpy.init(args=args)

    node = MoveItAboveCupNode()

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)

    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
