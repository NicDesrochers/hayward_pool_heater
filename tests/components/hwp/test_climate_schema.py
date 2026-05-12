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
CLIMATE_PATH = REPO_ROOT / "components" / "hwp" / "climate.py"


def load_climate_module():
    spec = importlib.util.spec_from_file_location("hwp_climate_test", CLIMATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_esp32_idf_core():
    CORE.reset()

    # Import after reset so ESP32 GPIO validators are registered on the fresh registry.
    import esphome.components.esp32.gpio  # noqa: F401
    from esphome.components.esp32.const import (
        KEY_BOARD,
        KEY_ESP32,
        KEY_VARIANT,
        VARIANT_ESP32,
    )

    CORE.config_path = REPO_ROOT / "tests" / "components" / "hwp" / "schema-test.yaml"
    CORE.name = "schema-test"
    CORE.friendly_name = "Schema Test"
    CORE.testing_mode = True
    CORE.data[KEY_CORE] = {
        KEY_TARGET_PLATFORM: PLATFORM_ESP32,
        KEY_TARGET_FRAMEWORK: "esp-idf",
    }
    CORE.data[KEY_ESP32] = {
        KEY_BOARD: "esp32dev",
        KEY_VARIANT: VARIANT_ESP32,
    }


class ClimateSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.climate = load_climate_module()

    def validate(self, config):
        seed_esp32_idf_core()
        token = path_context.set(["climate", 0])
        try:
            return self.climate.CONFIG_SCHEMA(config)
        finally:
            path_context.reset(token)

    def test_minimal_valid_config(self):
        config = self.validate({"id": "pool_heater", "pin_txrx": "GPIO22"})

        self.assertEqual(config["name"], "Pool Heater")
        self.assertEqual(config["update_interval"].total_seconds, 30)
        self.assertEqual(config["pin_txrx"]["number"], 22)

    def test_missing_pin_txrx_fails(self):
        with self.assertRaisesRegex(cv.Invalid, "pin_txrx"):
            self.validate({"id": "pool_heater"})

    def test_update_interval_lower_bound(self):
        with self.assertRaisesRegex(cv.Invalid, "at least 10s"):
            self.validate(
                {
                    "id": "pool_heater",
                    "pin_txrx": "GPIO22",
                    "update_interval": "9s",
                }
            )

    def test_update_interval_upper_bound(self):
        with self.assertRaisesRegex(cv.Invalid, "at most 1800s"):
            self.validate(
                {
                    "id": "pool_heater",
                    "pin_txrx": "GPIO22",
                    "update_interval": "1801s",
                }
            )

    def test_default_helper_entities_are_created(self):
        config = self.validate({"id": "pool_heater", "pin_txrx": "GPIO22"})

        self.assertEqual(
            set(config["sensors"].keys()),
            set(self.climate.SENSORS.keys()),
        )
        self.assertEqual(
            set(config["input"].keys()),
            set(self.climate.INPUTS.keys()),
        )
        self.assertEqual(config["active_mode_switch"]["name"], "Active Mode")
        self.assertEqual(config["update_sensors_switch"]["name"], "Update Sensors")
        self.assertEqual(config["generate_code"]["name"], "Generate Code")

    def test_explicit_optional_helper_entities_validate(self):
        config = self.validate(
            {
                "id": "pool_heater",
                "pin_txrx": "GPIO22",
                "sensors": {
                    "s02_water_flow": {"name": "Water Flow Test"},
                },
                "input": {
                    "d01_defrost_start": {"name": "Defrost Start Test"},
                    "d06_defrost_eco_mode": {"name": "Defrost Eco Test"},
                },
            }
        )

        self.assertEqual(
            config["sensors"]["s02_water_flow"]["name"],
            "Water Flow Test",
        )
        self.assertEqual(
            config["input"]["d01_defrost_start"]["name"],
            "Defrost Start Test",
        )
        self.assertEqual(
            config["input"]["d06_defrost_eco_mode"]["name"],
            "Defrost Eco Test",
        )

    def test_fan_helper_defaults_are_created(self):
        config = self.validate({"id": "pool_heater", "pin_txrx": "GPIO22"})

        self.assertIn(
            "f02_fan_high_speed_cool_setpoint",
            config["input"],
        )
        self.assertIn(
            "f10_fan_speed_control_temp",
            config["input"],
        )
        self.assertIn(
            "f11_speed_control_module",
            config["input"],
        )
        self.assertIn(
            "f13_max_fan_voltage_pct",
            config["input"],
        )
        self.assertIn(
            "f12_min_fan_voltage_pct",
            config["input"],
        )

    def test_explicit_fan_helper_entities_validate(self):
        config = self.validate(
            {
                "id": "pool_heater",
                "pin_txrx": "GPIO22",
                "input": {
                    "f02_fan_high_speed_cool_setpoint": {
                        "name": "Fan High Cool Test"
                    },
                    "f10_fan_speed_control_temp": {
                        "name": "Fan Speed Source Test"
                    },
                    "f11_speed_control_module": {
                        "name": "Speed Module Test"
                    },
                    "f12_min_fan_voltage_pct": {
                        "name": "Min Fan Voltage Test"
                    },
                    "f13_max_fan_voltage_pct": {
                        "name": "Max Fan Voltage Test"
                    },
                },
            }
        )

        self.assertEqual(
            config["input"]["f02_fan_high_speed_cool_setpoint"]["name"],
            "Fan High Cool Test",
        )
        self.assertEqual(
            config["input"]["f10_fan_speed_control_temp"]["name"],
            "Fan Speed Source Test",
        )
        self.assertEqual(
            config["input"]["f11_speed_control_module"]["name"],
            "Speed Module Test",
        )
        self.assertEqual(
            config["input"]["f12_min_fan_voltage_pct"]["name"],
            "Min Fan Voltage Test",
        )
        self.assertEqual(
            config["input"]["f13_max_fan_voltage_pct"]["name"],
            "Max Fan Voltage Test",
        )


if __name__ == "__main__":
    unittest.main()
