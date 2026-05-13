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

from dataclasses import dataclass
from typing import Mapping, Sequence

from .hwp_fixtures import PacketFixture
from .hwp_log_parser import ParsedLogPacket
from .hwp_menu_map import MENU_PACKET_MAP, MenuPacketMapping
from .hwp_packet_fields import PACKET_FIELD_MAP, PacketFieldMapping


@dataclass(frozen=True)
class PacketCell:
    index: int
    value: int
    text: str
    role: str
    changed: bool
    menu_fields: tuple[MenuPacketMapping, ...]
    known_fields: tuple[PacketFieldMapping, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class PacketView:
    packet: ParsedLogPacket
    cells: tuple[PacketCell, ...]
    fixture_matches: tuple[str, ...]
    checksum_status: str
    title: str
    summary: str


class PacketViewState:
    """Track previous packets so the view model can mark byte-level changes."""

    def __init__(
        self,
        fixture_index: Mapping[tuple[int, ...], Sequence[PacketFixture]] | None = None,
    ):
        self.fixture_index = fixture_index or {}
        self._previous: dict[tuple[str, str, int], tuple[int, ...]] = {}

    def build(self, packet: ParsedLogPacket) -> PacketView:
        key = (packet.frame_type, packet.source, packet.length)
        previous = self._previous.get(key)
        view = build_packet_view(packet, self.fixture_index, previous)
        self._previous[key] = packet.bytes
        return view


def build_packet_view(
    packet: ParsedLogPacket,
    fixture_index: Mapping[tuple[int, ...], Sequence[PacketFixture]] | None = None,
    previous_bytes: Sequence[int] | None = None,
) -> PacketView:
    fixtures = tuple((fixture_index or {}).get(packet.byte_key, ()))
    fixture_matches = tuple(f"{fixture.fixture_name}:{fixture.id}" for fixture in fixtures)
    menu_by_index = _menu_fields_for_packet(packet)
    known_by_index = _known_fields_for_packet(packet)
    cells = []
    for index, value in enumerate(packet.bytes):
        role = _cell_role(index, packet.length)
        changed = previous_bytes is not None and (
            index >= len(previous_bytes) or previous_bytes[index] != value
        )
        menu_fields = tuple(menu_by_index.get(index, ()))
        known_fields = tuple(known_by_index.get(index, ()))
        tags = _cell_tags(
            role,
            changed,
            menu_fields,
            known_fields,
            packet.checksum_valid,
            bool(fixtures),
        )
        cells.append(
            PacketCell(
                index=index,
                value=value,
                text=f"{value:02X}",
                role=role,
                changed=changed,
                menu_fields=menu_fields,
                known_fields=known_fields,
                tags=tags,
            )
        )

    checksum_status = "valid" if packet.checksum_valid else "invalid"
    fixture_text = f", fixtures={len(fixtures)}" if fixtures else ""
    title = (
        f"{packet.kind or 'Packet'} {packet.frame_type} {packet.label or 'UNKNOWN'} "
        f"{packet.source} len={packet.length} checksum={checksum_status}{fixture_text}"
    )
    menu_names = sorted({field.menu for fields in menu_by_index.values() for field in fields})
    field_names = sorted({field.field for fields in known_by_index.values() for field in fields})
    known_labels = [*menu_names, *field_names]
    summary = ", ".join(known_labels) if known_labels else "no known packet fields"
    return PacketView(
        packet=packet,
        cells=tuple(cells),
        fixture_matches=fixture_matches,
        checksum_status=checksum_status,
        title=title,
        summary=summary,
    )


def render_packet_view_text(view: PacketView) -> str:
    """Return a compact text form suitable for CLI smoke output or Tk Text."""
    groups = []
    for cell in view.cells:
        label = _cell_label(cell)
        marker = "*" if cell.changed else ""
        suffix = f"<{label}>" if label else ""
        groups.append(f"{marker}{cell.text}{suffix}")
    return f"{view.title}\n[{' '.join(groups)}]\n{view.summary}"


def _menu_fields_for_packet(
    packet: ParsedLogPacket,
) -> dict[int, list[MenuPacketMapping]]:
    fields: dict[int, list[MenuPacketMapping]] = {}
    for entry in MENU_PACKET_MAP:
        if entry.frame == packet.frame_type and entry.byte_index < packet.length:
            fields.setdefault(entry.byte_index, []).append(entry)
    return fields


def _known_fields_for_packet(
    packet: ParsedLogPacket,
) -> dict[int, list[PacketFieldMapping]]:
    fields: dict[int, list[PacketFieldMapping]] = {}
    for entry in PACKET_FIELD_MAP:
        if entry.frame == packet.frame_type and entry.byte_index < packet.length:
            fields.setdefault(entry.byte_index, []).append(entry)
    return fields


def _cell_label(cell: PacketCell) -> str:
    labels = [field.menu for field in cell.menu_fields]
    labels.extend(field.field for field in cell.known_fields)
    return ",".join(labels)


def _cell_role(index: int, packet_length: int) -> str:
    if index == 0:
        return "frame"
    if index == packet_length - 1:
        return "checksum"
    return "body"


def _cell_tags(
    role: str,
    changed: bool,
    menu_fields: tuple[MenuPacketMapping, ...],
    known_fields: tuple[PacketFieldMapping, ...],
    checksum_valid: bool,
    fixture_match: bool,
) -> tuple[str, ...]:
    tags = [role]
    if changed:
        tags.append("changed")
    if menu_fields:
        tags.append("known-menu")
    if known_fields:
        tags.append("known-field")
    if role == "checksum" and not checksum_valid:
        tags.append("checksum-invalid")
    if fixture_match:
        tags.append("fixture-match")
    return tuple(tags)
