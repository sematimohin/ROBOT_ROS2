#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
import time

class FakeClockPublisher(Node):
    def __init__(self):
        super().__init__('fake_clock_publisher')
        self.pub = self.create_publisher(Clock, '/clock', 10)
        self.sim_time = 0.0
        self.dt = 0.01  # 100 Гц
        self.get_logger().info('Генератор симулированного времени запущен.')

    def run(self):
        while rclpy.ok():
            self.sim_time += self.dt
            msg = Clock()
            msg.clock.sec = int(self.sim_time)
            msg.clock.nanosec = int((self.sim_time - int(self.sim_time)) * 1e9)
            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(self.dt)

def main(args=None):
    rclpy.init(args=args)
    node = FakeClockPublisher()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()