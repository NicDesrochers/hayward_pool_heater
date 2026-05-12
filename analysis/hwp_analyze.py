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
from .hwp_fixtures import (
    DEFAULT_FIXTURE_DIR,
    FixtureValidationError,
    all_packets,
    fixture_index_by_bytes,
    load_fixture_file,
    load_fixture_files,
    validate_unique_packet_ids,
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


if __name__ == "__main__":
    raise SystemExit(main())
