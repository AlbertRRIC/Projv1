# Projv1


## 1. Introduction

&ensp;&ensp;&ensp;&ensp;This repository contains simulation models, and corresponding motion planning and controlling demos of the xArm series from UFACTORY. The development and test environment is as follows
- Ubuntu 22.04 + ROS Humble

&ensp;&ensp;&ensp;&ensp;Please switch to the corresponding code branch according to different ros2 versions (no corresponding code branch means it has not been tested in this version)
- 
- Humble: [humble](https://github.com/xArm-Developer/xarm_ros2/tree/humble)

## 2. Update History    
- (2026-05-14) Completed YOLO Detection + Intel Realsense D435i Camera Integration
- (2026-05-14) Processing Gazebo + pickplacenode
- (2026-05-15) Added Selection Node
- (2026-05-16) Linked eef with both Camera + Gripper
- (2026-06-23) Added Hand-eye Calibration

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


## 5. Package Introduction

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


## 6. Troubelshoot

- ### 6.1 View the TF frame link
```bash
ros2 run tf2_tools view_frames
```

- ### 6.2 Change of Detected Object

```bash
cd ~/projv1
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

