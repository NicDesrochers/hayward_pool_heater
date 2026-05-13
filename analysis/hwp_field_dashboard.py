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

from dataclasses import dataclass, replace
from typing import Iterable

from .hwp_log_parser import ParsedLogPacket
from .hwp_menu_map import MENU_PACKET_MAP, MenuPacketMapping
from .hwp_packet_fields import PACKET_FIELD_MAP, PacketFieldMapping


@dataclass(frozen=True)
class FieldObservation:
    field_id: str
    label: str
    description: str
    frame: str
    frame_label: str
    raw_location: str
    raw_byte_index: int
    raw_bit_index: int | None
    raw_value: int
    decoded_value: float | int | str | bool
    display_value: str
    unit: str
    source: str
    timestamp: str
    checksum_valid: bool
    evidence: str
    safety_status: str
    implementation_status: str
    changed: bool = False

    @property
    def numeric_value(self) -> float | None:
        if isinstance(self.decoded_value, bool):
            return None
        if isinstance(self.decoded_value, (float, int)):
            return float(self.decoded_value)
        return None


class DashboardState:
    """Maintain the latest decoded field observations from HWP packets."""

    def __init__(self, *, require_valid_checksum: bool = True):
        self.require_valid_checksum = require_valid_checksum
        self._latest: dict[str, FieldObservation] = {}

    @property
    def latest(self) -> tuple[FieldObservation, ...]:
        return tuple(
            self._latest[key]
            for key in sorted(self._latest, key=lambda value: (_group_sort(value), value))
        )

    def update(self, packet: ParsedLogPacket) -> tuple[FieldObservation, ...]:
        if self.require_valid_checksum and not packet.checksum_valid:
            return ()
        observations = decode_packet_fields(packet)
        changed_observations = []
        for observation in observations:
            previous = self._latest.get(observation.field_id)
            changed = (
                previous is not None
                and previous.decoded_value != observation.decoded_value
            )
            observation = replace(observation, changed=changed)
            self._latest[observation.field_id] = observation
            changed_observations.append(observation)
        return tuple(changed_observations)


class GraphState:
    """Rolling in-memory history for numeric dashboard fields."""

    def __init__(self, *, max_points: int = 240):
        self.max_points = max_points
        self._history: dict[str, list[tuple[int, float]]] = {}
        self._sequence = 0

    @property
    def history(self) -> dict[str, tuple[tuple[int, float], ...]]:
        return {
            field_id: tuple(points)
            for field_id, points in sorted(self._history.items())
        }

    def update(self, observations: Iterable[FieldObservation]) -> None:
        for observation in observations:
            value = observation.numeric_value
            if value is None:
                continue
            self._sequence += 1
            points = self._history.setdefault(observation.field_id, [])
            points.append((self._sequence, value))
            if len(points) > self.max_points:
                del points[: len(points) - self.max_points]


@dataclass(frozen=True)
class GraphGroup:
    group_id: str
    title: str
    field_ids: tuple[str, ...]


def decode_packet_fields(packet: ParsedLogPacket) -> tuple[FieldObservation, ...]:
    observations: list[FieldObservation] = []
    for mapping in _mappings_for_packet(packet):
        if mapping.byte_index >= packet.length:
            continue
        decoded = _decode_mapping(packet, mapping)
        if decoded is None:
            continue
        value, display, unit, raw_value = decoded
        observations.append(
            FieldObservation(
                field_id=mapping.field,
                label=_field_label(mapping),
                description=mapping.meaning,
                frame=mapping.frame,
                frame_label=mapping.frame_label,
                raw_location=mapping.location,
                raw_byte_index=mapping.byte_index,
                raw_bit_index=mapping.bit_index,
                raw_value=raw_value,
                decoded_value=value,
                display_value=display,
                unit=unit,
                source=packet.source,
                timestamp=packet.timestamp,
                checksum_valid=packet.checksum_valid,
                evidence=mapping.evidence,
                implementation_status=getattr(mapping, "implementation_status", "known"),
                safety_status=getattr(mapping, "safety_status", "evidence"),
            )
        )
    return tuple(observations)


def default_graph_field_ids() -> tuple[str, ...]:
    return tuple(
        field_id
        for group in graph_groups()
        for field_id in group.field_ids
    )


def graph_groups() -> tuple[GraphGroup, ...]:
    return (
        GraphGroup(
            "temperatures",
            "Temperatures",
            (
                "t02_inlet",
                "t03_outlet",
                "t04_coil",
                "t06_exhaust",
                "t_aux_cond2",
            ),
        ),
        GraphGroup(
            "setpoints",
            "Setpoints And Limits",
            (
                "r01_setpoint_cooling",
                "r02_setpoint_heating",
                "r03_setpoint_auto",
                "r08_min_cool_setpoint",
                "r09_max_cooling_setpoint",
                "r10_min_heating_setpoint",
                "r11_max_heating_setpoint",
            ),
        ),
        GraphGroup(
            "low_range",
            "Low-Range Values",
            (
                "r04_return_diff_cooling",
                "r05_shutdown_temp_diff_when_cooling",
                "r06_return_diff_heating",
                "r07_shutdown_diff_heating",
                "d03_defrosting_cycle_time_minutes",
                "d04_max_defrost_time_minutes",
                "d05_min_economy_defrost_time_minutes",
                "f08_fan_low_speed_running_time",
                "f09_fan_stop_low_speed_running_time",
                "f12_min_fan_voltage_pct",
                "f13_max_fan_voltage_pct",
            ),
        ),
    )


