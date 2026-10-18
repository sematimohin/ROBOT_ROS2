#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point


class UWBAnchors(Node):
    def __init__(self):
        super().__init__('uwb_anchors')

        # Координаты 4-х якорей (x, y, z) в метрах
        # Карта у вас 10x10 м, origin в (-5, -5), значит диапазон [-5..+5]
        # Ставим якоря по углам полигона, чуть внутрь от стен
        self.anchors = [
            ('anchor_1', -4.5, -4.5, 0.5),
            ('anchor_2',  4.5, -4.5, 0.5),
            ('anchor_3',  4.5,  4.5, 0.5),
            ('anchor_4', -4.5,  4.5, 0.5),
        ]

        self.publisher = self.create_publisher(MarkerArray, '/uwb_anchors', 10)

        # Публикуем периодически (RViz подписывается уже после запуска узла)
        self.timer = self.create_timer(1.0, self.publish_markers)
        self.get_logger().info(f'Опубликовано {len(self.anchors)} UWB-якорей')

    def publish_markers(self):
        msg = MarkerArray()

        for i, (name, x, y, z) in enumerate(self.anchors):
            # Сфера
            sphere = Marker()
            sphere.header.frame_id = 'map'
            sphere.header.stamp = self.get_clock().now().to_msg()
            sphere.ns = 'uwb_anchors'
            sphere.id = i * 2
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x = x
            sphere.pose.position.y = y
            sphere.pose.position.z = z
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = 0.3
            sphere.scale.y = 0.3
            sphere.scale.z = 0.3
            sphere.color.r = 1.0
            sphere.color.g = 0.0
            sphere.color.b = 0.0
            sphere.color.a = 0.9
            msg.markers.append(sphere)

            # Подпись с именем якоря
            text = Marker()
            text.header.frame_id = 'map'
            text.header.stamp = self.get_clock().now().to_msg()
            text.ns = 'uwb_labels'
            text.id = i * 2 + 1
            text.type = Marker.TEXT_VIEW_FACING
            text.action = Marker.ADD
            text.pose.position.x = x
            text.pose.position.y = y
            text.pose.position.z = z + 0.5
            text.pose.orientation.w = 1.0
            text.scale.z = 0.25
            text.color.r = 1.0
            text.color.g = 1.0
            text.color.b = 1.0
            text.color.a = 1.0
            text.text = name
            msg.markers.append(text)

        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = UWBAnchors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()