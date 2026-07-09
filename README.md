- # 4.5 projv1 Robotic Arm Manipulation Setup

- ## 4.5.1 xArm required packages

  These are needed for the real xArm + MoveIt launch:

    xarm_msgs, 
    xarm_description, 
    xarm_sdk, 
    uf_ros_lib, 
    xarm_api, 
    xarm_controller, 
    xarm_moveit_config, 
  
- ## 4.5.2 RealSense required packages

  Needed for the D435i camera:

  realsense2_camera
  realsense2_camera_msgs
  realsense2_description
  ros-humble-librealsense2

  Install with:
  ```bash
  sudo apt install -y \
  ros-humble-librealsense2 \
  ros-humble-realsense2-camera \
  ros-humble-realsense2-description \
  ros-humble-diagnostic-updater \
  ros-humble-diagnostic-msgs
  ```

   Test:
   ```bash
   ros2 launch realsense2_camera rs_launch.py enable_color:=true enable_depth:=true
   ```

- ## 4.5.3 Python dependencies

  Needed for YOLO, camera processing, transforms, and manipulation logic:
     ```bash
     pip install \
     "numpy>=1.23,<2" \
     opencv-python \
     ultralytics \
     torch \
     torchvision \
     scipy \
     transforms3d \
     pyrealsense2
     ```
- ## 4.5.4 Final build command

  Use this:
  ```bash
    cd ~/projv1
    
    rm -rf build install log
    
    source /opt/ros/humble/setup.bash
    
    colcon build --symlink-install \
      --packages-skip xarm_moveit_servo xarm_planner
    
    source install/setup.bash
  ```
- ## 4.5.5 Final run commands
  
  Terminal 1:
  
   ```bash
  cd ~/projv1
  source /opt/ros/humble/setup.bash
  source install/setup.bash
  
  ros2 launch projv1_bringup plant_pot_full_system.launch.py
   ```
  
  Terminal 2:
  
   ```bash
  cd ~/projv1
  source /opt/ros/humble/setup.bash
  source install/setup.bash
  
  ros2 service call /activate_plant_pot_above projv1_interfaces/srv/ActivatePlantPotAbove "{selected_class: 'Pot', target_frame: 'link_base', warmup_frames: 5}"
   ```
