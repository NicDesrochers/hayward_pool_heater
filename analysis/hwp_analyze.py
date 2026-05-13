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

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .hwp_annotation_fixtures import (
    DEFAULT_ANNOTATION_FIXTURE_DIR,
    load_annotation_fixture_file,
)
from .hwp_active_tx_fixtures import (
    DEFAULT_ACTIVE_TX_FIXTURE,
    command_echo_differences,
    load_active_tx_fixture_file,
)
from .hwp_fixtures import (
    DEFAULT_FIXTURE_DIR,
    FixtureValidationError,
    all_packets,
    fixture_index_by_bytes,
    load_fixture_file,
    load_fixture_files,
    validate_unique_packet_ids,
)
from .hwp_evidence_inventory import (
    DEFAULT_DEMO_FRAMES,
    DEFAULT_EVIDENCE_LOGS,
    build_evidence_inventory,
    inventory_field_counts,
    inventory_frame_counts,
    menu_coverage_summary,
)
from .hwp_log_parser import packet_counts, parse_annotation_file, parse_log_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze HWP packet fixtures and logs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fixtures_parser = subparsers.add_parser(
        "fixtures", help="Validate packet fixtures and print coverage."
    )
    fixtures_parser.add_argument(
        "--fixture-dir",
        default=str(DEFAULT_FIXTURE_DIR),
        help="Directory containing hwp_*.json packet fixtures.",
    )

    log_parser = subparsers.add_parser(
        "log", help="Parse an ESPHome HWP log and print a packet summary."
    )
    log_parser.add_argument("--input", required=True, help="ESPHome log path.")
    log_parser.add_argument(
        "--fixture-dir",
        default=str(DEFAULT_FIXTURE_DIR),
        help="Directory containing hwp_*.json packet fixtures.",
    )

    prove_parser = subparsers.add_parser(
        "prove",
        help="Verify every checksum-valid packet in a fixture appears in a log.",
    )
    prove_parser.add_argument("--input", required=True, help="ESPHome log path.")
    prove_parser.add_argument("--fixture", required=True, help="Fixture JSON path.")

    annotations_parser = subparsers.add_parser(
        "annotations",
        help="Parse manual annotation windows and print a summary.",
    )
    annotations_parser.add_argument("--input", required=True, help="ESPHome log path.")

    prove_annotations_parser = subparsers.add_parser(
        "prove-annotations",
        help="Verify annotation fixture windows appear in a tagged log.",
    )
    prove_annotations_parser.add_argument("--input", required=True, help="ESPHome log path.")
    prove_annotations_parser.add_argument(
        "--fixture",
        default=str(
            DEFAULT_ANNOTATION_FIXTURE_DIR
            / "hwp_annotated_fan_control_2024_11_01.json"
        ),
        help="Annotation fixture JSON path.",
    )

    active_tx_parser = subparsers.add_parser(
        "active-tx",
        help="Validate active TX command/echo fixtures and print a summary.",
    )
    active_tx_parser.add_argument(
        "--fixture",
        default=str(DEFAULT_ACTIVE_TX_FIXTURE),
        help="Active TX fixture JSON path.",
    )

    prove_active_tx_parser = subparsers.add_parser(
        "prove-active-tx",
        help="Verify active TX command/echo packets appear in a log.",
    )
    prove_active_tx_parser.add_argument("--input", required=True, help="ESPHome log path.")
    prove_active_tx_parser.add_argument(
        "--fixture",
        default=str(DEFAULT_ACTIVE_TX_FIXTURE),
        help="Active TX fixture JSON path.",
    )

    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Inventory tmp annotated logs and simulator packets against tracked fixtures.",
    )
    evidence_parser.add_argument(
        "--input",
        action="append",
        help="Annotated log path. May be repeated. Defaults to known tmp logs.",
    )
    evidence_parser.add_argument(
        "--demo-frames",
        default=str(DEFAULT_DEMO_FRAMES),
        help="Arduino simulator DemoFrames.h path.",
    )
    evidence_parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum uncovered examples to print.",
    )
    evidence_parser.add_argument(
        "--menu",
        action="store_true",
        help="Print manual menu-code coverage from the protocol map.",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            return _cmd_fixtures(Path(args.fixture_dir))
        if args.command == "log":
            return _cmd_log(Path(args.input), Path(args.fixture_dir))
        if args.command == "prove":
            return _cmd_prove(Path(args.input), Path(args.fixture))
        if args.command == "annotations":
            return _cmd_annotations(Path(args.input))
        if args.command == "prove-annotations":
            return _cmd_prove_annotations(Path(args.input), Path(args.fixture))
        if args.command == "active-tx":
            return _cmd_active_tx(Path(args.fixture))
        if args.command == "prove-active-tx":
            return _cmd_prove_active_tx(Path(args.input), Path(args.fixture))
        if args.command == "evidence":
            inputs = (
                tuple(Path(input_path) for input_path in args.input)
                if args.input
                else DEFAULT_EVIDENCE_LOGS
            )
            return _cmd_evidence(inputs, Path(args.demo_frames), args.limit, args.menu)
    except (FixtureValidationError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    return 2


def _cmd_fixtures(fixture_dir: Path) -> int:
    fixtures = load_fixture_files(fixture_dir)
    validate_unique_packet_ids(fixtures)
    packets = all_packets(fixtures)
    frame_counts = Counter(packet.frame_type for packet in packets)
    valid_count = sum(1 for packet in packets if packet.checksum_valid)
    invalid_count = len(packets) - valid_count

    print(f"Fixture files: {len(fixtures)}")
    print(f"Packets: {len(packets)} ({valid_count} valid, {invalid_count} invalid)")
    print("Frame coverage:")
    for frame_type in sorted(frame_counts):
        print(f"  {frame_type}: {frame_counts[frame_type]}")
    return 0


def _cmd_log(input_path: Path, fixture_dir: Path) -> int:
    fixtures = load_fixture_files(fixture_dir)
    fixture_index = fixture_index_by_bytes(fixtures)
    packets = parse_log_file(input_path)
    frame_counts = Counter(packet.frame_type for packet in packets)
    kind_counts = Counter(packet.kind for packet in packets)
    checksum_failures = [
        packet for packet in packets if packet.length in {9, 12} and not packet.checksum_valid
    ]
    match_count = sum(1 for packet in packets if packet.byte_key in fixture_index)

    print(f"Parsed packets: {len(packets)}")
    print(f"Fixture matches: {match_count}")
    print(f"Checksum failures: {len(checksum_failures)}")
    print("Kinds:")
    for kind, count in sorted(kind_counts.items()):
        print(f"  {kind or 'unknown'}: {count}")
    print("Frame coverage:")
    for frame_type in sorted(frame_counts):
        print(f"  {frame_type}: {frame_counts[frame_type]}")
    return 1 if checksum_failures else 0


def _cmd_prove(input_path: Path, fixture_path: Path) -> int:
    fixture = load_fixture_file(fixture_path)
    packets = parse_log_file(input_path)
    parsed_counts = packet_counts(packets)
    required_packets = [packet for packet in fixture.packets if packet.checksum_valid]
    missing = [packet for packet in required_packets if packet.byte_key not in parsed_counts]

    if missing:
        print(
            f"Missing {len(missing)} of {len(required_packets)} checksum-valid "
            f"fixture packets from {fixture.name}:"
        )
        for packet in missing:
            print(f"  {packet.id} {packet.frame_type} {packet.label}")
        return 1

    print(
        f"Proved {len(required_packets)} checksum-valid fixture packets from "
        f"{fixture.name} in {input_path}."
    )
    return 0


def _cmd_annotations(input_path: Path) -> int:
    windows = parse_annotation_file(input_path)
    packet_windows = [window for window in windows if window.packets]
    label_counts = Counter(window.label for window in windows)
    frame_counts = Counter(
        packet.frame_type
        for window in windows
        for packet in window.packets
    )

    print(f"Annotation windows: {len(windows)}")
    print(f"Windows with packets: {len(packet_windows)}")
    print("Labels:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label or '<empty>'}: {count}")
    print("Frame coverage:")
    for frame_type in sorted(frame_counts):
        print(f"  {frame_type}: {frame_counts[frame_type]}")
    return 0


def _cmd_prove_annotations(input_path: Path, fixture_path: Path) -> int:
    fixture = load_annotation_fixture_file(fixture_path)
    parsed_windows = parse_annotation_file(input_path)
    parsed_keys = {
        (window.label, packet.byte_key)
        for window in parsed_windows
        for packet in window.packets
    }
    missing = [
        annotation
        for annotation in fixture.annotations
        if (annotation.label, annotation.packet.byte_key) not in parsed_keys
    ]

    if missing:
        print(
            f"Missing {len(missing)} of {len(fixture.annotations)} annotation "
            f"fixtures from {fixture.name}:"
        )
        for annotation in missing:
            print(
                f"  {annotation.id} {annotation.label} "
                f"{annotation.packet.frame_type} {annotation.packet.label}"
            )
        return 1

    print(
        f"Proved {len(fixture.annotations)} annotation fixtures from "
        f"{fixture.name} in {input_path}."
    )
    return 0


def _cmd_active_tx(fixture_path: Path) -> int:
    fixture = load_active_tx_fixture_file(fixture_path)
    print(f"Active TX fixture: {fixture.name}")
    print(f"Transactions: {len(fixture.transactions)}")
    for transaction in fixture.transactions:
        differences = command_echo_differences(transaction)
        normalized = ", ".join(
            f"{index}:0x{command:02X}->0x{echo:02X}"
            for index, (command, echo) in sorted(differences.items())
        )
        print(
            f"  {transaction.id}: {transaction.requested_value} "
            f"{transaction.command.frame_type} normalization [{normalized or 'none'}]"
        )
    return 0


def _cmd_prove_active_tx(input_path: Path, fixture_path: Path) -> int:
    fixture = load_active_tx_fixture_file(fixture_path)
    parsed_packets = parse_log_file(input_path)
    parsed_counts = packet_counts(parsed_packets)
    missing = []
    for transaction in fixture.transactions:
        if transaction.command.byte_key not in parsed_counts:
            missing.append((transaction.id, "command", transaction.command))
        if transaction.echo.byte_key not in parsed_counts:
            missing.append((transaction.id, "echo", transaction.echo))

    if missing:
        print(
            f"Missing {len(missing)} active TX packet(s) from "
            f"{fixture.name}:"
        )
        for transaction_id, role, packet in missing:
            print(f"  {transaction_id} {role} {packet.frame_type} {packet.label}")
        return 1

    print(
        f"Proved {len(fixture.transactions)} active TX transaction(s) from "
        f"{fixture.name} in {input_path}."
    )
    return 0


def _cmd_evidence(
    input_paths: tuple[Path, ...],
    demo_frames_path: Path,
    limit: int,
    include_menu: bool,
) -> int:
    inventory = build_evidence_inventory(input_paths, demo_frames_path)
    packet_windows = inventory.packet_windows
    covered_windows = inventory.covered_windows
    uncovered_windows = inventory.uncovered_windows
    covered_demo = inventory.covered_demo_packets
    uncovered_demo = inventory.uncovered_demo_packets

    print(f"Evidence logs scanned: {len(input_paths) - len(inventory.missing_logs)}")
    if inventory.missing_logs:
        print(f"Missing logs: {len(inventory.missing_logs)}")
        for path in inventory.missing_logs:
            print(f"  {path}")
    print(f"Annotation windows: {len(inventory.windows)}")
    print(f"Windows with packets: {len(packet_windows)}")
    print(f"Tracked window matches: {len(covered_windows)}")
    print(f"Uncovered packet windows: {len(uncovered_windows)}")

    print(f"Demo packets: {len(inventory.demo_packets)}")
    print(f"Tracked demo matches: {len(covered_demo)}")
    print(f"Uncovered demo packets: {len(uncovered_demo)}")
    if inventory.missing_demo_frames:
        print(f"Missing demo frames: {demo_frames_path}")

    print("Field coverage:")
    for field, counts in sorted(inventory_field_counts(inventory.windows).items()):
        print(
            f"  {field}: {counts['packet_windows']}/{counts['windows']} "
            f"packet windows, {counts['covered']} tracked"
        )

    print("Frame coverage:")
    for frame_type, count in sorted(
        inventory_frame_counts(inventory.windows, inventory.demo_packets).items()
    ):
        print(f"  {frame_type}: {count}")

    if include_menu:
        print("Menu coverage:")
        for menu, (entry, annotation_count, has_demo) in sorted(
            menu_coverage_summary(inventory).items()
        ):
            evidence = []
            if annotation_count:
                evidence.append(f"annotations={annotation_count}")
            if has_demo:
                evidence.append("demo=yes")
            print(
                f"  {menu}: {entry.frame} {entry.location}, "
                f"{entry.implementation_status}, {entry.safety_status}, "
                f"{', '.join(evidence) or 'no scanned evidence'}"
            )

    if limit > 0 and uncovered_windows:
        print("Uncovered annotated examples:")
        for window in uncovered_windows[:limit]:
            frames = ",".join(window.frame_types) or "none"
            print(
                f"  {window.log_path}:{window.start_line}-{window.end_line} "
                f"{window.label} [{frames}]"
            )

    if limit > 0 and uncovered_demo:
        print("Uncovered demo examples:")
        for packet in uncovered_demo[:limit]:
            print(
                f"  {packet.identifier} {packet.label} {packet.frame_type} "
                f"checksum={'ok' if packet.checksum_valid else 'bad'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
