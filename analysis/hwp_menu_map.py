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


@dataclass(frozen=True)
class MenuPacketMapping:
    menu: str
    field: str
    meaning: str
    frame: str
    frame_label: str
    byte_index: int
    bit_index: int | None
    encoding: str
    evidence: str
    implementation_status: str
    safety_status: str
    notes: str

    @property
    def location(self) -> str:
        if self.bit_index is None:
            return f"byte {self.byte_index}"
        return f"byte {self.byte_index} bit {self.bit_index}"


MENU_PACKET_MAP: tuple[MenuPacketMapping, ...] = (
    MenuPacketMapping("H02", "h02_mode_restrictions", "Mode restrictions", "0x81", "CONFIG_1", 2, None, "bit field enum", "implemented config frame", "implemented", "byte-tested", "Mode restriction bits share the CONFIG_1 mode byte."),
    MenuPacketMapping("R01", "r01_setpoint_cooling", "Cooling setpoint", "0x81", "CONFIG_1", 3, None, "extended temperature", "demo command fixture / issue #11", "implemented", "byte-tested", "Demo command fixture pins R01 setpoint byte changes; issue #11 regression fixture pins >=34C encoding."),
    MenuPacketMapping("R02", "r02_setpoint_heating", "Heating setpoint", "0x81", "CONFIG_1", 4, None, "extended temperature", "demo command fixture / issue #11", "implemented", "byte-tested", "Demo command fixture pins R02 setpoint byte changes; issue #11 regression fixture pins >=34C encoding."),
    MenuPacketMapping("R03", "r03_setpoint_auto", "Auto setpoint", "0x81", "CONFIG_1", 5, None, "extended temperature", "demo command fixture / issue #11", "implemented", "fixture-backed", "Demo command fixture pins the observed R03 byte; issue #11 regression fixture pins >=34C encoding."),
    MenuPacketMapping("R04", "r04_return_diff_cooling", "Cooling return differential", "0x81", "CONFIG_1", 6, None, "extended temperature/delta", "demo command fixture", "implemented", "byte-tested", "Demo command fixture pins R04 differential byte changes."),
    MenuPacketMapping("R05", "r05_shutdown_temp_diff_when_cooling", "Cooling shutdown differential", "0x81", "CONFIG_1", 7, None, "extended temperature/delta", "demo command fixture", "implemented", "byte-tested", "Demo command fixture pins R05 differential byte changes."),
    MenuPacketMapping("R06", "r06_return_diff_heating", "Heating return differential", "0x81", "CONFIG_1", 8, None, "extended temperature/delta", "demo command fixture", "implemented", "byte-tested", "Demo command fixture pins R06 differential byte changes."),
    MenuPacketMapping("R07", "r07_shutdown_diff_heating", "Heating shutdown differential", "0x81", "CONFIG_1", 9, None, "extended temperature/delta", "demo command fixture", "implemented", "byte-tested", "Demo command fixture pins R07 differential byte changes."),
    MenuPacketMapping("F12", "f12_min_fan_voltage_pct", "Minimum fan voltage percent", "0x81", "CONFIG_1", 10, None, "integer percent", "annotated log window", "implemented", "byte-tested", "Additional F12 50 percent windows remain to import."),
    MenuPacketMapping("F01", "f01_fan_mode", "Fan mode", "0x82", "CONFIG_2", 2, None, "upper nibble enum", "annotation fixture", "implemented", "byte-tested", "F10 shares bit 3 in the same byte."),
    MenuPacketMapping("F10", "f10_fan_speed_control_temp", "Fan speed control temperature source", "0x82", "CONFIG_2", 2, 3, "boolean enum", "annotation fixture", "implemented", "byte-tested", "Uncovered F10=0 windows remain to import."),
    MenuPacketMapping("D01", "d01_defrost_start", "Defrost start temperature", "0x82", "CONFIG_2", 3, None, "extended temperature", "Arduino simulator packet", "implemented", "needs fixture import", "Uncovered simulator examples include D01 changes."),
    MenuPacketMapping("D02", "d02_defrost_end", "Defrost end temperature", "0x82", "CONFIG_2", 4, None, "temperature", "implemented config frame", "implemented", "needs fixture import", "No dedicated tracked command fixture yet."),
    MenuPacketMapping("D03", "d03_defrosting_cycle_time_minutes", "Defrosting cycle time", "0x82", "CONFIG_2", 5, None, "decimal minutes", "implemented config frame", "implemented", "needs fixture import", "No dedicated tracked command fixture yet."),
    MenuPacketMapping("D04", "d04_max_defrost_time_minutes", "Maximum defrost time", "0x82", "CONFIG_2", 6, None, "decimal minutes", "implemented config frame", "implemented", "needs fixture import", "No dedicated tracked command fixture yet."),
    MenuPacketMapping("F13", "f13_max_fan_voltage_pct", "Maximum fan voltage percent", "0x82", "CONFIG_2", 10, None, "integer percent", "annotation fixture", "implemented", "byte-tested", "Additional F13 99/100 percent windows remain to import."),
    MenuPacketMapping("R08", "r08_min_cool_setpoint", "Minimum cooling setpoint limit", "0x83", "CONFIG_3", 7, None, "extended temperature", "runtime fixture", "read-only", "read-only", "Parsed and exposed from passive fixtures; command path is not implemented."),
    MenuPacketMapping("R09", "r09_max_cooling_setpoint", "Maximum cooling setpoint limit", "0x83", "CONFIG_3", 8, None, "extended temperature", "demo command fixture", "read-only", "fixture-backed", "Demo fixture pins observed R09 limit bytes without enabling writes."),
    MenuPacketMapping("R10", "r10_min_heating_setpoint", "Minimum heating setpoint limit", "0x83", "CONFIG_3", 9, None, "extended temperature", "demo command fixture", "read-only", "fixture-backed", "Demo fixture pins observed R10 limit bytes without enabling writes."),
    MenuPacketMapping("R11", "r11_max_heating_setpoint", "Maximum heating setpoint limit", "0x83", "CONFIG_3", 10, None, "extended temperature", "demo command fixture", "read-only", "fixture-backed", "Demo fixture pins observed R11 limit bytes without enabling writes."),
    MenuPacketMapping("F02", "f02_fan_high_speed_cool_setpoint", "Fan high-speed cooling setpoint", "0x84", "CONFIG_4", 2, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", "Additional F02 41.0 windows remain to import."),
    MenuPacketMapping("F03", "f03_fan_low_speed_temp_in_cooling_set_point", "Fan low-speed cooling temperature", "0x84", "CONFIG_4", 3, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", "Additional F03 15.5 window remains to import."),
    MenuPacketMapping("F04", "f04_fan_stop_temp_in_cooling_set_point", "Fan stop cooling temperature", "0x84", "CONFIG_4", 4, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", ""),
    MenuPacketMapping("F05", "f05_fan_high_speed_temp_in_heating_set_point", "Fan high-speed heating temperature", "0x84", "CONFIG_4", 5, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", ""),
    MenuPacketMapping("F06", "f06_fan_low_speed_temp_in_heating_set_point", "Fan low-speed heating temperature", "0x84", "CONFIG_4", 6, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", ""),
    MenuPacketMapping("F07", "f07_fan_stop_temp_in_heating_set_point", "Fan stop heating temperature", "0x84", "CONFIG_4", 7, None, "extended temperature", "annotation fixture", "implemented", "byte-tested", ""),
    MenuPacketMapping("F08", "f08_fan_low_speed_running_time", "Fan low-speed running time", "0x84", "CONFIG_4", 8, None, "integer minutes", "annotation fixture", "implemented", "byte-tested", "Additional F08=1 window remains to import."),
    MenuPacketMapping("F09", "f09_fan_stop_low_speed_running_time", "Fan stop low-speed running time", "0x84", "CONFIG_4", 9, None, "integer minutes", "annotation fixture", "implemented", "byte-tested", ""),
    MenuPacketMapping("U01", "u01_flow_meter", "Flow meter enable", "0x85", "CONFIG_5", 2, 2, "boolean enum", "implemented config frame", "implemented", "needs fixture import", "No dedicated tracked command fixture yet."),
    MenuPacketMapping("F11", "f11_speed_control_module", "Speed-control module enable", "0x85", "CONFIG_5", 2, 3, "inverted boolean enum", "annotation fixture", "implemented", "byte-tested", "Annotated windows cover enabled/disabled transitions."),
    MenuPacketMapping("D06", "d06_defrost_eco_mode", "Defrost economy mode", "0x85", "CONFIG_5", 2, 6, "boolean enum", "active TX echo fixture", "implemented", "live-echo-validated", "Live ECO/NORMAL write echoes are captured under active_tx fixtures."),
    MenuPacketMapping("D05", "d05_min_economy_defrost_time_minutes", "Minimum economy defrost time", "0x85", "CONFIG_5", 3, None, "decimal minutes", "Arduino simulator packet", "implemented", "needs fixture import", "Uncovered simulator examples include D05 changes."),
    MenuPacketMapping("U02", "u02_pulses_per_liter", "Flow-meter pulses per liter", "0x85", "CONFIG_5", 10, None, "large integer", "implemented config frame", "implemented", "needs fixture import", "Candidate for next supervised active TX only after fixture triage."),
    MenuPacketMapping("S02", "s02_water_flow", "Water flow status", "0xD1", "COND_1B", 3, 2, "status bit", "runtime fixture", "read-only", "read-only", "Status bit, not a writable menu option."),
)


MENU_BY_CODE = {entry.menu: entry for entry in MENU_PACKET_MAP}
MENU_BY_FIELD = {entry.field: entry for entry in MENU_PACKET_MAP}


def menu_codes() -> tuple[str, ...]:
    return tuple(entry.menu for entry in MENU_PACKET_MAP)


def validate_menu_packet_map() -> None:
    seen_codes: set[str] = set()
    seen_fields: set[str] = set()
    for entry in MENU_PACKET_MAP:
        if entry.menu in seen_codes:
            raise ValueError(f"duplicate menu code {entry.menu}")
        if entry.field in seen_fields:
            raise ValueError(f"duplicate menu field {entry.field}")
        seen_codes.add(entry.menu)
        seen_fields.add(entry.field)
        if not entry.frame.startswith("0x") or len(entry.frame) != 4:
            raise ValueError(f"{entry.menu}: bad frame {entry.frame}")
        if entry.byte_index < 0 or entry.byte_index > 11:
            raise ValueError(f"{entry.menu}: bad byte index {entry.byte_index}")
        if entry.bit_index is not None and (entry.bit_index < 0 or entry.bit_index > 7):
            raise ValueError(f"{entry.menu}: bad bit index {entry.bit_index}")
        for value in (
            entry.field,
            entry.meaning,
            entry.frame_label,
            entry.encoding,
            entry.evidence,
            entry.implementation_status,
            entry.safety_status,
        ):
            if not value:
                raise ValueError(f"{entry.menu}: missing metadata")
