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


class MoveItPickPlaceNode(Node):

    def __init__(self):
        super().__init__('moveit_pick_place_node')

        self.busy = False
        self.done_once = False
        self.latest_joint_state = None
        self.saved_target = None

        # Fixed place location in link_base frame
        self.place_x = 0.30
        self.place_y = -0.25
        self.place_z = 0.25

        self.callback_group = ReentrantCallbackGroup()

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

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

        self.create_timer(1.0, self.status_timer)

        self.get_logger().info("Waiting for /compute_ik service...")
        self.ik_client.wait_for_service()

        self.get_logger().info("Waiting for trajectory action server...")
        self.action_client.wait_for_server()

        self.get_logger().info("MoveIt pick/place node started")
        self.get_logger().info("Waiting for /joint_states and /target_base...")

    def joint_state_callback(self, msg):
        self.latest_joint_state = msg

    def status_timer(self):
        if self.latest_joint_state is None:
            self.get_logger().warn("Still waiting for /joint_states...")
            return

        if self.saved_target is not None and not self.busy and not self.done_once:
            x, y, z = self.saved_target
            self.busy = True
            self.done_once = True

            threading.Thread(
                target=self.pick_place_sequence,
                args=(x, y, z),
                daemon=True
            ).start()

    def target_callback(self, msg):
        if self.done_once:
            return

        self.saved_target = (
            msg.point.x,
            msg.point.y,
            msg.point.z
        )

        self.get_logger().info(
            f"Target received: X={msg.point.x:.3f}, "
            f"Y={msg.point.y:.3f}, Z={msg.point.z:.3f}"
        )

    def wait_future(self, future, timeout_sec):
        start_time = time.time()

        while rclpy.ok():
            if future.done():
                return True

            if time.time() - start_time > timeout_sec:
                return False

            time.sleep(0.05)

        return False

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
                    f"Waiting for link_base -> link_eef TF... {i + 1}/20: {e}"
                )
                time.sleep(0.2)

        return None

    def compute_ik(self, x, y, z):
        if self.latest_joint_state is None:
            self.get_logger().warn("No /joint_states available for IK")
            return None

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

        self.get_logger().info(
            f"Calling IK for X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        future = self.ik_client.call_async(req)

        if not self.wait_future(future, 10.0):
            self.get_logger().warn("IK timeout")
            return None

        result = future.result()

        if result.error_code.val != 1:
            self.get_logger().warn(
                f"IK failed with error code: {result.error_code.val}"
            )
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

        # Reduce wrist twisting by keeping joint7 close to current value
        current_joint_map = dict(
            zip(self.latest_joint_state.name, self.latest_joint_state.position)
        )

        if 'joint7' in current_joint_map:
            positions[6] = current_joint_map['joint7']

        self.get_logger().info(f"IK solution: {positions}")
        return positions

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
        goal_msg.goal_time_tolerance.sec = 3

        self.get_logger().info(f"Sending joint goal: {positions}")

        future = self.action_client.send_goal_async(goal_msg)

        if not self.wait_future(future, 5.0):
            self.get_logger().warn("Goal send timeout")
            return False

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected")
            return False

        self.get_logger().info("Goal accepted")

        result_future = goal_handle.get_result_async()

        if not self.wait_future(result_future, duration + 6):
            self.get_logger().warn("Goal result timeout, continuing")
            time.sleep(1.0)
            return True

        result = result_future.result().result

        if result.error_code == 0:
            self.get_logger().info("Motion complete")
            time.sleep(0.5)
            return True

        self.get_logger().warn(f"Goal failed: {result.error_string}")
        return False

    def move_to_pose(self, x, y, z):
        joints = self.compute_ik(x, y, z)

        if joints is None:
            return False

        self.get_logger().info(
            f"Moving to pose X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        return self.send_joint_goal(joints, duration=4)

    def open_gripper(self):
        self.get_logger().info("Opening gripper placeholder")
        time.sleep(1.0)

    def close_gripper(self):
        self.get_logger().info("Closing gripper placeholder")
        time.sleep(1.0)

    def pick_place_sequence(self, x, y, z):
        self.get_logger().info(
            f"Starting pick/place at X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        )

        above_z = z + 0.12
        pick_z = z + 0.03
        lift_z = z + 0.20

        self.open_gripper()

        # 1. Move above target
        if not self.move_to_pose(x, y, above_z):
            self.busy = False
            return

        # 2. Lower near target
        if not self.move_to_pose(x, y, pick_z):
            self.busy = False
            return

        # 3. Placeholder close gripper
        self.close_gripper()

        # 4. Lift
        if not self.move_to_pose(x, y, lift_z):
            self.busy = False
            return

        # 5. Move to fixed place location
        if not self.move_to_pose(self.place_x, self.place_y, self.place_z + 0.15):
            self.busy = False
            return

        # 6. Placeholder open gripper
        self.open_gripper()

        self.get_logger().info("Pick/place motion complete")
        self.busy = False


def main(args=None):
    rclpy.init(args=args)

    node = MoveItPickPlaceNode()

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)

    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
