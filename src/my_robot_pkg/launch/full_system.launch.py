import os
from launch import LaunchDescription
from launch.actions import TimerAction, LogInfo
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # ============================================================
    # ПУТИ К ФАЙЛАМ (замените при необходимости)
    # ============================================================
    # Если используете пакет — раскомментируйте строки ниже:
    pkg_share = get_package_share_directory('my_robot_pkg')
    urdf_file = os.path.join(pkg_share, 'urdf', 'rviz_robot.urdf')
    map_yaml  = os.path.join(pkg_share, 'maps', 'map.yaml')
    rviz_cfg  = os.path.join(pkg_share, 'rviz', 'display.rviz')


    # ============================================================
    # ЧТЕНИЕ URDF
    # ============================================================
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # ============================================================
    # 1. Robot State Publisher — публикует модель робота
    # ============================================================
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': False
        }]
    )

    # ============================================================
    # 2. Joint State Publisher GUI — оживляет колёса
    # ============================================================
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        remappings=[('/joint_states', '/joint_states')]
    )

    # ============================================================
    # 3. Map Server — сервер карты полигона
    # ============================================================
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml,
            'use_sim_time': False
        }]
    )

    # ============================================================
    # 4. Lifecycle Manager — активирует map_server
    # ============================================================
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['map_server'],
            'use_sim_time': False
        }]
    )

    # ============================================================
    # 5. Static Transform Publisher — связка map -> base_footprint
    #    Робот ставится в центр карты (0, 0, 0)
    # ============================================================

    # БЫЛО:
    # static_tf = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='static_tf_map_to_base',
    #     output='screen',
    #     arguments=[
    #         '--x', '-4',
    #         '--y', '-4',
    #         '--z', '0.0',
    #         '--yaw', '0.0',
    #         '--pitch', '0.0',
    #         '--roll', '0.0',
    #         '--frame-id', 'map',
    #         '--child-frame-id', 'base_footprint'
    #     ]
    # )

    # СТАЛО: Статическая связка карты и одометрии (перенос начала координат робота в угол карты)
    static_tf_map_to_odom = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_map_to_odom',
            output='screen',
            arguments=[
                '--x', '-4.0',
                '--y', '-4.0',
                '--z', '0.0',
                '--yaw', '0.0',
                '--pitch', '0.0',
                '--roll', '0.0',
                '--frame-id', 'map',
                '--child-frame-id', 'odom'  # <-- Теперь дочерний фрейм odom
            ]
        )

        # Новый узел - симулятор истинной траектории
    trajectory_node = Node(
        package='my_robot_pkg',
        executable='trajectory_publisher',
        name='trajectory_publisher',
        output='screen'
    )

    # ============================================================
    # 6. RViz2 — визуализация
    # ============================================================
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_cfg] if os.path.exists(rviz_cfg) else []
    )

    # ============================================================
    # ЗАДЕРЖКИ ЗАПУСКА
    # map_server нужно активировать через lifecycle_manager
    # с небольшой задержкой, чтобы он успел подняться
    # ============================================================

    # RViz запускается через 2 секунды
    delayed_rviz = TimerAction(
        period=2.0,
        actions=[
            LogInfo(msg='[LAUNCH] Запуск RViz2...'),
            rviz2
        ]
    )

    # Активация map_server — через 7 секунд (после того как RViz подписался)
    delayed_lifecycle = TimerAction(
        period=8.0,
        actions=[
            LogInfo(msg='[LAUNCH] Активация map_server через lifecycle_manager...'),
            lifecycle_manager
        ]
    )

    def anchor_tf(name, x, y, z):
         return Node(
             package='tf2_ros',
             executable='static_transform_publisher',
             name=f'{name}_tf',
             output='screen',
             arguments=[
                 '--x', str(x),
                 '--y', str(y),
                 '--z', str(z),
                 '--yaw', '0.0',
                 '--pitch', '0.0',
                 '--roll', '0.0',
                 '--frame-id', 'map',
                 '--child-frame-id', name
             ]
         )
 
    anchor_1_tf = anchor_tf('uwb_anchor_1', -4.5, -4.5, 0.5)
    anchor_2_tf = anchor_tf('uwb_anchor_2',  4.5, -4.5, 0.5)
    anchor_3_tf = anchor_tf('uwb_anchor_3',  4.5,  4.5, 0.5)
    anchor_4_tf = anchor_tf('uwb_anchor_4', -4.5,  4.5, 0.5)
 
    # ============================================================
    # 7. Визуализация UWB-якорей (MarkerArray)
    # ============================================================
    uwb_anchors_node = Node(
        package='my_robot_pkg',
        executable='uwb_anchors',
        name='uwb_anchors',
        output='screen'
    )


    return LaunchDescription([
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
        delayed_lifecycle,
        delayed_rviz,
    ])