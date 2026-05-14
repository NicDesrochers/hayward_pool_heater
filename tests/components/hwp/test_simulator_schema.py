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

import importlib.util
import unittest
from pathlib import Path

import esphome.config_validation as cv
from esphome.config import path_context
from esphome.const import KEY_CORE, KEY_TARGET_FRAMEWORK, KEY_TARGET_PLATFORM, PLATFORM_ESP32
from esphome.core import CORE


REPO_ROOT = Path(__file__).resolve().parents[3]
SIMULATOR_PATH = REPO_ROOT / "components" / "hwp_simulator" / "__init__.py"


def load_simulator_module():
    spec = importlib.util.spec_from_file_location("hwp_simulator_test", SIMULATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_esp32_idf_core():
    CORE.reset()
    import esphome.components.esp32.gpio  # noqa: F401
    from esphome.components.esp32.const import (
        KEY_BOARD,
        KEY_ESP32,
        KEY_VARIANT,
        VARIANT_ESP32,
    )

    CORE.config_path = REPO_ROOT / "tests" / "components" / "hwp" / "simulator-schema.yaml"
    CORE.name = "simulator-schema"
    CORE.friendly_name = "Simulator Schema"
    CORE.testing_mode = True
    CORE.config = {}
    CORE.data[KEY_CORE] = {
        KEY_TARGET_PLATFORM: PLATFORM_ESP32,
        KEY_TARGET_FRAMEWORK: "esp-idf",
    }
    CORE.data[KEY_ESP32] = {
        KEY_BOARD: "esp32dev",
        KEY_VARIANT: VARIANT_ESP32,
    }


class SimulatorSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.simulator = load_simulator_module()

    def validate(self, config):
        seed_esp32_idf_core()
        token = path_context.set(["hwp_simulator"])
        try:
            return self.simulator.CONFIG_SCHEMA(config)
        finally:
            path_context.reset(token)

    def test_minimal_valid_config_creates_default_entities(self):
        config = self.validate({"id": "hwp_sim", "pin_txrx": "GPIO16"})

        self.assertEqual(config["pin_txrx"]["number"], 16)
        self.assertEqual(config["startup_playbook"], "normal_idle")
        self.assertEqual(config["packet_buffer_size"], 120)
        self.assertFalse(config["active_on_boot"])
        self.assertEqual(config["playbook"]["name"], "HWP Simulator Playbook")
        self.assertEqual(config["active"]["name"], "HWP Simulator Active")
        self.assertEqual(config["command"]["name"], "HWP Simulator Command")
        self.assertEqual(config["current_playbook"]["name"], "HWP Simulator Current Playbook")
        self.assertEqual(config["last_rx_frame"]["name"], "HWP Simulator Last RX Frame")
        self.assertEqual(config["last_echo"]["name"], "HWP Simulator Last Echo")

    def test_explicit_config_validates(self):
        config = self.validate(
            {
                "id": "hwp_sim",
                "pin_txrx": "GPIO17",
                "startup_playbook": "rx_stress",
                "packet_buffer_size": 64,
                "active_on_boot": True,
                "playbook": {"name": "Playbook"},
                "active": {"name": "Run"},
                "interval_scale": {"name": "Scale"},
                "command": {"name": "Command"},
                "last_frame": {"name": "Last"},
                "last_rx_frame": {"name": "Last RX"},
                "last_echo": {"name": "Last Echo"},
                "error_count": {"name": "Errors"},
            }
        )

        self.assertEqual(config["startup_playbook"], "rx_stress")
        self.assertEqual(config["packet_buffer_size"], 64)
        self.assertTrue(config["active_on_boot"])
        self.assertEqual(config["playbook"]["name"], "Playbook")
        self.assertEqual(config["last_rx_frame"]["name"], "Last RX")
        self.assertEqual(config["last_echo"]["name"], "Last Echo")
        self.assertEqual(config["error_count"]["name"], "Errors")

    def test_invalid_playbook_fails(self):
        with self.assertRaises(cv.Invalid):
            self.validate(
                {
                    "id": "hwp_sim",
                    "pin_txrx": "GPIO16",
                    "startup_playbook": "mystery",
                }
            )

    def test_packet_buffer_bounds(self):
        with self.assertRaises(cv.Invalid):
            self.validate(
                {
                    "id": "hwp_sim",
                    "pin_txrx": "GPIO16",
                    "packet_buffer_size": 4,
                }
            )


if __name__ == "__main__":
    unittest.main()
