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
import argparse
import json
import struct
import tempfile
import time
import unittest
from pathlib import Path

from analysis import hwp_analyze
from analysis import hwp_web_capture
from analysis.TagEntry import TagEntry, TagType
from analysis.hwp_active_tx_fixtures import (
    allowed_normalization_differences,
    command_echo_differences,
    load_active_tx_fixture_file,
)
from analysis.hwp_logs_annotator import (
    build_parser,
    _format_age,
    _graph_checkbox_label,
    format_profiles,
    is_restart_button_entity,
    setup_profile_interactive,
)
from analysis.hwp_sim_orchestrate import (
    EntitySummary,
    build_parser as build_sim_orchestrator_parser,
    entity_matches,
    find_entity,
    load_env_file,
    prepare_args,
    transcript_event_json,
)
from analysis.hwp_annotation_fixtures import load_annotation_fixture_file
from analysis.hwp_fixtures import (
    fixture_index_by_bytes,
    load_fixture_file,
    load_fixture_files,
)
from analysis.hwp_field_dashboard import (
    DashboardState,
    GraphState,
    decode_packet_fields,
    graph_group_for_field,
    graph_groups,
)
from analysis.hwp_evidence_inventory import (
    build_evidence_inventory,
    inventory_field_counts,
    menu_coverage_summary,
    summarize_demo_frames,
)
from analysis.hwp_menu_map import MENU_BY_CODE, MENU_BY_FIELD, validate_menu_packet_map
from analysis.hwp_log_parser import (
    parse_annotation_windows,
    parse_log_line,
    parse_log_lines,
    strip_ansi,
)
from analysis.hwp_packet_view import PacketViewState, build_packet_view
from analysis.hwp_tool_config import (
    ToolConfigError,
    ToolConnectionConfig,
    load_profile_file,
    require_connection_config,
    resolve_connection_config,
    save_profile_file,
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


class ButtonInfo:
    def __init__(
        self,
        *,
        name: str = "",
        object_id: str = "",
        device_class: str = "",
    ):
        self.name = name
        self.object_id = object_id
        self.device_class = device_class


class SwitchInfo:
    def __init__(self):
        self.name = "Restart"
        self.object_id = "restart"
        self.device_class = "restart"


class DummyEntityState:
    def __init__(self, key, state):
        self.key = key
        self.state = state


class HwpSimulatorOrchestratorTest(unittest.TestCase):
    def test_entity_matching_uses_name_or_object_id(self):
        entity = EntitySummary(
            key=12,
            name="HWP Simulator Command",
            object_id="hwp_sim_command",
            kind="TextInfo",
        )

        self.assertTrue(entity_matches(entity, "command"))
        self.assertTrue(entity_matches(entity, "sim_command"))
        self.assertFalse(entity_matches(entity, "playbook"))

    def test_find_entity_returns_first_matching_entity(self):
        entities = [
            EntitySummary(1, "Other", "other", "SensorInfo"),
            EntitySummary(2, "HWP Simulator Playbook", "hwp_sim_playbook", "SelectInfo"),
        ]

        found = find_entity(entities, "playbook")

        self.assertIsNotNone(found)
        self.assertEqual(found.key, 2)

    def test_transcript_parser_accepts_firmware_node(self):
        args = build_sim_orchestrator_parser().parse_args(
            [
                "--device",
                "sim.local",
                "transcript",
                "--duration",
                "1.5",
                "--out",
                "capture.jsonl",
                "--firmware-device",
                "heater.local",
            ]
        )

        self.assertEqual(args.action, "transcript")
        self.assertEqual(args.duration, 1.5)
        self.assertEqual(args.firmware_device, "heater.local")

    def test_connection_defaults_can_load_repo_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "SIMULATOR_NET_NAME=simulator.local",
                        "SIMULATOR_API_KEY='sim-secret'",
                        "TEST_DEVICE_NET_NAME=test.local",
                        "TEST_DEVICE_API_KEY=test-secret",
                    ]
                ),
                encoding="utf-8",
            )

            args = build_sim_orchestrator_parser().parse_args(
                ["--env-file", str(env_file), "transcript", "--duration", "1", "--out", "-"]
            )
            prepare_args(args)

            self.assertEqual(args.device, "simulator.local")
            self.assertEqual(args.api_key, "sim-secret")
            self.assertIsNone(args.firmware_device)

    def test_connection_defaults_fill_firmware_key_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "SIMULATOR_NET_NAME=simulator.local\n"
                "TEST_DEVICE_NET_NAME=test.local\n"
                "TEST_DEVICE_API_KEY=test-secret\n",
                encoding="utf-8",
            )

            args = build_sim_orchestrator_parser().parse_args(
                [
                    "--env-file",
                    str(env_file),
                    "transcript",
                    "--duration",
                    "1",
                    "--out",
                    "-",
                    "--firmware-device",
                    "",
                ]
            )
            prepare_args(args)

            self.assertEqual(args.firmware_device, "test.local")
            self.assertEqual(args.firmware_api_key, "test-secret")

    def test_empty_device_fails_before_zeroconf(self):
        args = build_sim_orchestrator_parser().parse_args(
            ["--env-file", "/does/not/exist", "--device", "", "command", "step"]
        )

        with self.assertRaisesRegex(SystemExit, "Missing simulator device address"):
            prepare_args(args)

    def test_load_env_file_strips_quotes_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "# local secrets\nSIMULATOR_NET_NAME=\"sim.local\"\nSIMULATOR_API_KEY='secret'\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_env_file(env_file),
                {"SIMULATOR_NET_NAME": "sim.local", "SIMULATOR_API_KEY": "secret"},
            )

    def test_transcript_event_json_includes_entity_metadata(self):
        entity = EntitySummary(
            key=42,
            name="HWP Simulator Last RX Frame",
            object_id="hwp_sim_last_rx_frame",
            kind="TextSensorInfo",
        )

        line = transcript_event_json("sim.local", DummyEntityState(42, "rx 0x85"), {42: entity})
        payload = json.loads(line)

        self.assertEqual(payload["event"], "entity.state")
        self.assertEqual(payload["device"], "sim.local")
        self.assertEqual(payload["name"], "HWP Simulator Last RX Frame")
        self.assertEqual(payload["state"], "rx 0x85")


