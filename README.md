# Projv1


## 1. Introduction

&ensp;&ensp;&ensp;&ensp;This repository contains simulation models, and corresponding motion planning and controlling demos of the xArm series from UFACTORY. The development and test environment is as follows
- Ubuntu 22.04 + ROS Humble

&ensp;&ensp;&ensp;&ensp;Please switch to the corresponding code branch according to different ros2 versions (no corresponding code branch means it has not been tested in this version)
- 
- Humble: [humble](https://github.com/xArm-Developer/xarm_ros2/tree/humble)

## 2. Update History    
- (2026-05-14) Completed YOLO Detection + Intel Realsense D435i Camera Integration
- (2026-05-14) Processing Gazebo + Manipulation Node
- (2026-05-15) Added Selection Node
- (2026-05-16) Linked eef with both Camera + Gripper
- (2026-06-23) Added Hand-eye Calibration
- (2026-07-02) Condensed Selection + YOLO + Target Transform Nodes into 1 (visionv1_node.py)
- (2026-07-02) Made a Service call between visionv1_node & Manupalation_node

## 3. Preparation

- ### 3.1 Install [ROS2](https://docs.ros.org/) 
  - [Humble](https://docs.ros.org/en/ros2_documentation/humble/Installation.html)

- ### 3.2 Install [Moveit2](https://moveit.ros.org/install-moveit2/binary/)  

- ### 3.3 Install [Gazebo](https://classic.gazebosim.org/tutorials?tut=install_ubuntu)  

- ### 3.4 Install [gazebo_ros_pkgs](http://gazebosim.org/tutorials?tut=ros2_installing&cat=connect_ros)

- ### 3.5 Respository to Clone
  - #### 3.5.1 xarm_ros2 [https://github.com/xarm-Developer/xarm_ros2]
  - #### 3.5.2 realsense-ros [https://github.com/realsenseai/realsense-ros/blob/ros2-master/README.md]
  - #### 3.5.3 easy_handeye2 [https://github.com/marcoesposito1988/easy_handeye2]
  - #### 3.5.4 aruco_ros [https://github.com/pal-robotics/aruco_ros]
    


## 4. How To Use

- ### 4.1 Create a workspace
    ```bash
    # Skip this step if you already have a target workspace
    cd ~/projv1
    mkdir -p projv1/src
    ```

- ### 4.2 Obtain source code of "Projv1" repository
    ```bash
    # Remember to source ros2 environment settings first
    cd ~/projv1/src
    # DO NOT omit "--recursive"，or the source code of dependent submodule will not be downloaded.
    # Pay attention to the use of the -b parameter command branch, $ROS_DISTRO indicates the currently activated ROS version, if the ROS environment is not activated, you need to customize the specified branch (foxy/galactic/humble)
    git clone https://github.com/AlbertRRIC/Projv1 --recursive -b $ROS_DISTRO
    ```

- ### 4.3 Update "Projv1" repository 
    ```bash
    cd ~/projv1

    # If you did not use the --recursive or --recurse-submodules option when cloning, use this command to initialize and update all submodules
    git submodule update --init --recursive
    
    # Pull the main repository and update the submodule
    git pull --recurse-submodules
    ```

- ### 4.4 Install dependencies
    ```bash
    # Remember to source ros2 environment settings first
    cd ~/projv1/src/
    rosdep update
    rosdep install --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y
    ```
# projv1 Robotic Arm Manipulation Setup

This README is for setting up the project on a new device for:

* xArm7 robotic arm manipulation
* MoveIt 2
* Intel RealSense camera
* YOLO object detection
* ROS 2 service-based vision and manipulation pipeline

This setup excludes Flutter, KONE API, Nav2, RTAB-Map, and mobile base dependencies.

---

## 1. System Requirements

Use:

```text
Ubuntu 22.04
ROS 2 Humble
Python 3.10
```

Before running the setup, copy the full project folder to:

```bash
~/projv1
```

Important files/folders that must exist after copying:

```text
~/projv1/src/projv1_interfaces
~/projv1/src/projv1_vision
~/projv1/src/projv1_manipulation
~/projv1/models/best.pt
```

---

## 2. One-Shot Installation Command

Copy and run this entire command in a terminal:

```bash
# ============================================================
# MINIMAL INSTALL FOR projv1 ROBOTIC ARM + REALSENSE + YOLO
# Ubuntu 22.04 + ROS 2 Humble + xArm7 + MoveIt2 + RealSense + YOLO
# ============================================================

set -e

echo "============================================================"
echo "1. Basic Ubuntu tools"
echo "============================================================"

sudo apt update
sudo apt upgrade -y

sudo apt install -y \
  git curl wget unzip build-essential cmake \
  python3-pip python3-dev python3-venv \
  software-properties-common lsb-release gnupg

echo "============================================================"
echo "2. Set up ROS 2 Humble repository"
echo "============================================================"

sudo add-apt-repository universe -y

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update

echo "============================================================"
echo "3. Install ROS 2, MoveIt2, xArm manipulation deps, RealSense deps"
echo "============================================================"

sudo apt install -y \
  ros-humble-desktop \
  ros-dev-tools \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  python3-argcomplete \
  ros-humble-moveit \
  ros-humble-moveit-ros-planning-interface \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-controller-manager \
  ros-humble-joint-state-broadcaster \
  ros-humble-joint-trajectory-controller \
  ros-humble-gripper-controllers \
  ros-humble-control-msgs \
  ros-humble-trajectory-msgs \
  ros-humble-sensor-msgs \
  ros-humble-geometry-msgs \
  ros-humble-std-msgs \
  ros-humble-std-srvs \
  ros-humble-tf2-ros \
  ros-humble-tf2-geometry-msgs \
  ros-humble-tf-transformations \
  ros-humble-xacro \
  ros-humble-rviz2 \
  ros-humble-rqt \
  ros-humble-rqt-graph \
  ros-humble-rqt-image-view \
  ros-humble-realsense2-camera \
  ros-humble-realsense2-description \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  ros-humble-image-view \
  ros-humble-rosidl-default-generators \
  ros-humble-rosidl-default-runtime \
  ros-humble-ament-cmake \
  ros-humble-ament-cmake-python

echo "============================================================"
echo "4. Initialise rosdep"
echo "============================================================"

sudo rosdep init || true
rosdep update

echo "============================================================"
echo "5. Install YOLO / Python vision dependencies"
echo "============================================================"

python3 -m pip install --upgrade pip setuptools wheel

python3 -m pip install \
  "numpy>=1.23,<2" \
  opencv-python \
  ultralytics \
  torch \
  torchvision \
  torchaudio \
  transforms3d \
  scipy \
  matplotlib \
  pandas \
  pyyaml \
  pillow \
  requests

echo "============================================================"
echo "6. Check projv1 workspace"
echo "============================================================"

mkdir -p ~/projv1/src
cd ~/projv1/src

echo "============================================================"
echo "7. Clone xArm ROS 2 package if missing"
echo "============================================================"

if [ ! -d "xarm_ros2" ]; then
  git clone https://github.com/xArm-Developer/xarm_ros2.git --recursive -b humble
else
  echo "xarm_ros2 already exists, skipping"
fi

echo "============================================================"
echo "8. Clone RealSense ROS package if missing"
echo "============================================================"

if [ ! -d "realsense-ros" ]; then
  git clone https://github.com/IntelRealSense/realsense-ros.git -b ros2-master
else
  echo "realsense-ros already exists, skipping"
fi

echo "============================================================"
echo "9. Build projv1 workspace"
echo "============================================================"

cd ~/projv1

rm -rf build install log

source /opt/ros/humble/setup.bash

rosdep install --from-paths src --ignore-src -r -y

colcon build --symlink-install

echo "============================================================"
echo "10. Add source commands to ~/.bashrc"
echo "============================================================"

grep -qxF "source /opt/ros/humble/setup.bash" ~/.bashrc || \
  echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

grep -qxF "source ~/projv1/install/setup.bash" ~/.bashrc || \
  echo "source ~/projv1/install/setup.bash" >> ~/.bashrc

source ~/.bashrc

echo "============================================================"
echo "11. Final checks"
echo "============================================================"

source /opt/ros/humble/setup.bash
source ~/projv1/install/setup.bash

echo "Checking projv1 packages:"
ros2 pkg list | grep projv1 || true

echo "Checking Python vision dependencies:"
python3 -c "import cv2, numpy, ultralytics, transforms3d; print('Vision dependencies OK')"

echo "Checking YOLO:"
yolo version || true

echo "============================================================"
echo "DONE."
echo "Open a new terminal and run:"
echo "cd ~/projv1"
echo "source install/setup.bash"
echo "============================================================"
```

---


## Main Project Dependencies

This project requires:

```text
Ubuntu 22.04
ROS 2 Humble
MoveIt 2
ros2_control
xarm_ros2
RealSense ROS
cv_bridge
OpenCV
Ultralytics YOLO
PyTorch
NumPy >=1.23,<2
transforms3d
projv1_interfaces
projv1_vision
projv1_manipulation
```

---

## Main Project Files

The important custom project packages are:

```text
projv1_interfaces
projv1_vision
projv1_manipulation
```

The important trained model file is:

```text
~/projv1/models/best.pt
```

Without `best.pt`, the YOLO node may still run, but it will not use the trained plant/pot detection model.

- ### 4.5 Build Projv1
    ```bash
    # Remember to source ros2 and moveit2 environment settings first
    cd ~/projv1/
    # build all packages
    colcon build
   ```
    ```bash 
    # build selected packages
    colcon build --packages-select projv1_vision
    source install/setup.bash
    
    ```


## 5. Simulations

__Reminder 1: If there are multiple people using ros2 in the current LAN, in order to avoid mutual interference, please set ROS_DOMAIN_ID__  
  - [Humble](https://docs.ros.org/en/ros2_documentation/humble/Concepts/About-Domain-ID.html)

__Reminder 2： Remember to source the environment setup script before running any applications in xarm_ros2__  

```bash
cd ~/projv1/
source install/setup.bash
```
__Reminder 3： All following instructions will base on xArm7__


- ### 5.1 Terminal 1- Start xArm with gripper + Camera TF
    
```bash
cd ~/projv1
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch xarm_moveit_config _robot_moveit_realmove.launch.py

```

- ### 5.2 Terminal 2- Controllers
    
```bash
cd ~/projv1
source install/setup.bash
ros2 control list_controllers

```
   If not Active:
```bash
ros2 control load_controller --set-state active joint_state_broadcaster
ros2 control load_controller --set-state active xarm7_traj_controller

```
   Check:
```bash
ros2 control list_controllers

```
   Make sure Output:
```bash
joint_state_broadcaster active
xarm7_traj_controller active

```
- ### 5.3 Terminal 3- RealSense Camera
    
```bash
cd ~/projv1
source install/setup.bash

ros2 launch realsense2_camera rs_launch.py 

```

- ### 5.4 Terminal 4- Gazebo For Simulation
    
```bash
source /opt/ros/humble/setup.bash
source ~/projv1/install/setup.bash
ros2 launch xarm_moveit_config xarm7_moveit_gazebo.launch.py

```
https://github.com/xarm-Developer/xarm_ros2


- ### 5.5 Terminal 5- Selection of classes to detect
    
```bash
cd ~/projv1
source install/setup.bash
ros2 run projv1_vision select_class_node

```
For troubleshooting

On another Terminal 
```bash
cd ~/projv1
source install/setup.bash
ros2 topic echo /selected_class

```
You should see this output:
data: Browncup

- ### 5.6 Terminal 6- YOLO
    
```bash
cd ~/projv1
source install/setup.bash
ros2 run projv1_vision yolov2_node

```

- ### 5.7 Terminal 7- Transform node
    
```bash
cd ~/projv1
source install/setup.bash
ros2 run projv1_manipulation target_transform_node
 
```

- ### 5.8 Terminal 8- Check target coordinates
    
```bash
cd ~/projv1
source install/setup.bash
ros2 topic echo /target_base

```
   Only contine if you see:
   
   frame_id: link_base
   point:
   x: ...
   y: ...
   z: ...

- ### 5.9 Terminal 9- Moveit pick/place node
    
```bash
cd ~/projv1
source install/setup.bash
ros2 run projv1_manipulation moveit_pick_place_node

```

   Expected:
   
   Direct object-aware pick/place node started
   Accepted target...
   Sending joint goal...
   Goal succeeded
   
- ### 5.10 Terminal 10- Gazebo cup marker node
    
```bash
cd ~/projv1
source install/setup.bash
ros2 run projv1_manipulation gazebo_cup_marker_node

```

   Expected:
   
   Green cup should be spawned in Gazebo

## 6. Package Introduction

- ### 6.1 Terminal 1- Start xArm with gripper + Camera TF
    
```bash
cd ~/projv1
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch xarm_moveit_config _robot_moveit_realmove.launch.py

```

- ### 6.2 Terminal 2- Controllers
    
```bash
cd ~/projv1
source install/setup.bash
ros2 control list_controllers

```
   If not Active:
```bash
ros2 control load_controller --set-state active joint_state_broadcaster
ros2 control load_controller --set-state active xarm7_traj_controller

```
   Check:
```bash
ros2 control list_controllers

```
   Make sure Output:
```bash
joint_state_broadcaster active
xarm7_traj_controller active

```

- ### 6.3 Terminal 3- RealSense Camera
    
```bash
cd ~/projv1
source install/setup.bash

ros2 launch realsense2_camera rs_launch.py 

```

- ### 6.4 Terminal 4- Turn on visionv1_node

```bash
cd ~/projv1
source install/setup.bash

ros2 run projv1_vision visionv1_node

```

- ### 6.5 Terminal 5- Turn on visionv1_viewer ( to view the detected obj ) 

```bash
cd ~/projv1
source install/setup.bash

ros2 run projv1_vision visionv1_viewer

```

- ### 6.6 Terminal 6- Service

```bash
cd ~/projv1
source install/setup.bash

ros2 service call /visionv1/detect projv1_interfaces/srv/VisionDetect "{selected_class: 'Pot', target_frame: 'camera_color_frame', warmup_frames: 5}"
requester: making request: projv1_interfaces.srv.VisionDetect_Request(selected_class='Pot', target_frame='camera_color_frame', warmup_frames=5)

```
var: selected_class, target_frame, warmup_frames

## 7. Troubelshoot

- ### 7.1 View the TF frame link
```bash
ros2 run tf2_tools view_frames
```

- ### 7.2 Change of Detected Object

```bash
cd ~/projv1/training
source install/setup.bash

```
- Download the dataset from roboflow
- Put the unzipped dataset into the folder dataset

```bash
sudo apt update
pip install "numpy>=1.23,<2"
yolo detect train \
  data=dataset/data.yaml \
  model=yolo11n.pt \
  epochs=50 \
  imgsz=640

```
After training
```bash
pip install "numpy<2"

```
Expected example:
runs/detect/train-3/weights/best.pt

Change train-? and remove the prev best.pt
```bash

cp runs/detect/train-3/weights/best.pt ~/projv1/models/

```
How ws should look ( View in the code tab )

projv1/
├── src/
│   ├── xarm_ros2/                  # official xArm repo
│   ├── realsense-ros/              # camera driver
│
│   ├── projv1_vision/              # YOUR vision package
│   │   ├── projv1_vision/
│   │   │   ├── yolo_node.py
│   │   │   └── __init__.py
│   │   ├── package.xml
│   │   ├── setup.py
│   │   └── resource/
│
│   ├── projv1_manipulation/        # (later: MoveIt + robot control)
│   │   ├── projv1_manipulation/
│   │   ├── package.xml
│   │   └── setup.py
│
├── models/                         # ⭐ your trained models
│   └── best.pt
│
├── training/                       # ⭐ training workspace (NOT ROS)
│   ├── dataset/
│   │   ├── train/
│   │   ├── valid/
│   │   ├── test/
│   │   └── data.yaml
│   │
│   ├── runs/
│   │   └── detect/
│   │       └── train-3/
│   │           └── weights/
│   │               ├── best.pt
│   │               └── last.pt
│   │
│   └── (optional venv/)
│
├── build/                          # auto-generated
├── install/                        # auto-generated
└── log/                            # auto-generated

