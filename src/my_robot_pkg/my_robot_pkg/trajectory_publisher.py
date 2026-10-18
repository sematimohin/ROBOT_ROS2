#!/usr/bin/env python3
import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

class TrajectoryPublisher(Node):
    def __init__(self):
        super().__init__('trajectory_publisher')
        
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Параметры движения
        self.v = 0.8  
        self.w = 0.8  
        self.side_len = 8
        
        self.t_straight = self.side_len / self.v
        self.t_turn = (math.pi / 2) / self.w

        # Состояние
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.state = 'WAITING' 
        self.t_state = 0.0
        self.sides = 0
        
        self.dt_fixed = 0.01  # <--- УВЕЛИЧЕНА ЧАСТОТА ДО 100 Гц (было 0.02)
        self.get_logger().info('Узел траектории запущен. Ожидание 3 сек...')

    def update(self):
        dt = self.dt_fixed 
        self.t_state += dt

        # Логика состояний
        if self.state == 'WAITING':
            v_cmd = 0.0
            w_cmd = 0.0
            if self.t_state >= 3.0:
                self.state = 'STRAIGHT'
                self.t_state = 0.0
                self.get_logger().info('Начинаем движение!')
        elif self.state == 'STRAIGHT':
            v_cmd = self.v
            w_cmd = 0.0
            if self.t_state >= self.t_straight:
                self.state = 'TURN'
                self.t_state = 0.0
                self.sides += 1
        else: # TURN
            v_cmd = 0.0
            w_cmd = self.w
            if self.t_state >= self.t_turn:
                self.state = 'STRAIGHT'
                self.t_state = 0.0
                if self.sides >= 4:
                    self.sides = 0
                    self.x, self.y, self.theta = 0.0, 0.0, 0.0

        if self.state != 'WAITING':
            self.x += v_cmd * math.cos(self.theta) * dt
            self.y += v_cmd * math.sin(self.theta) * dt
            self.theta += w_cmd * dt
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # Берем время строго на момент отправки
        now = self.get_clock().now().to_msg()

        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = math.sin(self.theta / 2.0)
        t.transform.rotation.w = math.cos(self.theta / 2.0)
        self.tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        odom.twist.twist.linear.x = v_cmd
        odom.twist.twist.angular.z = w_cmd
        self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryPublisher()
    try:
        while rclpy.ok():
            node.update()
            rclpy.spin_once(node, timeout_sec=0.0)
            time.sleep(node.dt_fixed)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()