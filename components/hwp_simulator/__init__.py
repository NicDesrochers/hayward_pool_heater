# Copyright (c) 2024 S. Leclerc (sle118@hotmail.com)
#
# This file is part of the Pool Heater Controller component project.
#
# @project Pool Heater Controller Component
# @developer S. Leclerc (sle118@hotmail.com)
# @license MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import button, esp32, number, select, sensor, switch, text, text_sensor
from esphome.const import (
    CONF_ID,
    CONF_INPUT,
    CONF_OUTPUT,
    ENTITY_CATEGORY_CONFIG,
    ENTITY_CATEGORY_DIAGNOSTIC,
)

CODEOWNERS = ["@sle118"]
DEPENDENCIES = ["esp32"]
AUTO_LOAD = ["button", "number", "select", "sensor", "switch", "text", "text_sensor"]

CONF_PIN_TXRX = "pin_txrx"
CONF_STARTUP_PLAYBOOK = "startup_playbook"
CONF_PACKET_BUFFER_SIZE = "packet_buffer_size"
CONF_ACTIVE_ON_BOOT = "active_on_boot"
CONF_PLAYBOOK = "playbook"
CONF_ACTIVE = "active"
CONF_INTERVAL_SCALE = "interval_scale"
CONF_COMMAND = "command"
CONF_CURRENT_PLAYBOOK = "current_playbook"
CONF_LAST_FRAME = "last_frame"
CONF_LAST_RX_FRAME = "last_rx_frame"
CONF_LAST_ECHO = "last_echo"
CONF_STATUS = "status"
CONF_STEP = "step"
CONF_PACKET_COUNT = "packet_count"
CONF_ERROR_COUNT = "error_count"
CONF_START_BUTTON = "start_button"
CONF_PAUSE_BUTTON = "pause_button"
CONF_STEP_BUTTON = "step_button"
CONF_RESET_BUTTON = "reset_button"
CONF_INJECT_BUTTON = "inject_button"

PLAYBOOK_OPTIONS = [
    "paused",
    "normal_idle",
    "config_refresh",
    "active_defrost_echo",
    "rx_stress",
]

hwp_simulator_ns = cg.esphome_ns.namespace("hwp_simulator")
HWPSimulator = hwp_simulator_ns.class_("HWPSimulator", cg.Component)
HWPSimulatorPlaybookSelect = hwp_simulator_ns.class_(
    "HWPSimulatorPlaybookSelect", select.Select, cg.Parented
)
HWPSimulatorActiveSwitch = hwp_simulator_ns.class_(
    "HWPSimulatorActiveSwitch", switch.Switch, cg.Component, cg.Parented
)
HWPSimulatorIntervalScaleNumber = hwp_simulator_ns.class_(
    "HWPSimulatorIntervalScaleNumber", number.Number, cg.Parented
)
HWPSimulatorStartButton = hwp_simulator_ns.class_(
    "HWPSimulatorStartButton", button.Button, cg.Component, cg.Parented
)
HWPSimulatorPauseButton = hwp_simulator_ns.class_(
    "HWPSimulatorPauseButton", button.Button, cg.Component, cg.Parented
)
HWPSimulatorStepButton = hwp_simulator_ns.class_(
    "HWPSimulatorStepButton", button.Button, cg.Component, cg.Parented
)
HWPSimulatorResetButton = hwp_simulator_ns.class_(
    "HWPSimulatorResetButton", button.Button, cg.Component, cg.Parented
)
HWPSimulatorInjectButton = hwp_simulator_ns.class_(
    "HWPSimulatorInjectButton", button.Button, cg.Component, cg.Parented
)
HWPSimulatorCommandText = hwp_simulator_ns.class_(
    "HWPSimulatorCommandText", text.Text, cg.Parented
)


CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(HWPSimulator),
        cv.Required(CONF_PIN_TXRX): pins.gpio_pin_schema(
            {CONF_OUTPUT: True, CONF_INPUT: True}
        ),
        cv.Optional(CONF_STARTUP_PLAYBOOK, default="normal_idle"): cv.enum(
            {option: option for option in PLAYBOOK_OPTIONS}, lower=True
        ),
        cv.Optional(CONF_PACKET_BUFFER_SIZE, default=120): cv.int_range(min=8, max=512),
        cv.Optional(CONF_ACTIVE_ON_BOOT, default=False): cv.boolean,
        cv.Optional(CONF_PLAYBOOK, default={"name": "HWP Simulator Playbook"}): select.select_schema(
            HWPSimulatorPlaybookSelect,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:playlist-play",
        ),
        cv.Optional(CONF_ACTIVE, default={"name": "HWP Simulator Active"}): switch.switch_schema(
            HWPSimulatorActiveSwitch,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:play-network",
            default_restore_mode="RESTORE_DEFAULT_OFF",
        ),
        cv.Optional(
            CONF_INTERVAL_SCALE, default={"name": "HWP Simulator Interval Scale"}
        ): number.number_schema(
            HWPSimulatorIntervalScaleNumber,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:speedometer",
        ),
        cv.Optional(CONF_COMMAND, default={"name": "HWP Simulator Command"}): text.text_schema(
            HWPSimulatorCommandText,
            entity_category=ENTITY_CATEGORY_CONFIG,
            mode="TEXT",
            icon="mdi:console",
        ),
        cv.Optional(CONF_START_BUTTON, default={"name": "HWP Simulator Start"}): button.button_schema(
            HWPSimulatorStartButton,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:play",
        ),
        cv.Optional(CONF_PAUSE_BUTTON, default={"name": "HWP Simulator Pause"}): button.button_schema(
            HWPSimulatorPauseButton,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:pause",
        ),
        cv.Optional(CONF_STEP_BUTTON, default={"name": "HWP Simulator Step"}): button.button_schema(
            HWPSimulatorStepButton,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:debug-step-over",
        ),
        cv.Optional(CONF_RESET_BUTTON, default={"name": "HWP Simulator Reset"}): button.button_schema(
            HWPSimulatorResetButton,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:restart",
        ),
        cv.Optional(CONF_INJECT_BUTTON, default={"name": "HWP Simulator Inject"}): button.button_schema(
            HWPSimulatorInjectButton,
            entity_category=ENTITY_CATEGORY_CONFIG,
            icon="mdi:ray-start-arrow",
        ),
        cv.Optional(
            CONF_CURRENT_PLAYBOOK, default={"name": "HWP Simulator Current Playbook"}
        ): text_sensor.text_sensor_schema(
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:playlist-check",
        ),
        cv.Optional(CONF_LAST_FRAME, default={"name": "HWP Simulator Last Frame"}): text_sensor.text_sensor_schema(
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:code-brackets",
        ),
        cv.Optional(
            CONF_LAST_RX_FRAME, default={"name": "HWP Simulator Last RX Frame"}
        ): text_sensor.text_sensor_schema(
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:download-network-outline",
        ),
        cv.Optional(
            CONF_LAST_ECHO, default={"name": "HWP Simulator Last Echo"}
        ): text_sensor.text_sensor_schema(
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:upload-network-outline",
        ),
        cv.Optional(CONF_STATUS, default={"name": "HWP Simulator Status"}): text_sensor.text_sensor_schema(
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:information-outline",
        ),
        cv.Optional(CONF_STEP, default={"name": "HWP Simulator Step"}): sensor.sensor_schema(
            accuracy_decimals=0,
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:counter",
        ),
        cv.Optional(
            CONF_PACKET_COUNT, default={"name": "HWP Simulator Packet Count"}
        ): sensor.sensor_schema(
            accuracy_decimals=0,
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:counter",
        ),
        cv.Optional(
            CONF_ERROR_COUNT, default={"name": "HWP Simulator Error Count"}
        ): sensor.sensor_schema(
            accuracy_decimals=0,
            entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
            icon="mdi:alert-circle-outline",
        ),
    }
).extend(cv.COMPONENT_SCHEMA)


def include_esp_driver_rmt():
    include_builtin_idf_component = getattr(
        esp32, "include_builtin_idf_component", None
    )
    if include_builtin_idf_component is None:
        return
    include_builtin_idf_component("esp_driver_rmt")


async def to_code(config):
    include_esp_driver_rmt()

    pin = await cg.gpio_pin_expression(config[CONF_PIN_TXRX])
    var = cg.new_Pvariable(config[CONF_ID], pin)
    await cg.register_component(var, config)
    cg.add(var.set_startup_playbook(config[CONF_STARTUP_PLAYBOOK]))
    cg.add(var.set_packet_buffer_size(config[CONF_PACKET_BUFFER_SIZE]))
    cg.add(var.set_active_on_boot(config[CONF_ACTIVE_ON_BOOT]))

    playbook = await select.new_select(config[CONF_PLAYBOOK], options=PLAYBOOK_OPTIONS)
    await cg.register_parented(playbook, var)
    cg.add(var.set_playbook_select(playbook))

    active = await switch.new_switch(config[CONF_ACTIVE])
    await cg.register_component(active, config[CONF_ACTIVE])
    await cg.register_parented(active, var)
    cg.add(var.set_active_switch(active))

    interval = await number.new_number(
        config[CONF_INTERVAL_SCALE], min_value=0.1, max_value=10.0, step=0.1
    )
    await cg.register_parented(interval, var)
    cg.add(var.set_interval_scale_number(interval))

    command = await text.new_text(config[CONF_COMMAND], min_length=0, max_length=160)
    await cg.register_parented(command, var)
    cg.add(var.set_command_text(command))

    for key in [
        CONF_START_BUTTON,
        CONF_PAUSE_BUTTON,
        CONF_STEP_BUTTON,
        CONF_RESET_BUTTON,
        CONF_INJECT_BUTTON,
    ]:
        btn = await button.new_button(config[key])
        await cg.register_component(btn, config[key])
        await cg.register_parented(btn, var)

    current_playbook = await text_sensor.new_text_sensor(config[CONF_CURRENT_PLAYBOOK])
    cg.add(var.set_current_playbook_sensor(current_playbook))
    last_frame = await text_sensor.new_text_sensor(config[CONF_LAST_FRAME])
    cg.add(var.set_last_frame_sensor(last_frame))
    last_rx_frame = await text_sensor.new_text_sensor(config[CONF_LAST_RX_FRAME])
    cg.add(var.set_last_rx_frame_sensor(last_rx_frame))
    last_echo = await text_sensor.new_text_sensor(config[CONF_LAST_ECHO])
    cg.add(var.set_last_echo_sensor(last_echo))
    status = await text_sensor.new_text_sensor(config[CONF_STATUS])
    cg.add(var.set_status_sensor(status))

    step_sensor = await sensor.new_sensor(config[CONF_STEP])
    cg.add(var.set_step_sensor(step_sensor))
    packet_count = await sensor.new_sensor(config[CONF_PACKET_COUNT])
    cg.add(var.set_packet_count_sensor(packet_count))
    error_count = await sensor.new_sensor(config[CONF_ERROR_COUNT])
    cg.add(var.set_error_count_sensor(error_count))