def graph_group_for_field(field_id: str) -> str:
    for group in graph_groups():
        if field_id in group.field_ids:
            return group.group_id
    return "other"


def _mappings_for_packet(
    packet: ParsedLogPacket,
) -> tuple[MenuPacketMapping | PacketFieldMapping, ...]:
    mappings: list[MenuPacketMapping | PacketFieldMapping] = []
    seen: set[str] = set()
    for mapping in (*MENU_PACKET_MAP, *PACKET_FIELD_MAP):
        if mapping.frame != packet.frame_type:
            continue
        if not _label_applies(mapping.frame_label, packet.label):
            continue
        if mapping.field in seen:
            continue
        mappings.append(mapping)
        seen.add(mapping.field)
    return tuple(mappings)


def _label_applies(mapping_label: str, packet_label: str) -> bool:
    if not packet_label or "/" in mapping_label:
        return True
    return packet_label == mapping_label


def _decode_mapping(
    packet: ParsedLogPacket,
    mapping: MenuPacketMapping | PacketFieldMapping,
) -> tuple[float | int | str | bool, str, str, int] | None:
    raw_byte = packet.bytes[mapping.byte_index]
    raw_value = (
        (raw_byte >> mapping.bit_index) & 0x01
        if mapping.bit_index is not None
        else raw_byte
    )
    field = mapping.field

    if field == "h02_mode_restrictions":
        if raw_byte & 0x08:
            return "Heating Only", "Heating Only", "", raw_byte
        if raw_byte & 0x04:
            return "Any Mode", "Any Mode", "", raw_byte
        return "Cooling Only", "Cooling Only", "", raw_byte
    if field == "f01_fan_mode":
        mode = _fan_mode((raw_byte >> 4) & 0x0F)
        return mode, mode, "", raw_byte
    if field == "f10_fan_speed_control_temp":
        value = "Ambient Temperature" if ((raw_byte >> 3) & 0x01) else "Coil Temperature"
        return value, value, "", raw_byte
    if field == "f11_speed_control_module":
        value = "Disabled" if raw_value else "Enabled"
        return value, value, "", raw_value
    if field == "d06_defrost_eco_mode":
        value = "Eco" if raw_value else "Normal"
        return value, value, "", raw_value
    if field == "u01_flow_meter":
        value = "Disabled" if raw_value else "Enabled"
        return value, value, "", raw_value
    if field == "s02_water_flow":
        # Runtime and hardware logs carry this bit in the COND_1B status byte
        # after the reserved bytes. Keep a fallback for older/native fixture
        # packets that put 0x02 one byte earlier.
        status_byte = packet.bytes[4] if packet.length > 4 and packet.bytes[4] else raw_byte
        flow_raw = (status_byte >> 1) & 0x01
        flowing = bool(flow_raw)
        return flowing, "FLOWING" if flowing else "NO FLOW", "", flow_raw

    encoding = mapping.encoding
    if encoding.startswith("extended temperature"):
        value = _decode_temperature_extended(raw_byte)
        return value, _format_float(value), "C", raw_byte
    if encoding == "temperature":
        value = _decode_temperature(raw_byte)
        return value, _format_float(value), "C", raw_byte
    if encoding == "decimal minutes":
        value = _decode_decimal_number(raw_byte)
        return value, _format_float(value), "min", raw_byte
    if encoding in {"integer minutes", "integer percent"}:
        unit = "min" if encoding == "integer minutes" else "%"
        return raw_byte, str(raw_byte), unit, raw_byte
    if encoding == "large integer":
        return raw_byte, str(raw_byte), "", raw_byte
    if encoding == "boolean enum":
        value = bool(raw_value)
        return value, "ON" if value else "OFF", "", raw_value
    if encoding == "inverted boolean enum":
        value = not bool(raw_value)
        return value, "ON" if value else "OFF", "", raw_value
    return raw_value, str(raw_value), "", raw_value


def _decode_temperature_extended(value: int) -> float:
    return float((value >> 1) & 0x7F) - 30.0 + (0.5 if value & 0x01 else 0.0)


def _decode_temperature(value: int) -> float:
    result = float((value >> 1) & 0x1F) + (0.5 if value & 0x01 else 0.0)
    if value & 0x40:
        result += 2.0
    return -result if value & 0x80 else result


def _decode_decimal_number(value: int) -> float:
    result = float((value >> 1) & 0x3F) + (0.5 if value & 0x01 else 0.0)
    return -result if value & 0x80 else result


def _fan_mode(value: int) -> str:
    return {
        0: "Low Speed",
        1: "High Speed",
        2: "Ambient",
        3: "Scheduled",
        4: "Scheduled Ambient",
    }.get(value, "Low Speed")


def _field_label(mapping: MenuPacketMapping | PacketFieldMapping) -> str:
    menu = getattr(mapping, "menu", "")
    return f"{menu} {mapping.meaning}" if menu else mapping.meaning


def short_field_label(observation: FieldObservation) -> str:
    if observation.label.startswith("R"):
        return observation.label
    if observation.label.startswith("F"):
        return observation.label
    if observation.label.startswith("D"):
        return observation.label
    return observation.description


def _format_float(value: float) -> str:
    return f"{value:.1f}"


def _group_sort(field_id: str) -> tuple[int, str]:
    if field_id.startswith("t"):
        return (0, field_id)
    if field_id.startswith("r"):
        return (1, field_id)
    if field_id.startswith("f"):
        return (2, field_id)
    return (3, field_id)
