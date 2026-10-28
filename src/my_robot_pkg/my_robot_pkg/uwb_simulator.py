#!/usr/bin/env python3
import math
import random
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
import tf2_ros
from rclpy.time import Time

class UwbSimulator(Node):
    def __init__(self):
        super().__init__('uwb_simulator')
        
        self.declare_parameter('noise_std', 0.0)
        self.declare_parameter('bias', 0.0)
        self.declare_parameter('dropout_prob', 0.0)

        self.noise_std = self.get_parameter('noise_std').value
        self.bias = self.get_parameter('bias').value
        self.dropout_prob = self.get_parameter('dropout_prob').value

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.pubs = [self.create_publisher(Range, f'/uwb/anchor_{i}', 10) for i in range(1, 5)]
        self.anchors = {1: (-4.5, -4.5, 0.5), 2: ( 4.5, -4.5, 0.5), 3: ( 4.5,  4.5, 0.5), 4: (-4.5,  4.5, 0.5)}

        self.timer = self.create_timer(0.1, self.publish_measurements)
        self.get_logger().info('Симулятор UWB запущен (TF режим)')

    def publish_measurements(self):
        try:
            # Берем позу робота на КАРТЕ через TF
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', Time())
            rx, ry = t.transform.translation.x, t.transform.translation.y
            rz = 0.0 
        except Exception:
            return # Ждем, пока TF инициализируется

        for anchor_id, (ax, ay, az) in self.anchors.items():
            msg = Range()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = f'uwb_anchor_{anchor_id}'
            msg.radiation_type = Range.ULTRASOUND
            msg.field_of_view = 1.57
            msg.min_range = 0.1
            msg.max_range = 20.0
            
            true_dist = math.sqrt((ax - rx)**2 + (ay - ry)**2 + (az - rz)**2)
            noisy_dist = true_dist + self.bias + random.gauss(0, self.noise_std)
            
            if random.random() < self.dropout_prob:
                msg.range = float('inf')
            else:
                msg.range = noisy_dist
                
            self.pubs[anchor_id - 1].publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = UwbSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()