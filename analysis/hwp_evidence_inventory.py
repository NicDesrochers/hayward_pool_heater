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
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .hwp_active_tx_fixtures import load_active_tx_fixture_files
from .hwp_annotation_fixtures import load_annotation_fixture_files
from .hwp_fixtures import (
    DEFAULT_FIXTURE_DIR,
    REPO_ROOT,
    calculate_checksum,
    format_hex_byte,
    load_fixture_files,
)
from .hwp_log_parser import ParsedAnnotationWindow, parse_annotation_file
from .hwp_menu_map import MENU_PACKET_MAP, MenuPacketMapping


DEFAULT_EVIDENCE_LOGS = (
    REPO_ROOT / "tmp" / "hwp" / "POOL_esphome_logs - Copy.log",
    REPO_ROOT / "tmp" / "hwp" / "POOL_esphome_logs.log.2024-11-01",
    REPO_ROOT / "tmp" / "hwp" / "POOL_esphome_logs.log.2024-10-31",
    REPO_ROOT / "tmp" / "hwp" / "analysis" / "POOL_esphome_logs.log.2024-10-30",
    REPO_ROOT / "tmp" / "hwp" / "analysis" / "POOL_esphome_logs.log.2024-11-09",
)
DEFAULT_DEMO_FRAMES = REPO_ROOT / "tmp" / "hwp" / "analysis" / "simulator" / "DemoFrames.h"

FIELD_RE = re.compile(r"^(?P<field>[A-Za-z]\d{2}|[A-Za-z]+)")
DATA_RE = re.compile(
    r"const\s+uint8_t\s+(?P<name>[A-Za-z0-9_]+)\[(?P<length>\d+)\]\s*=\s*"
    r"\{(?P<body>[^}]*)\}"
)
PACKET_RE = re.compile(
    r"static\s+const\s+packet_t\s+(?P<id>[A-Za-z0-9_]+)\s*=\s*packet_t\(\s*"
    r"(?P<controllable>true|false)\s*,\s*(?P<length>\d+)\s*,\s*std::string\(\"(?P<label>[^\"]*)\"\s*\)\s*,\s*"
    r"(?P<data>[A-Za-z0-9_]+)"
)
HEX_RE = re.compile(r"0x[0-9A-Fa-f]{2}")


@dataclass(frozen=True)
class TrackedPacketEvidence:
    kind: str
    identifier: str


@dataclass(frozen=True)
class EvidenceWindowSummary:
    log_path: Path
    label: str
    field: str
    start_line: int
    end_line: int
    packet_count: int
    checksum_valid_count: int
    frame_types: tuple[str, ...]
    packet_sources: tuple[str, ...]
    tracked_matches: tuple[str, ...]

    @property
    def has_packet(self) -> bool:
        return self.packet_count > 0

    @property
    def is_covered(self) -> bool:
        return bool(self.tracked_matches)


@dataclass(frozen=True)
class DemoPacketSummary:
    identifier: str
    label: str
    controllable: bool
    length: int
    frame_type: str
    checksum_valid: bool
    tracked_matches: tuple[str, ...]

    @property
    def is_covered(self) -> bool:
        return bool(self.tracked_matches)


@dataclass(frozen=True)
class EvidenceInventory:
    windows: tuple[EvidenceWindowSummary, ...]
    demo_packets: tuple[DemoPacketSummary, ...]
    missing_logs: tuple[Path, ...]
    missing_demo_frames: bool

    @property
    def packet_windows(self) -> tuple[EvidenceWindowSummary, ...]:
        return tuple(window for window in self.windows if window.has_packet)

    @property
    def covered_windows(self) -> tuple[EvidenceWindowSummary, ...]:
        return tuple(window for window in self.packet_windows if window.is_covered)

    @property
    def uncovered_windows(self) -> tuple[EvidenceWindowSummary, ...]:
        return tuple(window for window in self.packet_windows if not window.is_covered)

    @property
    def covered_demo_packets(self) -> tuple[DemoPacketSummary, ...]:
        return tuple(packet for packet in self.demo_packets if packet.is_covered)

    @property
    def uncovered_demo_packets(self) -> tuple[DemoPacketSummary, ...]:
        return tuple(packet for packet in self.demo_packets if not packet.is_covered)


def menu_coverage_summary(
    inventory: EvidenceInventory,
) -> dict[str, tuple[MenuPacketMapping, int, bool]]:
    field_counts = inventory_field_counts(inventory.windows)
    demo_labels = {packet.label.lower() for packet in inventory.demo_packets}
    summary: dict[str, tuple[MenuPacketMapping, int, bool]] = {}
    for entry in MENU_PACKET_MAP:
        annotation_count = field_counts.get(entry.menu, Counter()).get("packet_windows", 0)
        has_demo = _menu_has_demo_label(entry.menu, demo_labels)
        summary[entry.menu] = (entry, annotation_count, has_demo)
    return summary


def build_tracked_packet_index() -> dict[tuple[int, ...], set[TrackedPacketEvidence]]:
    index: dict[tuple[int, ...], set[TrackedPacketEvidence]] = {}

    for fixture_file in load_fixture_files(DEFAULT_FIXTURE_DIR):
        for packet in fixture_file.packets:
            _add_tracked(index, packet.bytes, "packet", packet.id)

    for fixture_file in load_annotation_fixture_files():
        for annotation in fixture_file.annotations:
            _add_tracked(index, annotation.packet.bytes, "annotation", annotation.id)
            if annotation.write is not None:
                _add_tracked(
                    index,
                    annotation.write.expected_bytes,
                    "annotation-write",
                    annotation.id,
                )

    for fixture_file in load_active_tx_fixture_files():
        for transaction in fixture_file.transactions:
            _add_tracked(index, transaction.command.bytes, "active-tx-command", transaction.id)
            _add_tracked(index, transaction.echo.bytes, "active-tx-echo", transaction.id)

    return index


