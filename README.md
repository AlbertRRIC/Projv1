# Projv1


## 1. Introduction

&ensp;&ensp;&ensp;&ensp;This repository contains simulation models, and corresponding motion planning and controlling demos of the xArm series from UFACTORY. The development and test environment is as follows
- Ubuntu 22.04 + ROS Humble

&ensp;&ensp;&ensp;&ensp;Please switch to the corresponding code branch according to different ros2 versions (no corresponding code branch means it has not been tested in this version)
- 
- Humble: [humble](https://github.com/xArm-Developer/xarm_ros2/tree/humble)
- 

## 2. Update History    
(2026-05-14) Completed YOLO Detection + Intel Realsense D435i Camera Integration
(2026-05-14) Processing Gazebo + pickplacenode 

## 3. Preparation

- ### 3.1 Install [ROS2](https://docs.ros.org/) 
  - [Humble](https://docs.ros.org/en/ros2_documentation/humble/Installation.html)

- ### 3.2 Install [Moveit2](https://moveit.ros.org/install-moveit2/binary/)  

- ### 3.3 Install [Gazebo](https://classic.gazebosim.org/tutorials?tut=install_ubuntu)  

- ### 3.4 Install [gazebo_ros_pkgs](http://gazebosim.org/tutorials?tut=ros2_installing&cat=connect_ros)  


## 4. How To Use

- ### 4.1 Create a workspace
    ```bash
    # Skip this step if you already have a target workspace
    cd ~
    mkdir -p dev_ws/src
    ```

- ### 4.2 Obtain source code of "Projv1" repository
    ```bash
    # Remember to source ros2 environment settings first
    cd ~/dev_ws/src
    # DO NOT omit "--recursive"，or the source code of dependent submodule will not be downloaded.
    # Pay attention to the use of the -b parameter command branch, $ROS_DISTRO indicates the currently activated ROS version, if the ROS environment is not activated, you need to customize the specified branch (foxy/galactic/humble)
    git clone https://github.com/xArm-Developer/xarm_ros2.git --recursive -b $ROS_DISTRO
    ```

- ### 4.3 Update "Projv1" repository 
    ```bash
    cd ~/dev_ws/src/Projv1

    # If you did not use the --recursive or --recurse-submodules option when cloning, use this command to initialize and update all submodules
    git submodule update --init --recursive
    
    # Pull the main repository and update the submodule
    git pull --recurse-submodules
    ```

- ### 4.4 Install dependencies
    ```bash
    # Remember to source ros2 environment settings first
    cd ~/dev_ws/src/
    rosdep update
    rosdep install --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y
    ```

- ### 4.5 Build Projv1
    ```bash
    # Remember to source ros2 and moveit2 environment settings first
    cd ~/dev_ws/
    # build all packages
    colcon build
    
    # build selected packages
    colcon build --packages-select Projv1
    ```


## 5. Package Introduction

__Reminder 1: If there are multiple people using ros2 in the current LAN, in order to avoid mutual interference, please set ROS_DOMAIN_ID__  
  - [Humble](https://docs.ros.org/en/ros2_documentation/humble/Concepts/About-Domain-ID.html)

__Reminder 2： Remember to source the environment setup script before running any applications in xarm_ros2__  

```bash
cd ~/dev_ws/
source install/setup.bash
```
__Reminder 3： All following instructions will base on xArm7__
__Reminder 4: The <hw_ns> described below is replaced with the actual one, the xarm series defaults is xarm, and the rest defaults is ufactory__  


- ### 5.1 Terminal 1- Gazebo
    
```bash
   source /opt/ros/humble/setup.bash
   source ~/projv1/install/setup.bash

   ros2 launch xarm_moveit_config xarm7_moveit_gazebo.launch.py

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

   ros2 launch realsense2_camera rs_launch.py \
   align_depth.enable:=true \
   enable_color:=true \
   enable_depth:=true


```

- ### 5.4 Terminal 4- Camera TF
    
```bash
   cd ~/projv1
   source install/setup.bash

   ros2 run tf2_ros static_transform_publisher \
   0.2 0.0 0.2 0 0 0 \
   link_base camera_link



```

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

   ros2 run projv1_vision yolov1_node



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

- ### 5.9 Terminal 9- Direct pick/place node
    
```bash
   cd ~/projv1
   source install/setup.bash
   ~/projv1/src/projv1_gazebo/scripts/spawn_table_cups.sh
   ros2 run projv1_manipulation direct_pick_place_node


 

```

   Expected:
   
   Direct object-aware pick/place node started
   Accepted target...
   Sending joint goal...
   Goal succeeded




