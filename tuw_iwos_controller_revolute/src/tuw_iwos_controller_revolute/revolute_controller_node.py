#!/usr/bin/env python3

import math
import rospy
import sys

from typing import NoReturn
from typing import Optional

from rospy import Publisher
from rospy import Subscriber

from dynamic_reconfigure.server import Server

from tuw_iwos_controller_revolute.cfg import RevoluteControllerDynamicConfig
from tuw_nav_msgs.msg import Joints
from tuw_nav_msgs.msg import JointsIWS

from tuw_iwos_controller_revolute.config.abstract_dynamic_config import DynamicReconfigureDict
from tuw_iwos_controller_revolute.config.revolute_controller_config import RevoluteControllerConfig
from tuw_iwos_controller_revolute.exception.invalid_file_exception import InvalidFileException
from tuw_iwos_controller_revolute.exception.invalid_path_exception import InvalidPathException


class RevoluteControllerNode:

    def __init__(self, wheel_diameter: float) -> None:
        self._node_name: str = 'IWOS_REVOLUTE_CONTROLLER'

        self._wheel_circumference: float = float(wheel_diameter) * math.pi
        self._config: Optional[RevoluteControllerConfig] = None
        self._reconfigure_server: Optional[Server] = None

        self._command_subscriber_topic: str = 'iwos_cmd'
        self._command_publisher_topic: str = 'iwos_cmd_revolute'

        self._state_subscriber_topic: str = 'iwos_state_revolute_raw'
        self._state_publisher_topic: str = 'iwos_state_revolute_tuw'

        self._command_subscriber: Optional[Subscriber] = None
        self._command_publisher: Optional[Publisher] = None

        self._state_subscriber: Optional[Subscriber] = None
        self._state_publisher: Optional[Publisher] = None

    def run(self) -> NoReturn:
        rospy.init_node(self._node_name)

        try:
            config_file_path = rospy.get_param(param_name='iwos_controller_revolute_config')
            self._config = RevoluteControllerConfig().from_file(config_file_path=config_file_path)
        except InvalidPathException:
            rospy.logerr('%s: failed to load config (invalid path)', self._node_name)
        except InvalidFileException:
            rospy.logerr('%s: failed to load config (invalid file)', self._node_name)

        self._reconfigure_server = Server(
            type=RevoluteControllerDynamicConfig,
            callback=self.callback_reconfigure)

        self._command_subscriber = rospy.Subscriber(
            name=self._command_subscriber_topic,
            data_class=JointsIWS,
            callback=self.callback_command,
            queue_size=100)

        self._command_publisher = rospy.Publisher(
            name=self._command_publisher_topic,
            data_class=Joints,
            queue_size=100)

        self._state_subscriber = rospy.Subscriber(
            name=self._state_subscriber_topic,
            data_class=Joints,
            callback=self.callback_state,
            queue_size=100)

        self._state_publisher = rospy.Publisher(
            name=self._state_publisher_topic,
            data_class=Joints,
            queue_size=100)

        rospy.spin()

    def callback_reconfigure(self, dynamic_reconfigure: DynamicReconfigureDict, level: int) -> DynamicReconfigureDict:
        if level == -1:
            return self._config.to_dynamic_reconfigure()

        self._config = RevoluteControllerConfig().from_dynamic_reconfigure(dynamic_reconfigure)
        return self._config.to_dynamic_reconfigure()

    def callback_command(self, message_in: JointsIWS) -> None:
        assert(len(message_in.revolute) == 2)

        if message_in.type_revolute == "cmd_velocity":
            message_out = Joints()

            for mps in message_in.revolute:
                if mps > self._config.max_velocity:
                    mps = self._config.max_velocity
                value_out = self.mps_to_rpm(mps=float(mps)) * self._config.velocity_scale
                message_out.velocity.append(value_out)

            if self._config.reverse_left_wheel:
                message_out.velocity[0] *= -1
            if self._config.reverse_right_wheel:
                message_out.velocity[1] *= -1
            if self._config.exchange_wheels:
                message_out.velocity.reverse()

            self._command_publisher.publish(message_out)

        else:
            rospy.logerr('%s: revolute type %s not supported', self._node_name, message_in.type_revolute)

    def callback_state(self, message_in: Joints) -> None:
        assert(len(message_in.position) == 2)
        assert(len(message_in.velocity) == 2)
        assert(len(message_in.torque) == 2)

        message_out = Joints(header=message_in.header, name=["left_revolute", "right_revolute"])
        message_out.position = [self.steps_to_rad(steps=int(steps)) for steps in list(message_in.position)]
        message_out.velocity = [self.rpm_to_mps(rpm=float(rpm)) for rpm in list(message_in.velocity)]
        message_out.torque = list(message_in.torque)

        if self._config.exchange_wheels:
            message_out.position.reverse()
            message_out.velocity.reverse()
            message_out.torque.reverse()

        if self._config.reverse_left_wheel:
            message_out.position[0] *= -1
            message_out.velocity[0] *= -1
            message_out.torque[0] *= -1

        if self._config.reverse_right_wheel:
            message_out.position[1] *= -1
            message_out.velocity[1] *= -1
            message_out.torque[1] *= -1

        self._state_publisher.publish(message_out)

    def mps_to_rpm(self, mps: float) -> float:
        return float(mps * 60 / self._wheel_circumference)

    def rpm_to_mps(self, rpm: float) -> float:
        return float(rpm * self._wheel_circumference / 60)

    def rad_to_steps(self, rad: float) -> int:
        return int(rad * self._config.sensor_steps / (2 * math.pi))

    def steps_to_rad(self, steps: int) -> float:
        return float(steps * 2 * math.pi / self._config.sensor_steps)


if __name__ == '__main__':
    try:
        arguments = rospy.myargv(argv=sys.argv)
        wheel_diameter_arg = arguments[1]
        revolute_controller_node = RevoluteControllerNode(wheel_diameter=wheel_diameter_arg)
        revolute_controller_node.run()
    except rospy.ROSInterruptException:
        rospy.logerr('ROS Interrupt Exception')