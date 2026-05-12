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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "packets"
SUPPORTED_LENGTHS = {9, 12}
REQUIRED_PACKET_KEYS = {
    "id",
    "source_id",
    "label",
    "source",
    "length",
    "frame_type",
    "bytes",
    "checksum_valid",
    "expected_checksum",
    "notes",
}


class FixtureValidationError(ValueError):
    """Raised when a tracked packet fixture is malformed."""


@dataclass(frozen=True)
class PacketFixture:
    fixture_name: str
    id: str
    source_id: str
    label: str
    source: str
    length: int
    frame_type: str
    bytes: tuple[int, ...]
    checksum_valid: bool
    expected_checksum: int
    notes: str

    @property
    def byte_key(self) -> tuple[int, ...]:
        return self.bytes


@dataclass(frozen=True)
class FixtureFile:
    path: Path
    schema_version: int
    source: str
    provenance: str
    packets: tuple[PacketFixture, ...]

    @property
    def name(self) -> str:
        return self.path.name


def parse_hex_byte(value: str) -> int:
    if not isinstance(value, str):
        raise FixtureValidationError(f"{value!r} is not a hex string")
    if not value.startswith("0x") or len(value) != 4:
        raise FixtureValidationError(f"{value!r} is not formatted as 0xNN")
    parsed = int(value, 16)
    if parsed < 0 or parsed > 0xFF:
        raise FixtureValidationError(f"{value!r} is outside byte range")
    return parsed


def format_hex_byte(value: int) -> str:
    if value < 0 or value > 0xFF:
        raise FixtureValidationError(f"{value!r} is outside byte range")
    return f"0x{value:02X}"


def calculate_checksum(data: Iterable[int], length: int | None = None) -> int:
    values = list(data)
    packet_length = len(values) if length is None else length
    if packet_length == 9:
        return sum(values[1 : packet_length - 1]) % 256
    if packet_length == 12:
        return sum(values[: packet_length - 1]) % 256
    raise FixtureValidationError(f"unsupported fixture length {packet_length}")


def is_checksum_valid(data: Iterable[int], length: int | None = None) -> bool:
    values = list(data)
    packet_length = len(values) if length is None else length
    if packet_length not in SUPPORTED_LENGTHS or len(values) < packet_length:
        return False
    return values[packet_length - 1] == calculate_checksum(values, packet_length)


def load_fixture_file(path: Path | str) -> FixtureFile:
    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as fixture_file:
        raw_fixture = json.load(fixture_file)

    schema_version = raw_fixture.get("schema_version")
    source = raw_fixture.get("source")
    provenance = raw_fixture.get("provenance")
    raw_packets = raw_fixture.get("packets")

    if schema_version != 1:
        raise FixtureValidationError(
            f"{fixture_path}: unsupported schema_version {schema_version!r}"
        )
    if not isinstance(source, str) or not source:
        raise FixtureValidationError(f"{fixture_path}: missing source")
    if not isinstance(provenance, str) or not provenance:
        raise FixtureValidationError(f"{fixture_path}: missing provenance")
    if not isinstance(raw_packets, list) or not raw_packets:
        raise FixtureValidationError(f"{fixture_path}: missing packets")

    packets = tuple(_parse_packet(fixture_path.name, packet) for packet in raw_packets)
    return FixtureFile(
        path=fixture_path,
        schema_version=schema_version,
        source=source,
        provenance=provenance,
        packets=packets,
    )


def load_fixture_files(fixture_dir: Path | str = DEFAULT_FIXTURE_DIR) -> tuple[FixtureFile, ...]:
    paths = sorted(Path(fixture_dir).glob("hwp_*.json"))
    return tuple(load_fixture_file(path) for path in paths)


def all_packets(fixtures: Iterable[FixtureFile]) -> tuple[PacketFixture, ...]:
    return tuple(packet for fixture in fixtures for packet in fixture.packets)


def fixture_index_by_bytes(
    fixtures: Iterable[FixtureFile],
) -> dict[tuple[int, ...], list[PacketFixture]]:
    index: dict[tuple[int, ...], list[PacketFixture]] = {}
    for packet in all_packets(fixtures):
        index.setdefault(packet.byte_key, []).append(packet)
    return index


def validate_unique_packet_ids(fixtures: Iterable[FixtureFile]) -> None:
    seen: set[str] = set()
    for packet in all_packets(fixtures):
        if packet.id in seen:
            raise FixtureValidationError(f"duplicate packet id {packet.id!r}")
        seen.add(packet.id)


def _parse_packet(fixture_name: str, packet: dict) -> PacketFixture:
    missing = REQUIRED_PACKET_KEYS - set(packet)
    if missing:
        raise FixtureValidationError(
            f"{fixture_name}: packet {packet.get('id')!r} missing {sorted(missing)}"
        )

    packet_id = packet["id"]
    source_id = packet["source_id"]
    label = packet["label"]
    source = packet["source"]
    length = packet["length"]
    frame_type = packet["frame_type"]
    checksum_valid = packet["checksum_valid"]
    notes = packet["notes"]

    if source not in {"heater", "controller"}:
        raise FixtureValidationError(f"{fixture_name}: {packet_id}: bad source")
    if length not in SUPPORTED_LENGTHS:
        raise FixtureValidationError(f"{fixture_name}: {packet_id}: bad length")
    if not isinstance(checksum_valid, bool):
        raise FixtureValidationError(
            f"{fixture_name}: {packet_id}: checksum_valid must be bool"
        )
    if not isinstance(notes, str) or not notes:
        raise FixtureValidationError(f"{fixture_name}: {packet_id}: missing notes")

    data = tuple(parse_hex_byte(value) for value in packet["bytes"])
    expected_checksum = parse_hex_byte(packet["expected_checksum"])
    if len(data) != length:
        raise FixtureValidationError(f"{fixture_name}: {packet_id}: byte length mismatch")
    if frame_type != format_hex_byte(data[0]):
        raise FixtureValidationError(f"{fixture_name}: {packet_id}: frame_type mismatch")

    calculated_checksum = calculate_checksum(data, length)
    if expected_checksum != calculated_checksum:
        raise FixtureValidationError(
            f"{fixture_name}: {packet_id}: expected checksum "
            f"{format_hex_byte(expected_checksum)} != calculated "
            f"{format_hex_byte(calculated_checksum)}"
        )
    if checksum_valid != (data[length - 1] == calculated_checksum):
        raise FixtureValidationError(
            f"{fixture_name}: {packet_id}: checksum_valid does not match bytes"
        )

    return PacketFixture(
        fixture_name=fixture_name,
        id=packet_id,
        source_id=source_id,
        label=label,
        source=source,
        length=length,
        frame_type=frame_type,
        bytes=data,
        checksum_valid=checksum_valid,
        expected_checksum=expected_checksum,
        notes=notes,
    )
