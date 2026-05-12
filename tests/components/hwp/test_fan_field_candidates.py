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

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "packets"
    / "hwp_demo_packets.json"
)


def load_packet(packet_id):
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        packets = json.load(fixture_file)["packets"]
    for packet in packets:
        if packet["id"] == packet_id:
            return [int(value, 16) for value in packet["bytes"]]
    raise AssertionError(f"fixture packet {packet_id!r} not found")


def decode_temperature_extended(raw):
    decimal = raw & 0x01
    integer = raw >> 1
    return float(integer) - 30.0 + (0.5 if decimal else 0.0)


def decode_decimal_number(raw):
    decimal = raw & 0x01
    integer = (raw >> 1) & 0x3F
    negative = raw & 0x80
    value = float(integer) * (-1.0 if negative else 1.0)
    return value + (0.5 if decimal else 0.0)


def decode_large_integer(high_byte, low_byte):
    return (high_byte << 8) | low_byte


class TestFanFieldCandidates(unittest.TestCase):
    def test_base_fan_candidate_fields(self):
        data = load_packet("base-fan")
        fan_flags = data[2]

        self.assertEqual(data[0], 0x82)
        self.assertEqual(fan_flags >> 4, 0x01, "F01 fan mode should be high speed")
        self.assertEqual(
            (fan_flags >> 3) & 0x01,
            0,
            "tmp maps bit 3 of the fan flags byte to F10 speed-control temperature source",
        )
        self.assertEqual(
            fan_flags & 0x07,
            0x06,
            "lower three fan flag bits remain candidate/unknown bits",
        )
        self.assertEqual(data[10], 100, "tmp maps byte 10 to F13 max fan voltage percent")

    def test_base_type_84_candidate_fields(self):
        data = load_packet("base-type-84")

        self.assertEqual(data[0], 0x84)
        self.assertEqual(data[1], 0xB1)
        self.assertEqual(decode_temperature_extended(data[2]), 40.0)
        self.assertEqual(decode_temperature_extended(data[3]), 15.0)
        self.assertEqual(decode_temperature_extended(data[4]), 10.0)
        self.assertEqual(decode_temperature_extended(data[5]), 10.0)
        self.assertEqual(decode_temperature_extended(data[6]), 20.0)
        self.assertEqual(decode_temperature_extended(data[7]), 30.0)
        self.assertEqual(data[8], 0, "tmp maps byte 8 to F08 low-speed running time")
        self.assertEqual(data[9], 0, "tmp maps byte 9 to F09 stop low-speed running time")
        self.assertEqual(data[10], 0x78, "final payload byte remains unknown")

    def test_base_conf_a_candidate_fields(self):
        data = load_packet("base-conf-a")
        flags = data[2]

        self.assertEqual(data[0], 0x85)
        self.assertEqual((flags >> 2) & 0x01, 0, "U01 flow meter should be disabled")
        self.assertEqual(
            (flags >> 3) & 0x01,
            0,
            "tmp maps bit 3 of the CONF_A flags byte to F11 speed-control module disabled",
        )
        self.assertEqual((flags >> 6) & 0x01, 0, "D06 defrost eco should be normal")
        self.assertEqual(decode_decimal_number(data[3]), 3.0)
        self.assertEqual(decode_large_integer(data[9], data[10]), 205)


if __name__ == "__main__":
    unittest.main()
