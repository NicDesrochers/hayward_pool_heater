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

from .hwp_menu_map import MENU_BY_CODE


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
class PacketMenuExpectation:
    fixture_name: str
    packet_id: str
    menu: str
    field: str
    value: float | str
    raw_byte_index: int
    raw_byte_value: int
    frame_type: str
    source: str


@dataclass(frozen=True)
class PacketMenuPairContract:
    fixture_name: str
    id: str
    menu: str
    field: str
    base_packet_id: str
    expected_packet_id: str
    raw_byte_index: int
    expected_raw_byte_value: int
    changed_byte_indexes: tuple[int, ...]


@dataclass(frozen=True)
class FixtureFile:
    path: Path
    schema_version: int
    source: str
    provenance: str
    packets: tuple[PacketFixture, ...]
    menu_expectations: tuple[PacketMenuExpectation, ...]
    menu_pairs: tuple[PacketMenuPairContract, ...]

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
    raw_menu_expectations = raw_fixture.get("menu_expectations", [])
    raw_menu_pairs = raw_fixture.get("menu_pairs", [])

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
    packet_index = {packet.id: packet for packet in packets}
    menu_expectations = tuple(
        _parse_menu_expectation(fixture_path.name, expectation, packet_index)
        for expectation in raw_menu_expectations
    )
    menu_pairs = tuple(
        _parse_menu_pair(fixture_path.name, pair, packet_index) for pair in raw_menu_pairs
    )
    return FixtureFile(
        path=fixture_path,
        schema_version=schema_version,
        source=source,
        provenance=provenance,
        packets=packets,
        menu_expectations=menu_expectations,
        menu_pairs=menu_pairs,
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


def all_menu_expectations(fixtures: Iterable[FixtureFile]) -> tuple[PacketMenuExpectation, ...]:
    return tuple(expectation for fixture in fixtures for expectation in fixture.menu_expectations)


def all_menu_pairs(fixtures: Iterable[FixtureFile]) -> tuple[PacketMenuPairContract, ...]:
    return tuple(pair for fixture in fixtures for pair in fixture.menu_pairs)


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


def _parse_menu_expectation(
    fixture_name: str, expectation: dict, packet_index: dict[str, PacketFixture]
) -> PacketMenuExpectation:
    required = {
        "packet_id",
        "menu",
        "field",
        "value",
        "raw_byte_index",
        "raw_byte_value",
        "frame_type",
        "source",
    }
    missing = required - set(expectation)
    if missing:
        raise FixtureValidationError(
            f"{fixture_name}: menu expectation missing {sorted(missing)}"
        )

    packet_id = expectation["packet_id"]
    packet = packet_index.get(packet_id)
    if packet is None:
        raise FixtureValidationError(
            f"{fixture_name}: menu expectation references unknown packet {packet_id!r}"
        )

    menu = expectation["menu"]
    mapping = MENU_BY_CODE.get(menu)
    if mapping is None:
        raise FixtureValidationError(f"{fixture_name}: unknown menu code {menu!r}")
    if expectation["field"] != mapping.field:
        raise FixtureValidationError(f"{fixture_name}: {menu}: field mismatch")
    if expectation["frame_type"] != mapping.frame or packet.frame_type != mapping.frame:
        raise FixtureValidationError(f"{fixture_name}: {menu}: frame mismatch")
    if expectation["source"] != packet.source:
        raise FixtureValidationError(f"{fixture_name}: {menu}: source mismatch")

    raw_byte_index = expectation["raw_byte_index"]
    if raw_byte_index != mapping.byte_index:
        raise FixtureValidationError(f"{fixture_name}: {menu}: byte index mismatch")
    raw_byte_value = parse_hex_byte(expectation["raw_byte_value"])
    if packet.bytes[raw_byte_index] != raw_byte_value:
        raise FixtureValidationError(f"{fixture_name}: {menu}: raw byte mismatch")

    value = expectation["value"]
    if not isinstance(value, (int, float, str)):
        raise FixtureValidationError(f"{fixture_name}: {menu}: bad expectation value")

    return PacketMenuExpectation(
        fixture_name=fixture_name,
        packet_id=packet_id,
        menu=menu,
        field=expectation["field"],
        value=value,
        raw_byte_index=raw_byte_index,
        raw_byte_value=raw_byte_value,
        frame_type=expectation["frame_type"],
        source=expectation["source"],
    )


def _parse_menu_pair(
    fixture_name: str, pair: dict, packet_index: dict[str, PacketFixture]
) -> PacketMenuPairContract:
    required = {
        "id",
        "menu",
        "field",
        "base_packet_id",
        "expected_packet_id",
        "raw_byte_index",
        "expected_raw_byte_value",
        "changed_byte_indexes",
    }
    missing = required - set(pair)
    if missing:
        raise FixtureValidationError(f"{fixture_name}: menu pair missing {sorted(missing)}")

    menu = pair["menu"]
    mapping = MENU_BY_CODE.get(menu)
    if mapping is None:
        raise FixtureValidationError(f"{fixture_name}: unknown menu code {menu!r}")
    if pair["field"] != mapping.field:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair field mismatch")

    base_packet = packet_index.get(pair["base_packet_id"])
    expected_packet = packet_index.get(pair["expected_packet_id"])
    if base_packet is None or expected_packet is None:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair references unknown packet")
    if base_packet.frame_type != mapping.frame or expected_packet.frame_type != mapping.frame:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair frame mismatch")
    if base_packet.source != expected_packet.source:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair source mismatch")
    if not base_packet.checksum_valid or not expected_packet.checksum_valid:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair checksum invalid")

    raw_byte_index = pair["raw_byte_index"]
    if raw_byte_index != mapping.byte_index:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair byte index mismatch")
    expected_raw_byte_value = parse_hex_byte(pair["expected_raw_byte_value"])
    if expected_packet.bytes[raw_byte_index] != expected_raw_byte_value:
        raise FixtureValidationError(f"{fixture_name}: {menu}: pair expected byte mismatch")

    changed_byte_indexes = tuple(pair["changed_byte_indexes"])
    if not all(isinstance(index, int) for index in changed_byte_indexes):
        raise FixtureValidationError(f"{fixture_name}: {menu}: bad changed byte indexes")
    checksum_index = expected_packet.length - 1
    actual_changed = tuple(
        index
        for index, (base_value, expected_value) in enumerate(
            zip(base_packet.bytes, expected_packet.bytes, strict=True)
        )
        if index != checksum_index and base_value != expected_value
    )
    if actual_changed != changed_byte_indexes:
        raise FixtureValidationError(
            f"{fixture_name}: {menu}: changed bytes {actual_changed} != "
            f"{changed_byte_indexes}"
        )

    return PacketMenuPairContract(
        fixture_name=fixture_name,
        id=pair["id"],
        menu=menu,
        field=pair["field"],
        base_packet_id=pair["base_packet_id"],
        expected_packet_id=pair["expected_packet_id"],
        raw_byte_index=raw_byte_index,
        expected_raw_byte_value=expected_raw_byte_value,
        changed_byte_indexes=changed_byte_indexes,
    )
