import os
from launch import LaunchDescription
from launch.actions import TimerAction, LogInfo
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('my_robot_pkg')
    urdf_file = os.path.join(pkg_share, 'urdf', 'rviz_robot.urdf')
    map_yaml  = os.path.join(pkg_share, 'maps', 'map.yaml')
    rviz_cfg  = os.path.join(pkg_share, 'rviz', 'display.rviz')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # 0. ГЕНЕРАТОР ВРЕМЕНИ
    fake_clock_node = Node(
        package='my_robot_pkg',
        executable='fake_clock',
        name='fake_clock_publisher',
        output='screen'
    )

    # 1. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    # 2. Joint State Publisher GUI
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    # 3. Map Server
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        parameters=[{'yaml_filename': map_yaml, 'use_sim_time': True}]
    )

    # 4. Lifecycle Manager
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        parameters=[{'autostart': True, 'node_names': ['map_server'], 'use_sim_time': True}]
    )

    # 5. Статическая связка map -> odom
    static_tf_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '-4.0', '--y', '-4.0', '--z', '0.0',
            '--yaw', '0.0', '--pitch', '0.0', '--roll', '0.0',
            '--frame-id', 'map', '--child-frame-id', 'odom'
        ],
        parameters=[{'use_sim_time': True}]
    )

    # 6. Узел истинной траектории
    trajectory_node = Node(
        package='my_robot_pkg',
        executable='trajectory_publisher',
        parameters=[{'use_sim_time': True}]
    )

    # 7. UWB-якоря (все с use_sim_time)
    def anchor_tf(name, x, y, z):
        return Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--x', str(x), '--y', str(y), '--z', str(z),
                '--yaw', '0.0', '--pitch', '0.0', '--roll', '0.0',
                '--frame-id', 'map', '--child-frame-id', name
            ],
            parameters=[{'use_sim_time': True}]
        )

    # БЕЗ ШУМА И БЕЗ СМЕЩЕНИЙ
    # uwb_simulator = Node(
    #     package='my_robot_pkg', executable='uwb_simulator', name='uwb_simulator',
    #     parameters=[{'use_sim_time': True, 'noise_std': 0.0, 'bias': 0.0, 'dropout_prob': 0.0}]
    # )
    # lidar_simulator = Node(
    #     package='my_robot_pkg', executable='lidar_simulator', name='lidar_simulator',
    #     parameters=[{'use_sim_time': True, 'noise_std': 0.0, 'bias': 0.0, 'dropout_prob': 0.0}]
    # )

    # # ВКЛ ШУМЫ
    # uwb_simulator = Node(
    #     package='my_robot_pkg', executable='uwb_simulator', name='uwb_simulator',
    #     parameters=[{'use_sim_time': True, 'noise_std': 0.3, 'bias': 0.0, 'dropout_prob': 0.0}]
    # )
    # lidar_simulator = Node(
    #     package='my_robot_pkg', executable='lidar_simulator', name='lidar_simulator',
    #     parameters=[{'use_sim_time': True, 'noise_std': 0.05, 'bias': 0.0, 'dropout_prob': 0.0}]
    # )

    # ВКЛ СМЕЩЕНИЯ
    uwb_simulator = Node(
        package='my_robot_pkg', executable='uwb_simulator', name='uwb_simulator',
        parameters=[{'use_sim_time': True, 'noise_std': 0.0, 'bias': 1.0, 'dropout_prob': 0.0}]
    )
    lidar_simulator = Node(
        package='my_robot_pkg', executable='lidar_simulator', name='lidar_simulator',
        parameters=[{'use_sim_time': True, 'noise_std': 0.0, 'bias': 0.2, 'dropout_prob': 0.0}]
    )
 
    anchor_1_tf = anchor_tf('uwb_anchor_1', -4.5, -4.5, 0.5)
    anchor_2_tf = anchor_tf('uwb_anchor_2',  4.5, -4.5, 0.5)
    anchor_3_tf = anchor_tf('uwb_anchor_3',  4.5,  4.5, 0.5)
    anchor_4_tf = anchor_tf('uwb_anchor_4', -4.5,  4.5, 0.5)

    uwb_anchors_node = Node(
        package='my_robot_pkg',
        executable='uwb_anchors',
        parameters=[{'use_sim_time': True}]
    )

    # 8. RViz2
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_cfg] if os.path.exists(rviz_cfg) else [],
        parameters=[{'use_sim_time': True}]
    )

    delayed_rviz = TimerAction(period=2.0, actions=[rviz2])
    delayed_lifecycle = TimerAction(period=5.0, actions=[lifecycle_manager])

    return LaunchDescription([
        fake_clock_node,
        robot_state_publisher,
        joint_state_publisher_gui,
        map_server,
        static_tf_map_to_odom,
        trajectory_node,
        anchor_1_tf,
        anchor_2_tf,
        anchor_3_tf,
        anchor_4_tf,
        uwb_anchors_node,
        uwb_simulator,
        lidar_simulator,
        delayed_rviz,
        delayed_lifecycle,
    ])