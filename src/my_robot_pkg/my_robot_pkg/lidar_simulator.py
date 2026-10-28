#!/usr/bin/env python3
import math
import random
import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import LaserScan
import tf2_ros
from rclpy.time import Time

class LidarSimulator(Node):
    def __init__(self):
        super().__init__('lidar_simulator')
        
        # Параметры
        self.declare_parameter('noise_std', 0.02)
        self.declare_parameter('bias', 0.0)
        self.declare_parameter('dropout_prob', 0.0)

        self.noise_std = self.get_parameter('noise_std').value
        self.bias = self.get_parameter('bias').value
        self.dropout_prob = self.get_parameter('dropout_prob').value

        # Инициализация TF2 (для получения истинной позы на карте)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)

        self.num_beams = 360 
        self.angle_min = -math.pi
        self.angle_max = math.pi
        self.range_max = 10.0
        
        self.map_data = None
        self.map_info = None
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        self.timer = self.create_timer(0.1, self.generate_scan) # 10 Гц

    def map_callback(self, msg):
        self.map_info = msg.info
        self.map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))

    def generate_scan(self):
        if self.map_data is None:
            return

        # 1. Получаем истинную позу робота на карте через TF
        try:
            # Ищем трансформацию от карты до лидара
            t = self.tf_buffer.lookup_transform('map', 'laser_frame', Time())
            self.current_x = t.transform.translation.x
            self.current_y = t.transform.translation.y
            
            # Кватернион в Yaw
            q = t.transform.rotation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            # Если TF еще не готов (в первые секунды запуска) - пропускаем шаг
            return

        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'laser_frame'
        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = (self.angle_max - self.angle_min) / self.num_beams
        scan.range_min = 0.1
        scan.range_max = self.range_max
        ranges = []

        res = self.map_info.resolution
        origin_x = self.map_info.origin.position.x
        origin_y = self.map_info.origin.position.y

        for i in range(self.num_beams):
            angle = self.current_yaw + self.angle_min + i * scan.angle_increment
            step_size = res / 2.0
            dist = 0.0
            hit = False
            
            # Ray Casting
            while dist < self.range_max:
                dist += step_size
                px = self.current_x + dist * math.cos(angle)
                py = self.current_y + dist * math.sin(angle)
                
                col = int((px - origin_x) / res)
                row = int((py - origin_y) / res)
                
                if row < 0 or row >= self.map_info.height or col < 0 or col >= self.map_info.width:
                    break
                
                if self.map_data[row, col] > 50:
                    hit = True
                    break
            
            if hit:
                measured_dist = dist + self.bias + random.gauss(0, self.noise_std)
                if random.random() < self.dropout_prob:
                    ranges.append(float('inf'))
                else:
                    ranges.append(measured_dist)
            else:
                ranges.append(float('inf'))

        scan.ranges = ranges
        self.scan_pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = LidarSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()