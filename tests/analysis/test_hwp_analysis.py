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

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from analysis import hwp_analyze
from analysis.hwp_active_tx_fixtures import (
    allowed_normalization_differences,
    command_echo_differences,
    load_active_tx_fixture_file,
)
from analysis.hwp_annotation_fixtures import load_annotation_fixture_file
from analysis.hwp_fixtures import (
    fixture_index_by_bytes,
    load_fixture_file,
    load_fixture_files,
)
from analysis.hwp_log_parser import (
    parse_annotation_windows,
    parse_log_line,
    parse_log_lines,
    strip_ansi,
)


LONG_CONFIG_LINE = (
    "2025-06-24 10:15:28,903 - "
    "\x1b[0;37m[2025-06-24 10:15:28][V][hwp.pk:413]"
    "\x1b[1;31m[RX]\x1b[0;37m: Same  "
    "[82][B1 16 13 56 50 10 1E 03 01 64][98] CONFIG_2  (HEAT) "
    "( 5.0s) fan frame\x1b[0m"
)
SHORT_CONDITION_LINE = (
    "2025-06-24 10:15:31,561 - [2025-06-24 10:15:31][V][hwp.pk:413]"
    "[RX]: Chg   [DD][1D 1D 19 11 1F 00 00         ][83] COND_D    "
    "(HEAT) (10.0s)"
)
CONTROLLER_LINE = (
    "2025-06-24 10:15:29,010 - [2025-06-24 10:15:29][V][hwp.pk:413]"
    "[RX]: Same  [CF][B1 00 00 15 03 05 11 06 00 00][B4] CLOCK     "
    "(CONT) (55.0s)"
)
TX_COMMAND_LINE = (
    "2026-05-12 16:20:53,257 - [16:20:53.257][I][hwp:454][TX]: "
    "SEND  [85][B1 00 06 4A 16 00 08 00 00 CD][71] CONFIG_5  "
    "(HEAT) defrost normal command"
)
TX_QUEUE_LINE = (
    "2026-05-12 16:20:51,933 - [16:20:51.933][V][hwp:114]: "
    "TXQ   [85][B1 40 06 1E 16 00 08 00 00 CD][85] CONFIG_5  "
    "(HEAT) defrost eco command"
)
ANNOTATED_WINDOW_LINES = [
    "2024-11-01 11:46:33,685 - F02 - 41.5 -- BEGIN\n",
    (
        "2024-11-01 11:46:33,719 - F02 - 41.5: "
        "\x1b[0;36m[D][hwp.pk:404]\x1b[1;31m[RX]\x1b[0;36m: "
        "\x1b[0;93mChg   [84][B1 \x1b[7m8F\x1b[27m 5A 50 50 64 78 00 00 78]"
        "[12] CONFIG_4  (CONT) (2.0s)\x1b[0m\n"
    ),
    "2024-11-01 11:46:33,719 - F02 - 41.5 -- END\n",
]