COND2_TEMPERATURE_LINE = (
    "[2026-05-13 06:40:34][D][hwp.pk:404][RX]: Chg   "
    "[D2][B1 11 5E 52 45 46 00 64 00 00][33] COND_2    "
    "(HEAT) ( 5.0s) 11.0C(0x52), t04 Coil  5.0C(0x46), "
    "t06 Exhaust  4.5C(0x45), 4?? 20.0C(0x64)"
)
CONFIG1_LINE = (
    "[2026-05-13 16:00:20][V][hwp.pk:413][RX]: Same  "
    "[81][B1 1A 72 51 72 3D 3D 3D 3D 32][A7] CONFIG_1  (HEAT)"
)
CONFIG3_LINE = (
    "[2026-05-13 16:00:16][V][hwp.pk:413][RX]: Same  "
    "[83][B1 46 23 0A 23 23 4C 82 46 8C][8D] CONFIG_3  (HEAT)"
)
CONFIG4_LINE = (
    "[2026-05-13 16:00:22][V][hwp.pk:413][RX]: Same  "
    "[84][B1 8C 5A 50 50 64 78 00 00 78][0F] CONFIG_4  (HEAT)"
)
CONFIG5_LINE = (
    "[2026-05-13 16:00:23][V][hwp.pk:413][RX]: Same  "
    "[85][B1 00 06 1E 16 00 08 00 00 CD][45] CONFIG_5  (HEAT)"
)
COND1_LINE = (
    "[2026-05-13 16:00:18][V][hwp.pk:413][RX]: Same  "
    "[D1][B1 05 00 00 00 00 78 5E 56 1B][CE] COND_1    (HEAT)"
)
COND1B_LINE = (
    "[2026-05-13 16:00:20][V][hwp.pk:413][RX]: Same  "
    "[D1][B1 00 00 0F 00 00 78 5E 56 1B][D8] COND_1B   (HEAT)"
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
    def test_web_capture_parses_viewport_sizes(self):
        sizes = hwp_web_capture.parse_size_spec("phone=390x844,tablet=768x1024")

        self.assertEqual([size.name for size in sizes], ["phone", "tablet"])
        self.assertEqual((sizes[1].width, sizes[1].height), (768, 1024))
        self.assertEqual(sizes[1].filename, "hwp-web-tablet.png")
        self.assertEqual(
            hwp_web_capture.selected_readme_path(Path("analysis/screenshots"), sizes, "tablet"),
            Path("analysis/screenshots/hwp-web-tablet.png"),
        )

    def test_web_capture_dry_run_outputs_expected_paths(self):
        sizes = hwp_web_capture.parse_size_spec("tablet=768x1024")
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs = hwp_web_capture.capture_screenshots(
                base_url="http://device.local/hwp",
                out_dir=Path(temp_dir),
                sizes=sizes,
                wait_ms=0,
                dry_run=True,
            )

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].name, "hwp-web-tablet.png")

    def test_web_capture_validates_png_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "capture.png"
            png_header = (
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 768, 1024)
            )
            path.write_bytes(png_header + b"\x08\x02\x00\x00\x00" + (b"x" * 2048))

            self.assertEqual(hwp_web_capture.png_dimensions(path), (768, 1024))
            hwp_web_capture.validate_png(path, 768, 1024)

            with self.assertRaises(ValueError):
                hwp_web_capture.validate_png(path, 390, 844)

    def test_web_capture_help_and_dry_run_command(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = hwp_web_capture.main(
                [
                    "--base-url",
                    "http://device.local/hwp",
                    "--out-dir",
                    "analysis/screenshots",
                    "--sizes",
                    "tablet=768x1024",
                    "--readme-size",
                    "tablet",
                    "--dry-run",
                ]
            )

        self.assertEqual(result, 0)
        text = output.getvalue()
        self.assertIn("analysis/screenshots/hwp-web-tablet.png", text)
        self.assertIn("README capture: analysis/screenshots/hwp-web-tablet.png", text)

    def test_connection_profiles_round_trip_without_printing_secret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "hwp-tools.json"
            save_profile_file(
                profile_path,
                {
                    "pool": {
                        "address": "pool.local",
                        "api_key": "secret-key",
                        "port": 6053,
                        "log_prefix": "POOL",
                        "default_delay": 2.5,
                        "log_level": "VERBOSE",
                        "dump_config": False,
                    }
                },
                default_profile="pool",
            )
            payload = load_profile_file(profile_path)

        self.assertEqual(payload["default_profile"], "pool")
        self.assertEqual(payload["profiles"]["pool"]["address"], "pool.local")
        config = ToolConnectionConfig(api_key="secret-key")
        self.assertEqual(config.redacted()["api_key"], "<set>")
        self.assertNotIn("secret-key", str(config.redacted()))

    def test_connection_resolution_precedence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "hwp-tools.json"
            save_profile_file(
                profile_path,
                {
                    "pool": {
                        "address": "profile.local",
                        "api_key": "profile-key",
                        "port": 6054,
                        "log_prefix": "PROFILE",
                        "default_delay": 3.0,
                        "log_level": "INFO",
                        "dump_config": True,
                    }
                },
                default_profile="pool",
            )
            args = argparse.Namespace(
                yaml="legacy.yaml",
                profile=None,
                profile_file=str(profile_path),
                device="cli.local",
                api_key=None,
                port=None,
                log_prefix=None,
                delay=None,
                default_delay=None,
                log_level=None,
                dump_config=None,
            )
            env = {
                "HWP_API_KEY": "env-key",
                "HWP_LOG_LEVEL": "DEBUG",
                "HWP_DUMP_CONFIG": "false",
            }
            config = resolve_connection_config(
                args,
                environ=env,
                yaml_loader=lambda _path: {
                    "esphome": {"name": "legacy"},
                    "api": {"encryption": {"key": "yaml-key"}},
                },
            )

        self.assertEqual(config.address, "cli.local")
        self.assertEqual(config.api_key, "env-key")
        self.assertEqual(config.port, 6054)
        self.assertEqual(config.log_prefix, "PROFILE")
        self.assertEqual(config.log_level, "DEBUG")
        self.assertFalse(config.dump_config)

    def test_connection_requires_address(self):
        with self.assertRaises(ToolConfigError):
            require_connection_config(ToolConnectionConfig())

    def test_hwp_logs_annotator_help_is_yaml_free(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stdout(io.StringIO()):
                parser.parse_args(["--help"])
        self.assertEqual(context.exception.code, 0)

    def test_restart_button_detection_uses_button_entities_only(self):
        self.assertTrue(is_restart_button_entity(ButtonInfo(device_class="restart")))
        self.assertTrue(is_restart_button_entity(ButtonInfo(name="Device Reboot")))
        self.assertTrue(is_restart_button_entity(ButtonInfo(object_id="heater_restart")))
        self.assertFalse(is_restart_button_entity(ButtonInfo(name="Refresh Logs")))
        self.assertFalse(is_restart_button_entity(SwitchInfo()))

    def test_dashboard_age_formatting(self):
        self.assertEqual(_format_age(None), "")
        self.assertEqual(_format_age(4.9), "4s")
        self.assertEqual(_format_age(65), "1m 05s")
        self.assertEqual(_format_age(3661), "1h 01m")

    def test_annotator_setup_creates_profile_without_echoing_secret(self):
        answers = iter(
            [
                "pool",
                "heater.local",
                "6053",
                "POOL",
                "1.5",
                "verbose",
                "n",
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "hwp-tools.json"
            config = setup_profile_interactive(
                ToolConnectionConfig(),
                profile_path,
                input_func=lambda _prompt: next(answers),
                secret_func=lambda _prompt: "setup-secret",
            )
            listing = format_profiles(profile_path)
            payload = load_profile_file(profile_path)

        self.assertEqual(config.name, "pool")
        self.assertEqual(config.address, "heater.local")
        self.assertEqual(config.api_key, "setup-secret")
        self.assertEqual(config.log_level, "VERBOSE")
        self.assertFalse(config.dump_config)
        self.assertEqual(payload["default_profile"], "pool")
        self.assertIn("api_key=<set>", listing)
        self.assertNotIn("setup-secret", listing)

    def test_setup_allows_new_profile_name_from_cli(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            args = argparse.Namespace(
                yaml=None,
                profile="new-profile",
                profile_file=str(Path(temp_dir) / "hwp-tools.json"),
                device="heater.local",
                api_key=None,
                port=None,
                log_prefix=None,
                delay=None,
                default_delay=None,
                log_level=None,
                dump_config=None,
            )
            config = resolve_connection_config(args, allow_missing_profile=True)

        self.assertEqual(config.name, "new-profile")
        self.assertEqual(config.address, "heater.local")

    def test_gui_style_tag_entry_start_and_duration_windows(self):
        start = time_tuple = time.localtime(1_700_000_000)
        change = TagEntry.from_params(
            TagType.CHANGE, text="F02 to 41.5", start_time=start
        )
        event = TagEntry.from_params(
            TagType.EVENT, delay=10, text="compressor start", start_time=start
        )

        self.assertTrue(TagType.CHANGE.has_start_button)
        self.assertFalse(TagType.EVENT.has_start_button)
        self.assertEqual(change.get_start_time(), time_tuple)
        self.assertEqual(time.mktime(event.get_start_time()), 1_699_999_990)

    def test_tag_entry_search_filters_number_integer_and_temperatures(self):
        line = (
            "[RX]: Same  [84][B1 8C 5A 50 50 64 78 17 00 78][26] "
            "CONFIG_4  (HEAT)"
        )
        number = TagEntry.from_params(TagType.NUMBER, value="23")
        integer = TagEntry.from_params(TagType.INTEGER, value="23")
        extended = TagEntry.from_params(TagType.TEMPERATURE_EXTENDED, value="40")
        normal = TagEntry.from_params(TagType.TEMPERATURE, value="20")

        self.assertTrue(number.filter(line)[0])
        self.assertTrue(integer.filter(line)[0])
        self.assertTrue(extended.filter(line)[0])
        self.assertTrue(normal.filter(line)[0])

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

    def test_packet_view_model_marks_fixtures_menu_fields_and_checksum(self):
        fixtures = load_fixture_files()
        index = fixture_index_by_bytes(fixtures)
        packet = parse_log_line(LONG_CONFIG_LINE)
        view = build_packet_view(packet, index)

        self.assertEqual(view.checksum_status, "valid")
        self.assertTrue(view.fixture_matches)
        menu_cells = [
            cell for cell in view.cells if any(field.menu == "F01" for field in cell.menu_fields)
        ]
        self.assertEqual(len(menu_cells), 1)
        self.assertIn("known-menu", menu_cells[0].tags)

        invalid_packet = parse_log_line(LONG_CONFIG_LINE.replace("[98]", "[99]"))
        invalid_view = build_packet_view(invalid_packet, index)
        self.assertEqual(invalid_view.checksum_status, "invalid")
        self.assertIn("checksum-invalid", invalid_view.cells[-1].tags)

    def test_packet_view_state_marks_changed_bytes_by_frame_source_length(self):
        state = PacketViewState()
        first = parse_log_line(LONG_CONFIG_LINE)
        second = parse_log_line(LONG_CONFIG_LINE.replace("B1 16", "B1 26").replace("[98]", "[A8]"))
        state.build(first)
        view = state.build(second)

        changed_indexes = {cell.index for cell in view.cells if cell.changed}
        self.assertIn(2, changed_indexes)
        self.assertIn(11, changed_indexes)

    def test_packet_view_model_handles_tx_and_short_frames(self):
        tx_packet = parse_log_line(TX_COMMAND_LINE)
        tx_view = build_packet_view(tx_packet)
        short_packet = parse_log_line(SHORT_CONDITION_LINE)
        short_view = build_packet_view(short_packet)

        self.assertEqual(tx_view.packet.source, "controller")
        self.assertEqual(short_view.packet.length, 9)
        self.assertEqual(short_view.cells[-1].role, "checksum")

    def test_packet_view_model_marks_known_passive_condition_fields(self):
        packet = parse_log_line(COND2_TEMPERATURE_LINE)
        view = build_packet_view(packet)

        known_fields = {
            field.field
            for cell in view.cells
            for field in cell.known_fields
        }
        self.assertEqual(packet.frame_type, "0xD2")
        self.assertIn("t03_outlet", known_fields)
        self.assertIn("t04_coil", known_fields)
        self.assertIn("t06_exhaust", known_fields)
        self.assertIn("t_aux_cond2", known_fields)
        self.assertIn("known-field", view.cells[4].tags)
        self.assertNotEqual(view.summary, "no known packet fields")

    def test_field_dashboard_decodes_known_packet_values(self):
        packets = [
            parse_log_line(line)
            for line in (
                CONFIG1_LINE,
                LONG_CONFIG_LINE,
                CONFIG3_LINE,
                CONFIG4_LINE,
                CONFIG5_LINE,
                COND1_LINE,
                COND1B_LINE,
                COND2_TEMPERATURE_LINE,
            )
        ]
        observations = {
            observation.field_id: observation
            for packet in packets
            for observation in decode_packet_fields(packet)
        }

        self.assertEqual(observations["r01_setpoint_cooling"].decoded_value, 27.0)
        self.assertEqual(observations["r02_setpoint_heating"].decoded_value, 10.5)
        self.assertEqual(observations["f01_fan_mode"].decoded_value, "High Speed")
        self.assertEqual(
            observations["f10_fan_speed_control_temp"].decoded_value,
            "Coil Temperature",
        )
        self.assertEqual(observations["r09_max_cooling_setpoint"].decoded_value, 35.0)
        self.assertEqual(observations["f02_fan_high_speed_cool_setpoint"].decoded_value, 40.0)
        self.assertEqual(observations["f08_fan_low_speed_running_time"].decoded_value, 0)
        self.assertEqual(observations["f11_speed_control_module"].decoded_value, "Enabled")
        self.assertEqual(observations["d06_defrost_eco_mode"].decoded_value, "Normal")
        self.assertEqual(observations["t02_inlet"].decoded_value, 13.0)
        self.assertTrue(observations["s02_water_flow"].decoded_value)
        self.assertEqual(observations["t03_outlet"].decoded_value, 11.0)
        self.assertEqual(observations["t04_coil"].display_value, "5.0")
        self.assertEqual(observations["t06_exhaust"].unit, "C")

    def test_dashboard_state_ignores_invalid_checksum_and_marks_changes(self):
        state = DashboardState()
        first = parse_log_line(COND2_TEMPERATURE_LINE)
        changed = parse_log_line(COND2_TEMPERATURE_LINE.replace("52 45 46", "53 45 46").replace("[33]", "[34]"))
        invalid = parse_log_line(COND2_TEMPERATURE_LINE.replace("[33]", "[34]"))

        first_observations = state.update(first)
        invalid_observations = state.update(invalid)
        changed_observations = state.update(changed)

        self.assertGreater(len(first_observations), 0)
        self.assertEqual(invalid_observations, ())
        changed_fields = {
            observation.field_id
            for observation in changed_observations
            if observation.changed
        }
        self.assertIn("t03_outlet", changed_fields)

    def test_graph_state_records_numeric_values_and_trims_history(self):
        graph = GraphState(max_points=2)
        packet = parse_log_line(COND2_TEMPERATURE_LINE)
        observations = decode_packet_fields(packet)
        graph.update(observations)
        graph.update(observations)
        graph.update(observations)

        self.assertIn("t03_outlet", graph.history)
        self.assertEqual(len(graph.history["t03_outlet"]), 2)
        self.assertNotIn(
            "f10_fan_speed_control_temp",
            graph.history,
        )

    def test_graph_groups_split_ranges_and_use_human_labels(self):
        groups = {group.group_id: group for group in graph_groups()}

        self.assertIn("temperatures", groups)
        self.assertIn("setpoints", groups)
        self.assertIn("low_range", groups)
        self.assertEqual(graph_group_for_field("t04_coil"), "temperatures")
        self.assertEqual(graph_group_for_field("r09_max_cooling_setpoint"), "setpoints")
        self.assertEqual(graph_group_for_field("r04_return_diff_cooling"), "low_range")
        self.assertEqual(_graph_checkbox_label("t04_coil"), "Coil")
        self.assertEqual(
            _graph_checkbox_label("r09_max_cooling_setpoint"),
            "R09 Max cool",
        )
        self.assertEqual(
            _graph_checkbox_label("f12_min_fan_voltage_pct"),
            "F12 Min fan voltage",
        )

    def test_defrost_demo_fixture_pins_menu_expectations_and_pairs(self):
        fixture = load_fixture_file(
            "tests/fixtures/packets/hwp_defrost_demo_command_contracts.json"
        )
        expectations = {(expectation.menu, expectation.value) for expectation in fixture.menu_expectations}
        self.assertIn(("D01", -7.5), expectations)
        self.assertIn(("D01", -7.0), expectations)
        self.assertIn(("D05", 10.0), expectations)
        self.assertIn(("D05", 5.0), expectations)
        self.assertIn(("D06", "Eco"), expectations)
        self.assertIn(("D06", "Normal"), expectations)

        pairs = {pair.id: pair for pair in fixture.menu_pairs}
        self.assertEqual(pairs["demo-pair-d01-neg-7-0-to-neg-7-5"].changed_byte_indexes, (3,))
        self.assertEqual(pairs["demo-pair-d05-3-0-to-10-0"].changed_byte_indexes, (3,))
        self.assertEqual(pairs["demo-pair-d06-normal-to-eco"].changed_byte_indexes, (2,))
        for packet in fixture.packets:
            with self.subTest(packet=packet.id):
                self.assertTrue(packet.checksum_valid)

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

    def test_evidence_inventory_tracks_covered_annotation_windows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "annotated.log"
            log_path.write_text("".join(ANNOTATED_WINDOW_LINES), encoding="utf-8")
            inventory = build_evidence_inventory(
                (log_path,),
                Path(temp_dir) / "missing_DemoFrames.h",
            )

        self.assertEqual(len(inventory.windows), 1)
        self.assertEqual(len(inventory.packet_windows), 1)
        self.assertEqual(len(inventory.covered_windows), 1)
        self.assertTrue(inventory.missing_demo_frames)
        field_counts = inventory_field_counts(inventory.windows)
        self.assertEqual(field_counts["F02"]["windows"], 1)
        self.assertEqual(field_counts["F02"]["covered"], 1)

    def test_demo_frame_inventory_cross_checks_tracked_packets(self):
        demo_text = """
const uint8_t data_0[12] = {0x84, 0xB1, 0x8F, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x12};
const uint8_t data_1[12] = {0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
static const packet_t p_0 = packet_t(true, 12, std::string("F02 41.5"), data_0, std::string(""));
static const packet_t p_1 = packet_t(false, 12, std::string("base conf"), data_1, std::string(""));
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_path = Path(temp_dir) / "DemoFrames.h"
            demo_path.write_text(demo_text, encoding="utf-8")
            packets = summarize_demo_frames(demo_path)

        self.assertEqual(len(packets), 2)
        self.assertTrue(all(packet.checksum_valid for packet in packets))
        self.assertTrue(all(packet.is_covered for packet in packets))
        self.assertEqual(packets[0].frame_type, "0x84")
        self.assertTrue(packets[0].controllable)

    def test_menu_packet_map_validates_and_pins_core_mappings(self):
        validate_menu_packet_map()
        expectations = {
            "F13": ("f13_max_fan_voltage_pct", "0x82", 10, None),
            "F12": ("f12_min_fan_voltage_pct", "0x81", 10, None),
            "F02": ("f02_fan_high_speed_cool_setpoint", "0x84", 2, None),
            "F09": ("f09_fan_stop_low_speed_running_time", "0x84", 9, None),
            "F11": ("f11_speed_control_module", "0x85", 2, 3),
            "D06": ("d06_defrost_eco_mode", "0x85", 2, 6),
            "U02": ("u02_pulses_per_liter", "0x85", 10, None),
            "R09": ("r09_max_cooling_setpoint", "0x83", 8, None),
            "S02": ("s02_water_flow", "0xD1", 4, 1),
        }
        for menu, expected in expectations.items():
            with self.subTest(menu=menu):
                field, frame, byte_index, bit_index = expected
                entry = MENU_BY_CODE[menu]
                self.assertEqual(entry.field, field)
                self.assertEqual(entry.frame, frame)
                self.assertEqual(entry.byte_index, byte_index)
                self.assertEqual(entry.bit_index, bit_index)

    def test_menu_packet_map_covers_implemented_helper_fields(self):
        implemented_fields = {
            "d01_defrost_start",
            "d02_defrost_end",
            "d03_defrosting_cycle_time_minutes",
            "d04_max_defrost_time_minutes",
            "d05_min_economy_defrost_time_minutes",
            "d06_defrost_eco_mode",
            "f01_fan_mode",
            "f02_fan_high_speed_cool_setpoint",
            "f03_fan_low_speed_temp_in_cooling_set_point",
            "f04_fan_stop_temp_in_cooling_set_point",
            "f05_fan_high_speed_temp_in_heating_set_point",
            "f06_fan_low_speed_temp_in_heating_set_point",
            "f07_fan_stop_temp_in_heating_set_point",
            "f08_fan_low_speed_running_time",
            "f09_fan_stop_low_speed_running_time",
            "f10_fan_speed_control_temp",
            "f11_speed_control_module",
            "f12_min_fan_voltage_pct",
            "f13_max_fan_voltage_pct",
            "h02_mode_restrictions",
            "r01_setpoint_cooling",
            "r02_setpoint_heating",
            "r03_setpoint_auto",
            "r04_return_diff_cooling",
            "r05_shutdown_temp_diff_when_cooling",
            "r06_return_diff_heating",
            "r07_shutdown_diff_heating",
            "r08_min_cool_setpoint",
            "r09_max_cooling_setpoint",
            "r10_min_heating_setpoint",
            "r11_max_heating_setpoint",
            "u01_flow_meter",
            "u02_pulses_per_liter",
        }
        self.assertEqual(implemented_fields - set(MENU_BY_FIELD), set())

    def test_menu_coverage_summary_finds_annotation_and_demo_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "annotated.log"
            log_path.write_text("".join(ANNOTATED_WINDOW_LINES), encoding="utf-8")
            demo_path = Path(temp_dir) / "DemoFrames.h"
            demo_path.write_text(
                """
const uint8_t data_0[12] = {0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x3C, 0x84, 0x46, 0x8C, 0x7F};
static const packet_t p_0 = packet_t(true, 12, std::string("r09=36"), data_0, std::string(""));
""",
                encoding="utf-8",
            )
            inventory = build_evidence_inventory((log_path,), demo_path)

        summary = menu_coverage_summary(inventory)
        self.assertEqual(summary["F02"][1], 1)
        self.assertTrue(summary["R09"][2])

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
