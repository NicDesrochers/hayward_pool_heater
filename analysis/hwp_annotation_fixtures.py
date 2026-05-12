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

from .hwp_fixtures import (
    REPO_ROOT,
    SUPPORTED_LENGTHS,
    FixtureValidationError,
    calculate_checksum,
    format_hex_byte,
    parse_hex_byte,
)


DEFAULT_ANNOTATION_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "annotations"


@dataclass(frozen=True)
class AnnotationPacketFixture:
    label: str
    source: str
    length: int
    frame_type: str
    bytes: tuple[int, ...]
    checksum_valid: bool
    expected_checksum: int

    @property
    def byte_key(self) -> tuple[int, ...]:
        return self.bytes


@dataclass(frozen=True)
class AnnotationReadExpectation:
    field: str
    value: float | str
    raw_byte_index: int
    raw_byte_value: int
    frame_type: str
    source: str


@dataclass(frozen=True)
class AnnotationWriteExpectation:
    field: str
    value: float | str
    base_bytes: tuple[int, ...]
    expected_bytes: tuple[int, ...]
    checksum_valid: bool


@dataclass(frozen=True)
class AnnotationFixture:
    fixture_name: str
    id: str
    source_id: str
    label: str
    notes: str
    packet: AnnotationPacketFixture
    read: AnnotationReadExpectation | None
    write: AnnotationWriteExpectation | None


@dataclass(frozen=True)
class AnnotationFixtureFile:
    path: Path
    schema_version: int
    source: str
    provenance: str
    annotations: tuple[AnnotationFixture, ...]

    @property
    def name(self) -> str:
        return self.path.name


def load_annotation_fixture_file(path: Path | str) -> AnnotationFixtureFile:
    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as fixture_file:
        raw_fixture = json.load(fixture_file)

    schema_version = raw_fixture.get("schema_version")
    source = raw_fixture.get("source")
    provenance = raw_fixture.get("provenance")
    raw_annotations = raw_fixture.get("annotations")

    if schema_version != 1:
        raise FixtureValidationError(
            f"{fixture_path}: unsupported schema_version {schema_version!r}"
        )
    if not isinstance(source, str) or not source:
        raise FixtureValidationError(f"{fixture_path}: missing source")
    if not isinstance(provenance, str) or not provenance:
        raise FixtureValidationError(f"{fixture_path}: missing provenance")
    if not isinstance(raw_annotations, list) or not raw_annotations:
        raise FixtureValidationError(f"{fixture_path}: missing annotations")

    annotations = tuple(
        _parse_annotation(fixture_path.name, annotation)
        for annotation in raw_annotations
    )
    return AnnotationFixtureFile(
        path=fixture_path,
        schema_version=schema_version,
        source=source,
        provenance=provenance,
        annotations=annotations,
    )


def load_annotation_fixture_files(
    fixture_dir: Path | str = DEFAULT_ANNOTATION_FIXTURE_DIR,
) -> tuple[AnnotationFixtureFile, ...]:
    paths = sorted(Path(fixture_dir).glob("hwp_*.json"))
    return tuple(load_annotation_fixture_file(path) for path in paths)


def all_annotations(
    fixtures: Iterable[AnnotationFixtureFile],
) -> tuple[AnnotationFixture, ...]:
    return tuple(annotation for fixture in fixtures for annotation in fixture.annotations)


def validate_unique_annotation_ids(fixtures: Iterable[AnnotationFixtureFile]) -> None:
    seen: set[str] = set()
    for annotation in all_annotations(fixtures):
        if annotation.id in seen:
            raise FixtureValidationError(f"duplicate annotation id {annotation.id!r}")
        seen.add(annotation.id)


def _parse_annotation(fixture_name: str, annotation: dict) -> AnnotationFixture:
    for key in ("id", "source_id", "label", "notes", "packet"):
        if key not in annotation:
            raise FixtureValidationError(
                f"{fixture_name}: annotation missing {key!r}"
            )
    annotation_id = annotation["id"]
    packet = _parse_packet(fixture_name, annotation_id, annotation["packet"])
    read = _parse_read_expectation(
        fixture_name, annotation_id, annotation.get("read"), packet
    )
    write = _parse_write_expectation(
        fixture_name, annotation_id, annotation.get("write")
    )
    return AnnotationFixture(
        fixture_name=fixture_name,
        id=annotation_id,
        source_id=annotation["source_id"],
        label=annotation["label"],
        notes=annotation["notes"],
        packet=packet,
        read=read,
        write=write,
    )


