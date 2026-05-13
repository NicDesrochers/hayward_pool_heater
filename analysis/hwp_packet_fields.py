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
class PacketFieldMapping:
    field: str
    meaning: str
    frame: str
    frame_label: str
    byte_index: int
    bit_index: int | None
    encoding: str
    evidence: str
    notes: str = ""

    @property
    def label(self) -> str:
        return self.field

    @property
    def location(self) -> str:
        if self.bit_index is None:
            return f"byte {self.byte_index}"
        return f"byte {self.byte_index} bit {self.bit_index}"


PACKET_FIELD_MAP: tuple[PacketFieldMapping, ...] = (
    PacketFieldMapping(
        "t02_inlet",
        "Inlet water temperature",
        "0xD1",
        "COND_1/COND_1B",
        9,
        None,
        "temperature",
        "runtime frame contract",
    ),
    PacketFieldMapping(
        "s02_water_flow",
        "Water flow status",
        "0xD1",
        "COND_1B",
        4,
        1,
        "status bit",
        "runtime frame contract",
    ),
    PacketFieldMapping(
        "t03_outlet",
        "Outlet water temperature",
        "0xD2",
        "COND_2",
        4,
        None,
        "temperature",
        "runtime frame contract",
    ),
    PacketFieldMapping(
        "t06_exhaust",
        "Exhaust temperature",
        "0xD2",
        "COND_2",
        5,
        None,
        "temperature",
        "runtime frame contract",
    ),
    PacketFieldMapping(
        "t04_coil",
        "Coil temperature",
        "0xD2",
        "COND_2",
        6,
        None,
        "temperature",
        "runtime frame contract",
    ),
    PacketFieldMapping(
        "t_aux_cond2",
        "Auxiliary condition temperature",
        "0xD2",
        "COND_2",
        8,
        None,
        "temperature",
        "formatter/runtime evidence",
        "Firmware formatter currently labels this as 4??.",
    ),
)
