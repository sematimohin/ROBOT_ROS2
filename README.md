# Моделирование мобильного робота с дифференциальным приводом в ROS 2

Данный проект представляет собой симуляцию автономного мобильного робота, движущегося по заданной траектории (квадрат) на цифровом полигоне. Проект включает в себя 3D-модель робота (URDF), карту препятствий, визуализацию UWB-якорей и генератор истинной кинематики движения.

## 📋 Предварительные требования

Проект протестирован в среде **Ubuntu 22.04 (WSL 2)** с установленным **ROS 2 Humble**.

Для корректной работы необходимо установить следующие пакеты ROS 2. Выполните в терминале:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-joint-state-publisher-gui \
  ros-humble-nav2-map-server \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-tf2-ros \
  ros-humble-rviz2 \
  ros-humble-rqt-plot \
  ros-humble-plotjuggler-ros
```

## Установка и сборка проекта
### 1. Клонируйте репозиторий в ваше рабочее пространство ROS 2:
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone <URL_РЕПОЗИТОРИЯ> my_robot_pkg
```

### Структура проекта должна иметь следующий вид:
```
ros2_ws/
├── src/
│   └── my_robot_pkg/               # Исходный код пакета
│       ├── launch/
│       │   └── full_system.launch.py # Главный файл запуска всей системы
│       ├── urdf/
│       │   └── rviz_robot.urdf     # Кинематическая модель робота (4 колеса, лидар)
│       ├── maps/
│       │   ├── map.png             # Исходник карты в формате png
│       │   ├── map.pgm             # Растровая карта полигона (бинарная)
│       │   └── map.yaml            # Метаданные карты (разрешение, начало координат)
│       ├── rviz/
│       │   └── display.rviz        # Сохраненная конфигурация визуализации RViz2
│       ├── my_robot_pkg/           # Python-модули (узлы)
│       │   ├── __init__.py
│       │   ├── trajectory_publisher.py # Узел кинематики и генерации траектории
│       │   ├── fake_clock.py       # Генератор стабильного времени для WSL 2
│       │   └── uwb_anchors.py      # Узел визуализации UWB-якорей (MarkerArray)
│       │   └── Другие модули .py   .............................................
│       ├── package.xml             # Манифест пакета ROS 2
│       └── setup.py                # Файл сборки (регистрация узлов и ресурсов)
```

### 2. Перейдите в корень рабочего пространства и соберите пакет:
```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_pkg
```
### 3. Активируйте окружение:
```bash
source install/setup.bash
```
### 4. Запуск симуляции:
```bash
ros2 launch my_robot_pkg full_system.launch.py
```

### 5. Команды для пересборки с полной очисткой (нужны чтобы перезапускать симуляцию в rviz)
```bash
cd ~/ros2_ws
rm -rf build/my_robot_pkg install/my_robot_pkg
colcon build --packages-select my_robot_pkg
source install/setup.bash
ros2 launch my_robot_pkg full_system.launch.py
```

## 📊 Просмотр истинных координат и скоростей 
### Способ 1. (Графики)
### 1. Запустите симуляцию. Откройте новый терминал и введите:
```bash
ros2 run plotjuggler plotjuggler
```
### 2. Выберите "Start with ROS Topic Subscriber".

### 3. Найдите топик /odom и выберите нужные поля (pose.pose.position.x, twist.twist.linear.x и т.д.).

### 4. Перетащите их на рабочую область для визуализации.

### Способ 2. (Точные числовые значения в реальном времени)
```bash
ros2 topic echo /odom --field pose.pose.position
ros2 topic echo /odom --field twist.twist
```

## Граф обмена сообщениями (Computation Graph) (какие узлы существуют, кто на что подписан и кто куда публикует данные)
```bash
source ~/ros2_ws/install/setup.bash
rqt_graph
```

## Дерево координатных трансформаций (TF Tree)
```bash
source ~/ros2_ws/install/setup.bash
ros2 run tf2_tools view_frames
```

## Примечания:
1. 
```bash
При работе в WSL 2 системное время внутри Linux может «скакать» (отставать или идти назад) из-за синхронизации с Windows. 
Это приводит к ошибке TF_OLD_DATA (данные из прошлого), из-за которой робот двигается рывками или замирает.

Решение: В проекте реализован собственный узел fake_clock.py, который генерирует идеально ровное симулированное время (публикует его в топик /clock).
Все узлы системы (включая RViz2 и robot_state_publisher) запускаются с параметром use_sim_time = True. 
Это заставляет их игнорировать системные часы Windows и использовать время от нашего генератора. Благодаря этому движение робота становится абсолютно плавным.
```




