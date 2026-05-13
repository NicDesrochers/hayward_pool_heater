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

import unittest

from analysis.hwp_fixtures import (
    REQUIRED_PACKET_KEYS,
    FixtureValidationError,
    all_menu_expectations,
    all_menu_pairs,
    all_packets,
    calculate_checksum,
    format_hex_byte,
    load_fixture_files,
    parse_hex_byte,
    validate_unique_packet_ids,
)


REQUIRED_FRAME_TYPES = {
    "0x81",
    "0x82",
    "0x83",
    "0x84",
    "0x85",
    "0x86",
    "0xD1",
    "0xD2",
    "0xDD",
}


class TestPacketFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixture_files()
        cls.packets = all_packets(cls.fixtures)
        cls.menu_expectations = all_menu_expectations(cls.fixtures)
        cls.menu_pairs = all_menu_pairs(cls.fixtures)

    def test_fixture_schema(self):
        self.assertGreaterEqual(len(self.fixtures), 2)
        self.assertGreaterEqual(len(self.packets), 27)
        validate_unique_packet_ids(self.fixtures)

        for fixture in self.fixtures:
            with self.subTest(fixture=fixture.name):
                self.assertEqual(fixture.schema_version, 1)
                self.assertTrue(fixture.source)
                self.assertTrue(fixture.provenance)
                self.assertGreater(len(fixture.packets), 0)

    def test_packet_bytes_match_metadata(self):
        for packet in self.packets:
            with self.subTest(packet=packet.id):
                self.assertEqual(len(packet.bytes), packet.length)
                self.assertEqual(packet.frame_type, format_hex_byte(packet.bytes[0]))
                self.assertIn(packet.source, {"heater", "controller"})
                self.assertTrue(packet.notes)

    def test_expected_frame_type_coverage(self):
        frame_types = {packet.frame_type for packet in self.packets}
        self.assertTrue(
            REQUIRED_FRAME_TYPES.issubset(frame_types),
            f"missing frame types: {sorted(REQUIRED_FRAME_TYPES - frame_types)}",
        )

    def test_checksums_match_current_protocol_rules(self):
        invalid_packets = []

        for packet in self.packets:
            with self.subTest(packet=packet.id):
                checksum = calculate_checksum(packet.bytes, packet.length)

                self.assertEqual(packet.expected_checksum, checksum)
                self.assertEqual(
                    packet.checksum_valid,
                    packet.bytes[packet.length - 1] == checksum,
                )
                if not packet.checksum_valid:
                    invalid_packets.append(packet.id)

        self.assertEqual(invalid_packets, ["demo-type-dd-invalid-change"])

    def test_demo_menu_expectations_pin_menu_locations(self):
        menus = {expectation.menu for expectation in self.menu_expectations}
        self.assertTrue(
            {
                "H02",
                "R01",
                "R02",
                "R03",
                "R04",
                "R05",
                "R06",
                "R07",
                "R09",
                "R10",
                "R11",
            }.issubset(menus)
        )

        for expectation in self.menu_expectations:
            with self.subTest(menu=expectation.menu, packet=expectation.packet_id):
                expected_frame_type = (
                    "0x83" if expectation.menu in {"R09", "R10", "R11"} else "0x81"
                )
                self.assertEqual(expectation.frame_type, expected_frame_type)
                self.assertIn(expectation.source, {"heater", "controller"})
                self.assertGreaterEqual(expectation.raw_byte_index, 0)
                self.assertLess(expectation.raw_byte_index, 12)

    def test_demo_menu_pairs_change_only_the_menu_byte(self):
        pairs_by_menu = {pair.menu: pair for pair in self.menu_pairs}
        self.assertTrue({"R01", "R02", "R04", "R05", "R06", "R07"}.issubset(pairs_by_menu))
        self.assertTrue({"R09", "R10", "R11"}.issubset(pairs_by_menu))
        self.assertNotIn("R03", pairs_by_menu)

        for pair in self.menu_pairs:
            with self.subTest(pair=pair.id):
                self.assertEqual(pair.changed_byte_indexes, (pair.raw_byte_index,))
                self.assertEqual(len(pair.changed_byte_indexes), 1)

    def test_shared_hex_parser_rejects_bad_values(self):
        for value in ("82", "0x1", "0x100", 4):
            with self.subTest(value=value):
                with self.assertRaises((FixtureValidationError, ValueError)):
                    parse_hex_byte(value)


if __name__ == "__main__":
    unittest.main()