class TestHwpAnalysis(unittest.TestCase):
    def test_strip_ansi(self):
        self.assertEqual(strip_ansi("\x1b[31mhello\x1b[0m"), "hello")

    def test_parse_long_config_line(self):
        packet = parse_log_line(LONG_CONFIG_LINE, line_number=7)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.line_number, 7)
        self.assertEqual(packet.timestamp, "2025-06-24 10:15:28")
        self.assertEqual(packet.kind, "Same")
        self.assertEqual(packet.label, "CONFIG_2")
        self.assertEqual(packet.source, "heater")
        self.assertEqual(packet.length, 12)
        self.assertEqual(packet.frame_type, "0x82")
        self.assertTrue(packet.checksum_valid)

    def test_parse_short_condition_line(self):
        packet = parse_log_line(SHORT_CONDITION_LINE, line_number=8)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.kind, "Chg")
        self.assertEqual(packet.label, "COND_D")
        self.assertEqual(packet.source, "heater")
        self.assertEqual(packet.length, 9)
        self.assertEqual(packet.frame_type, "0xDD")
        self.assertTrue(packet.checksum_valid)

    def test_parse_controller_line(self):
        packet = parse_log_line(CONTROLLER_LINE)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.source, "controller")
        self.assertEqual(packet.source_marker, "CONT")
        self.assertEqual(packet.frame_type, "0xCF")

    def test_parse_tx_command_line(self):
        packet = parse_log_line(TX_COMMAND_LINE)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.kind, "SEND")
        self.assertEqual(packet.source, "controller")
        self.assertEqual(packet.source_marker, "TX")
        self.assertEqual(packet.label, "CONFIG_5")
        self.assertEqual(packet.frame_type, "0x85")
        self.assertTrue(packet.checksum_valid)

    def test_parse_tx_queue_line_without_direction_marker(self):
        packet = parse_log_line(TX_QUEUE_LINE)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.kind, "TXQ")
        self.assertEqual(packet.source, "controller")
        self.assertEqual(packet.label, "CONFIG_5")
        self.assertEqual(packet.frame_type, "0x85")
        self.assertTrue(packet.checksum_valid)

    def test_fixture_index_matches_parsed_bytes(self):
        fixtures = load_fixture_files()
        index = fixture_index_by_bytes(fixtures)
        packets = parse_log_lines([LONG_CONFIG_LINE, SHORT_CONDITION_LINE])
        self.assertIn(packets[0].byte_key, index)
        self.assertIn(packets[1].byte_key, index)

    def test_parse_annotation_window(self):
        windows = parse_annotation_windows(ANNOTATED_WINDOW_LINES)
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].label, "F02 - 41.5")
        self.assertEqual(windows[0].start_line, 1)
        self.assertEqual(windows[0].end_line, 3)
        self.assertEqual(len(windows[0].packets), 1)
        self.assertEqual(windows[0].packets[0].kind, "Chg")
        self.assertEqual(windows[0].packets[0].frame_type, "0x84")
        self.assertEqual(windows[0].packets[0].source, "controller")

    def test_annotation_fixture_loads_reference_windows(self):
        fixture = load_annotation_fixture_file(
            "tests/fixtures/annotations/hwp_annotated_fan_control_2024_11_01.json"
        )
        labels = {annotation.label for annotation in fixture.annotations}
        self.assertIn("F02 - 41.5", labels)
        self.assertIn("F13 -  50", labels)
        self.assertIn("F01 - 4", labels)
        self.assertGreaterEqual(len(fixture.annotations), 14)

    def test_fan_annotation_fixture_has_read_write_contracts(self):
        fixture = load_annotation_fixture_file(
            "tests/fixtures/annotations/hwp_annotated_fan_control_2024_11_01.json"
        )
        fan_annotations = [
            annotation
            for annotation in fixture.annotations
            if annotation.id.startswith("f")
        ]
        self.assertGreaterEqual(len(fan_annotations), 13)
        for annotation in fan_annotations:
            with self.subTest(annotation=annotation.id):
                self.assertIsNotNone(annotation.read)
                self.assertIsNotNone(annotation.write)
                self.assertEqual(annotation.read.field, annotation.write.field)
                self.assertEqual(annotation.read.value, annotation.write.value)
                self.assertEqual(
                    annotation.packet.bytes[annotation.read.raw_byte_index],
                    annotation.read.raw_byte_value,
                )
                self.assertEqual(annotation.write.expected_bytes, annotation.packet.bytes)
                self.assertTrue(annotation.write.checksum_valid)

    def test_fan_annotation_fixture_pins_key_read_values(self):
        fixture = load_annotation_fixture_file(
            "tests/fixtures/annotations/hwp_annotated_fan_control_2024_11_01.json"
        )
        annotations = {annotation.id: annotation for annotation in fixture.annotations}
        expectations = {
            "f01-4": ("f01_fan_mode", "Scheduled Ambient", 2, 0x46),
            "f02-41-5": ("f02_fan_high_speed_cool_setpoint", 41.5, 2, 0x8F),
            "f08-23": ("f08_fan_low_speed_running_time", 23.0, 8, 0x17),
            "f10-1": ("f10_fan_speed_control_temp", "Ambient Temperature", 2, 0x3E),
            "f11-1": ("f11_speed_control_module", "Disabled", 2, 0x08),
            "f12-55": ("f12_min_fan_voltage_pct", 55.0, 10, 0x37),
            "f13-50": ("f13_max_fan_voltage_pct", 50.0, 10, 0x32),
        }
        for annotation_id, expected in expectations.items():
            with self.subTest(annotation=annotation_id):
                field, value, index, raw = expected
                read = annotations[annotation_id].read
                self.assertEqual(read.field, field)
                self.assertEqual(read.value, value)
                self.assertEqual(read.raw_byte_index, index)
                self.assertEqual(read.raw_byte_value, raw)

    def test_active_tx_fixture_loads_config5_defrost_transactions(self):
        fixture = load_active_tx_fixture_file(
            "tests/fixtures/active_tx/hwp_active_tx_config5_defrost_2026_05_12.json"
        )
        transactions = {transaction.id: transaction for transaction in fixture.transactions}

        self.assertEqual(set(transactions), {"config5-defrost-eco", "config5-defrost-normal"})
        self.assertEqual(transactions["config5-defrost-eco"].requested_value, "Eco")
        self.assertEqual(transactions["config5-defrost-normal"].requested_value, "Normal")
        for transaction in fixture.transactions:
            with self.subTest(transaction=transaction.id):
                self.assertEqual(transaction.command.source, "controller")
                self.assertEqual(transaction.echo.source, "heater")
                self.assertTrue(transaction.command.checksum_valid)
                self.assertTrue(transaction.echo.checksum_valid)
                self.assertEqual(transaction.target.frame_type, "0x85")
                self.assertEqual(transaction.target.raw_byte_index, 2)
                self.assertEqual(transaction.target.raw_bit_index, 6)

    def test_active_tx_fixture_allows_only_declared_echo_normalization(self):
        fixture = load_active_tx_fixture_file(
            "tests/fixtures/active_tx/hwp_active_tx_config5_defrost_2026_05_12.json"
        )
        for transaction in fixture.transactions:
            with self.subTest(transaction=transaction.id):
                self.assertEqual(
                    command_echo_differences(transaction),
                    allowed_normalization_differences(transaction),
                )
                self.assertEqual(set(command_echo_differences(transaction)), {4})

    def test_prove_command_with_synthetic_log(self):
        fixture_path = Path("tests/fixtures/packets/hwp_hardware_log_2025_06_24.json")
        fixture = load_fixture_file(fixture_path)

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as log_file:
            log_path = Path(log_file.name)
            for packet in fixture.packets:
                body = " ".join(f"{byte:02X}" for byte in packet.bytes[1:-1])
                log_file.write(
                    "2025-06-24 00:00:00,000 - "
                    f"[RX]: Same  [{packet.bytes[0]:02X}][{body}]"
                    f"[{packet.bytes[-1]:02X}] {packet.label} (HEAT)\n"
                )

        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = hwp_analyze.main(
                    ["prove", "--input", str(log_path), "--fixture", str(fixture_path)]
                )
            self.assertEqual(result, 0)
            self.assertIn("Proved", output.getvalue())
        finally:
            log_path.unlink(missing_ok=True)

    def test_prove_annotations_command_with_synthetic_log(self):
        fixture_path = Path(
            "tests/fixtures/annotations/hwp_annotated_fan_control_2024_11_01.json"
        )
        fixture = load_annotation_fixture_file(fixture_path)

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as log_file:
            log_path = Path(log_file.name)
            for annotation in fixture.annotations:
                packet = annotation.packet
                body = " ".join(f"{byte:02X}" for byte in packet.bytes[1:-1])
                log_file.write(
                    f"2024-11-01 00:00:00,000 - {annotation.label} -- BEGIN\n"
                )
                log_file.write(
                    f"2024-11-01 00:00:00,001 - {annotation.label}: "
                    f"[RX]: Chg   [{packet.bytes[0]:02X}][{body}]"
                    f"[{packet.bytes[-1]:02X}] {packet.label} "
                    f"({'CONT' if packet.source == 'controller' else 'HEAT'})\n"
                )
                log_file.write(
                    f"2024-11-01 00:00:00,002 - {annotation.label} -- END\n"
                )

        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = hwp_analyze.main(
                    [
                        "prove-annotations",
                        "--input",
                        str(log_path),
                        "--fixture",
                        str(fixture_path),
                    ]
                )
            self.assertEqual(result, 0)
            self.assertIn("Proved", output.getvalue())
        finally:
            log_path.unlink(missing_ok=True)

    def test_prove_active_tx_command_with_synthetic_log(self):
        fixture_path = Path(
            "tests/fixtures/active_tx/hwp_active_tx_config5_defrost_2026_05_12.json"
        )
        fixture = load_active_tx_fixture_file(fixture_path)

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as log_file:
            log_path = Path(log_file.name)
            for transaction in fixture.transactions:
                command = transaction.command
                echo = transaction.echo
                command_body = " ".join(f"{byte:02X}" for byte in command.bytes[1:-1])
                echo_body = " ".join(f"{byte:02X}" for byte in echo.bytes[1:-1])
                log_file.write(
                    "2026-05-12 00:00:00,000 - "
                    f"[TX]: SEND  [{command.bytes[0]:02X}][{command_body}]"
                    f"[{command.bytes[-1]:02X}] {command.label} (HEAT)\n"
                )
                log_file.write(
                    "2026-05-12 00:00:01,000 - "
                    f"[RX]: Chg   [{echo.bytes[0]:02X}][{echo_body}]"
                    f"[{echo.bytes[-1]:02X}] {echo.label} (HEAT)\n"
                )

        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = hwp_analyze.main(
                    [
                        "prove-active-tx",
                        "--input",
                        str(log_path),
                        "--fixture",
                        str(fixture_path),
                    ]
                )
            self.assertEqual(result, 0)
            self.assertIn("Proved", output.getvalue())
        finally:
            log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