def _parse_packet(
    fixture_name: str, annotation_id: str, packet: dict
) -> AnnotationPacketFixture:
    for key in (
        "label",
        "source",
        "length",
        "frame_type",
        "bytes",
        "checksum_valid",
        "expected_checksum",
    ):
        if key not in packet:
            raise FixtureValidationError(
                f"{fixture_name}: {annotation_id}: packet missing {key!r}"
            )

    length = packet["length"]
    if length not in SUPPORTED_LENGTHS:
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad length")
    if packet["source"] not in {"heater", "controller"}:
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad source")
    if not isinstance(packet["checksum_valid"], bool):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: checksum_valid must be bool"
        )

    data = tuple(parse_hex_byte(value) for value in packet["bytes"])
    expected_checksum = parse_hex_byte(packet["expected_checksum"])
    if len(data) != length:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: byte length mismatch"
        )
    if packet["frame_type"] != format_hex_byte(data[0]):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: frame_type mismatch"
        )

    calculated_checksum = calculate_checksum(data, length)
    if expected_checksum != calculated_checksum:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: checksum mismatch"
        )
    if packet["checksum_valid"] != (data[length - 1] == calculated_checksum):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: checksum_valid mismatch"
        )

    return AnnotationPacketFixture(
        label=packet["label"],
        source=packet["source"],
        length=length,
        frame_type=packet["frame_type"],
        bytes=data,
        checksum_valid=packet["checksum_valid"],
        expected_checksum=expected_checksum,
    )


def _parse_read_expectation(
    fixture_name: str,
    annotation_id: str,
    read: dict | None,
    packet: AnnotationPacketFixture,
) -> AnnotationReadExpectation | None:
    if read is None:
        return None
    for key in ("field", "value", "raw_byte_index", "raw_byte_value", "frame_type", "source"):
        if key not in read:
            raise FixtureValidationError(
                f"{fixture_name}: {annotation_id}: read missing {key!r}"
            )
    if not isinstance(read["field"], str) or not read["field"]:
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad read field")
    raw_byte_index = read["raw_byte_index"]
    if not isinstance(raw_byte_index, int) or raw_byte_index < 0:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: bad read raw_byte_index"
        )
    if raw_byte_index >= packet.length:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: read raw_byte_index out of range"
        )
    raw_byte_value = parse_hex_byte(read["raw_byte_value"])
    if packet.bytes[raw_byte_index] != raw_byte_value:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: read raw_byte_value mismatch"
        )
    if read["frame_type"] != packet.frame_type:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: read frame_type mismatch"
        )
    if read["source"] != packet.source:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: read source mismatch"
        )
    value = read["value"]
    if not isinstance(value, (int, float, str)):
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad read value")
    return AnnotationReadExpectation(
        field=read["field"],
        value=float(value) if isinstance(value, int) else value,
        raw_byte_index=raw_byte_index,
        raw_byte_value=raw_byte_value,
        frame_type=read["frame_type"],
        source=read["source"],
    )


def _parse_write_expectation(
    fixture_name: str,
    annotation_id: str,
    write: dict | None,
) -> AnnotationWriteExpectation | None:
    if write is None:
        return None
    for key in ("field", "value", "base_bytes", "expected_bytes", "checksum_valid"):
        if key not in write:
            raise FixtureValidationError(
                f"{fixture_name}: {annotation_id}: write missing {key!r}"
            )
    if not isinstance(write["field"], str) or not write["field"]:
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad write field")
    value = write["value"]
    if not isinstance(value, (int, float, str)):
        raise FixtureValidationError(f"{fixture_name}: {annotation_id}: bad write value")
    if not isinstance(write["checksum_valid"], bool):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: write checksum_valid must be bool"
        )
    base_bytes = tuple(parse_hex_byte(value) for value in write["base_bytes"])
    expected_bytes = tuple(parse_hex_byte(value) for value in write["expected_bytes"])
    if len(base_bytes) not in SUPPORTED_LENGTHS:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: bad write base length"
        )
    if len(expected_bytes) not in SUPPORTED_LENGTHS:
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: bad write expected length"
        )
    if len(base_bytes) != len(expected_bytes):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: write length mismatch"
        )
    if write["checksum_valid"] != (
        expected_bytes[-1] == calculate_checksum(expected_bytes, len(expected_bytes))
    ):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: write checksum_valid mismatch"
        )
    if base_bytes[-1] != calculate_checksum(base_bytes, len(base_bytes)):
        raise FixtureValidationError(
            f"{fixture_name}: {annotation_id}: write base checksum mismatch"
        )
    return AnnotationWriteExpectation(
        field=write["field"],
        value=float(value) if isinstance(value, int) else value,
        base_bytes=base_bytes,
        expected_bytes=expected_bytes,
        checksum_valid=write["checksum_valid"],
    )
