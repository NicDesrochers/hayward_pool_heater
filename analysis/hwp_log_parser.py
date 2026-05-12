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

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .hwp_fixtures import (
    SUPPORTED_LENGTHS,
    FixtureValidationError,
    calculate_checksum,
    is_checksum_valid,
)


ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
HEX_RE = re.compile(r"[0-9A-Fa-f]{2}")
HOST_TIMESTAMP_RE = re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+-")
DEVICE_TIMESTAMP_RE = re.compile(r"\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
ANNOTATION_BEGIN_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+-\s*"
    r"(?P<label>.*?)\s+-- BEGIN$"
)
ANNOTATION_END_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+-\s*"
    r"(?P<label>.*?)\s+-- END$"
)
PACKET_RE = re.compile(
    r"(?:\[(?P<direction>RX|TX)\].*?:|:\s*)\s*"
    r"(?P<kind>TXQ|QUEUE|PUSH|SEND|[A-Za-z]+)?\s*"
    r"\[(?P<frame>[0-9A-Fa-f]{2})\]"
    r"\[(?P<body>[^\]]*)\]"
    r"\[(?P<checksum>[0-9A-Fa-f]{2})\]\s*"
    r"(?P<label>[A-Z0-9_]+)?"
    r"(?:\s+\((?P<source_marker>HEAT|CONT)\))?"
)


@dataclass(frozen=True)
class ParsedLogPacket:
    line_number: int
    timestamp: str
    kind: str
    label: str
    source: str
    source_marker: str
    length: int
    frame_type: str
    bytes: tuple[int, ...]
    expected_checksum: int | None
    checksum_valid: bool
    text: str

    @property
    def byte_key(self) -> tuple[int, ...]:
        return self.bytes


@dataclass(frozen=True)
class ParsedAnnotationWindow:
    label: str
    start_line: int
    end_line: int
    start_timestamp: str
    end_timestamp: str
    packets: tuple[ParsedLogPacket, ...]


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_log_line(line: str, line_number: int = 0) -> ParsedLogPacket | None:
    clean = strip_ansi(line).rstrip("\n")
    match = PACKET_RE.search(clean)
    if not match:
        return None

    body = tuple(int(value, 16) for value in HEX_RE.findall(match.group("body")))
    packet_bytes = (
        int(match.group("frame"), 16),
        *body,
        int(match.group("checksum"), 16),
    )
    length = len(packet_bytes)
    checksum: int | None
    checksum_ok = False
    if length in SUPPORTED_LENGTHS:
        checksum = calculate_checksum(packet_bytes, length)
        checksum_ok = is_checksum_valid(packet_bytes, length)
    else:
        checksum = None

    source_marker = match.group("source_marker") or ""
    kind = match.group("kind") or ""
    direction = match.group("direction") or ""
    source = (
        "controller"
        if source_marker.startswith("CONT") or direction == "TX" or kind in {"TXQ", "QUEUE", "PUSH", "SEND"}
        else "heater"
    )

    return ParsedLogPacket(
        line_number=line_number,
        timestamp=_extract_timestamp(clean),
        kind=kind,
        label=match.group("label") or "",
        source=source,
        source_marker=direction if direction == "TX" else source_marker or direction,
        length=length,
        frame_type=f"0x{packet_bytes[0]:02X}",
        bytes=tuple(packet_bytes),
        expected_checksum=checksum,
        checksum_valid=checksum_ok,
        text=clean,
    )


def parse_log_lines(lines: Iterable[str]) -> tuple[ParsedLogPacket, ...]:
    packets = []
    for line_number, line in enumerate(lines, 1):
        packet = parse_log_line(line, line_number)
        if packet is not None:
            packets.append(packet)
    return tuple(packets)


def parse_log_file(path: Path | str) -> tuple[ParsedLogPacket, ...]:
    log_path = Path(path)
    with log_path.open(encoding="utf-8", errors="replace") as log_file:
        return parse_log_lines(log_file)


def parse_annotation_windows(lines: Iterable[str]) -> tuple[ParsedAnnotationWindow, ...]:
    windows: list[ParsedAnnotationWindow] = []
    current_label: str | None = None
    start_line = 0
    start_timestamp = ""
    packets: list[ParsedLogPacket] = []

    for line_number, line in enumerate(lines, 1):
        clean = strip_ansi(line).rstrip("\n")
        begin_match = ANNOTATION_BEGIN_RE.search(clean)
        if begin_match:
            current_label = begin_match.group("label").strip()
            start_line = line_number
            start_timestamp = begin_match.group("timestamp")
            packets = []
            continue

        end_match = ANNOTATION_END_RE.search(clean)
        if end_match and current_label is not None:
            windows.append(
                ParsedAnnotationWindow(
                    label=current_label,
                    start_line=start_line,
                    end_line=line_number,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_match.group("timestamp"),
                    packets=tuple(packets),
                )
            )
            current_label = None
            packets = []
            continue

        if current_label is not None:
            packet = parse_log_line(line, line_number)
            if packet is not None:
                packets.append(packet)

    return tuple(windows)


def parse_annotation_file(path: Path | str) -> tuple[ParsedAnnotationWindow, ...]:
    log_path = Path(path)
    with log_path.open(encoding="utf-8", errors="replace") as log_file:
        return parse_annotation_windows(log_file)


def packet_counts(packets: Iterable[ParsedLogPacket]) -> dict[tuple[int, ...], int]:
    counts: dict[tuple[int, ...], int] = {}
    for packet in packets:
        counts[packet.byte_key] = counts.get(packet.byte_key, 0) + 1
    return counts


def _extract_timestamp(text: str) -> str:
    host_match = HOST_TIMESTAMP_RE.search(text)
    if host_match:
        return host_match.group("timestamp")
    device_match = DEVICE_TIMESTAMP_RE.search(text)
    if device_match:
        return device_match.group("timestamp")
    return ""