def build_evidence_inventory(
    log_paths: Iterable[Path | str] = DEFAULT_EVIDENCE_LOGS,
    demo_frames_path: Path | str = DEFAULT_DEMO_FRAMES,
) -> EvidenceInventory:
    tracked_index = build_tracked_packet_index()
    windows: list[EvidenceWindowSummary] = []
    missing_logs: list[Path] = []

    for raw_path in log_paths:
        path = Path(raw_path)
        if not path.exists():
            missing_logs.append(path)
            continue
        windows.extend(_summarize_windows(path, parse_annotation_file(path), tracked_index))

    demo_path = Path(demo_frames_path)
    missing_demo_frames = not demo_path.exists()
    demo_packets = (
        tuple()
        if missing_demo_frames
        else summarize_demo_frames(demo_path, tracked_index)
    )

    return EvidenceInventory(
        windows=tuple(windows),
        demo_packets=demo_packets,
        missing_logs=tuple(missing_logs),
        missing_demo_frames=missing_demo_frames,
    )


def summarize_demo_frames(
    path: Path | str,
    tracked_index: dict[tuple[int, ...], set[TrackedPacketEvidence]] | None = None,
) -> tuple[DemoPacketSummary, ...]:
    demo_path = Path(path)
    index = tracked_index if tracked_index is not None else build_tracked_packet_index()
    text = demo_path.read_text(encoding="utf-8", errors="replace")

    data_arrays: dict[str, tuple[int, ...]] = {}
    for match in DATA_RE.finditer(text):
        data = tuple(int(value, 16) for value in HEX_RE.findall(match.group("body")))
        data_arrays[match.group("name")] = data

    summaries: list[DemoPacketSummary] = []
    for match in PACKET_RE.finditer(text):
        data = data_arrays.get(match.group("data"))
        if data is None:
            continue
        length = int(match.group("length"))
        packet_bytes = data[:length]
        frame_type = format_hex_byte(packet_bytes[0]) if packet_bytes else "0x00"
        checksum_valid = (
            len(packet_bytes) == length
            and length in {9, 12}
            and packet_bytes[-1] == calculate_checksum(packet_bytes, length)
        )
        summaries.append(
            DemoPacketSummary(
                identifier=match.group("id"),
                label=match.group("label").strip(),
                controllable=match.group("controllable") == "true",
                length=length,
                frame_type=frame_type,
                checksum_valid=checksum_valid,
                tracked_matches=_format_matches(index.get(packet_bytes, set())),
            )
        )

    return tuple(summaries)


def inventory_field_counts(
    windows: Iterable[EvidenceWindowSummary],
) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = {}
    for window in windows:
        field_counts = counts.setdefault(window.field, Counter())
        field_counts["windows"] += 1
        if window.has_packet:
            field_counts["packet_windows"] += 1
        if window.is_covered:
            field_counts["covered"] += 1
    return counts


def inventory_frame_counts(
    windows: Iterable[EvidenceWindowSummary],
    demo_packets: Iterable[DemoPacketSummary],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for window in windows:
        counts.update(window.frame_types)
    counts.update(packet.frame_type for packet in demo_packets)
    return counts


def _summarize_windows(
    log_path: Path,
    windows: tuple[ParsedAnnotationWindow, ...],
    tracked_index: dict[tuple[int, ...], set[TrackedPacketEvidence]],
) -> tuple[EvidenceWindowSummary, ...]:
    summaries: list[EvidenceWindowSummary] = []
    for window in windows:
        matches: set[str] = set()
        for packet in window.packets:
            matches.update(_format_matches(tracked_index.get(packet.byte_key, set())))
        summaries.append(
            EvidenceWindowSummary(
                log_path=log_path,
                label=window.label,
                field=_field_from_label(window.label),
                start_line=window.start_line,
                end_line=window.end_line,
                packet_count=len(window.packets),
                checksum_valid_count=sum(1 for packet in window.packets if packet.checksum_valid),
                frame_types=tuple(sorted({packet.frame_type for packet in window.packets})),
                packet_sources=tuple(sorted({packet.source for packet in window.packets})),
                tracked_matches=tuple(sorted(matches)),
            )
        )
    return tuple(summaries)


def _field_from_label(label: str) -> str:
    match = FIELD_RE.search(label.strip())
    if not match:
        return "<unknown>"
    return match.group("field").upper()


def _menu_has_demo_label(menu: str, labels: set[str]) -> bool:
    menu_lower = menu.lower()
    if menu_lower in labels:
        return True
    return any(label.startswith(f"{menu_lower}=") for label in labels)


def _add_tracked(
    index: dict[tuple[int, ...], set[TrackedPacketEvidence]],
    packet_bytes: tuple[int, ...],
    kind: str,
    identifier: str,
) -> None:
    index.setdefault(packet_bytes, set()).add(TrackedPacketEvidence(kind, identifier))


def _format_matches(matches: Iterable[TrackedPacketEvidence]) -> tuple[str, ...]:
    return tuple(sorted(f"{match.kind}:{match.identifier}" for match in matches))
