# Menu-To-Packet Map

This is the tracked bridge between technical-manual menu options, observed
packets, and implementation status. It exists so future protocol work starts
from menu intent and evidence rather than raw bytes alone.

The machine-readable copy lives in `analysis/hwp_menu_map.py`; tests pin core
mappings and require implemented helper fields to appear in this map.

## Status Terms

- `implemented`: frame/helper plumbing exists.
- `read-only`: parsed and exposed but not written by the component.
- `byte-tested`: command-byte generation or read/write fixture coverage exists.
- `live-echo-validated`: supervised hardware write and heater echo evidence exists.
- `needs fixture import`: evidence exists in tmp/simulator material but should be converted into tracked fixtures before broadening behavior claims.

## CONFIG_1 / `0x81`

| Menu | Field | Meaning | Location | Encoding | Evidence | Status |
|----|----|----|----|----|----|----|
| H02 | `h02_mode_restrictions` | Mode restrictions | byte 2 | bit field enum | implemented config frame | implemented, byte-tested |
| R01 | `r01_setpoint_cooling` | Cooling setpoint | byte 3 | temperature | Arduino simulator packet | implemented, needs fixture import |
| R02 | `r02_setpoint_heating` | Heating setpoint | byte 4 | temperature | Arduino simulator packet | implemented, needs fixture import |
| R03 | `r03_setpoint_auto` | Auto setpoint | byte 5 | temperature | Arduino simulator packet | implemented, needs fixture import |
| R04 | `r04_return_diff_cooling` | Cooling return differential | byte 6 | extended temperature/delta | Arduino simulator packet | implemented, needs fixture import |
| R05 | `r05_shutdown_temp_diff_when_cooling` | Cooling shutdown differential | byte 7 | extended temperature/delta | Arduino simulator packet | implemented, needs fixture import |
| R06 | `r06_return_diff_heating` | Heating return differential | byte 8 | extended temperature/delta | Arduino simulator packet | implemented, needs fixture import |
| R07 | `r07_shutdown_diff_heating` | Heating shutdown differential | byte 9 | extended temperature/delta | Arduino simulator packet | implemented, needs fixture import |
| F12 | `f12_min_fan_voltage_pct` | Minimum fan voltage percent | byte 10 | integer percent | annotated log window | implemented, byte-tested |

## CONFIG_2 / `0x82`

| Menu | Field | Meaning | Location | Encoding | Evidence | Status |
|----|----|----|----|----|----|----|
| F01 | `f01_fan_mode` | Fan mode | byte 2 | upper nibble enum | annotation fixture | implemented, byte-tested |
| F10 | `f10_fan_speed_control_temp` | Fan speed control temperature source | byte 2 bit 3 | boolean enum | annotation fixture | implemented, byte-tested |
| D01 | `d01_defrost_start` | Defrost start temperature | byte 3 | extended temperature | Arduino simulator packet | implemented, needs fixture import |
| D02 | `d02_defrost_end` | Defrost end temperature | byte 4 | temperature | implemented config frame | implemented, needs fixture import |
| D03 | `d03_defrosting_cycle_time_minutes` | Defrosting cycle time | byte 5 | decimal minutes | implemented config frame | implemented, needs fixture import |
| D04 | `d04_max_defrost_time_minutes` | Maximum defrost time | byte 6 | decimal minutes | implemented config frame | implemented, needs fixture import |
| F13 | `f13_max_fan_voltage_pct` | Maximum fan voltage percent | byte 10 | integer percent | annotation fixture | implemented, byte-tested |

## CONFIG_3 / `0x83`

| Menu | Field | Meaning | Location | Encoding | Evidence | Status |
|----|----|----|----|----|----|----|
| R08 | `r08_min_cool_setpoint` | Minimum cooling setpoint limit | byte 7 | extended temperature | runtime fixture | read-only |
| R09 | `r09_max_cooling_setpoint` | Maximum cooling setpoint limit | byte 8 | extended temperature | Arduino simulator packet | read-only, needs fixture import |
| R10 | `r10_min_heating_setpoint` | Minimum heating setpoint limit | byte 9 | extended temperature | Arduino simulator packet | read-only, needs fixture import |
| R11 | `r11_max_heating_setpoint` | Maximum heating setpoint limit | byte 10 | extended temperature | Arduino simulator packet | read-only, needs fixture import |

## CONFIG_4 / `0x84`

| Menu | Field | Meaning | Location | Encoding | Evidence | Status |
|----|----|----|----|----|----|----|
| F02 | `f02_fan_high_speed_cool_setpoint` | Fan high-speed cooling setpoint | byte 2 | extended temperature | annotation fixture | implemented, byte-tested |
| F03 | `f03_fan_low_speed_temp_in_cooling_set_point` | Fan low-speed cooling temperature | byte 3 | extended temperature | annotation fixture | implemented, byte-tested |
| F04 | `f04_fan_stop_temp_in_cooling_set_point` | Fan stop cooling temperature | byte 4 | extended temperature | annotation fixture | implemented, byte-tested |
| F05 | `f05_fan_high_speed_temp_in_heating_set_point` | Fan high-speed heating temperature | byte 5 | extended temperature | annotation fixture | implemented, byte-tested |
| F06 | `f06_fan_low_speed_temp_in_heating_set_point` | Fan low-speed heating temperature | byte 6 | extended temperature | annotation fixture | implemented, byte-tested |
| F07 | `f07_fan_stop_temp_in_heating_set_point` | Fan stop heating temperature | byte 7 | extended temperature | annotation fixture | implemented, byte-tested |
| F08 | `f08_fan_low_speed_running_time` | Fan low-speed running time | byte 8 | integer minutes | annotation fixture | implemented, byte-tested |
| F09 | `f09_fan_stop_low_speed_running_time` | Fan stop low-speed running time | byte 9 | integer minutes | annotation fixture | implemented, byte-tested |

## CONFIG_5 / `0x85`

| Menu | Field | Meaning | Location | Encoding | Evidence | Status |
|----|----|----|----|----|----|----|
| U01 | `u01_flow_meter` | Flow meter enable | byte 2 bit 2 | boolean enum | implemented config frame | implemented, needs fixture import |
| F11 | `f11_speed_control_module` | Speed-control module enable | byte 2 bit 3 | inverted boolean enum | annotation fixture | implemented, byte-tested |
| D06 | `d06_defrost_eco_mode` | Defrost economy mode | byte 2 bit 6 | boolean enum | active TX echo fixture | implemented, live-echo-validated |
| D05 | `d05_min_economy_defrost_time_minutes` | Minimum economy defrost time | byte 3 | decimal minutes | Arduino simulator packet | implemented, needs fixture import |
| U02 | `u02_pulses_per_liter` | Flow-meter pulses per liter | byte 10 | large integer | implemented config frame | implemented, needs fixture import |

## Status Packet

| Menu | Field | Meaning | Frame | Location | Encoding | Status |
|----|----|----|----|----|----|----|
| S02 | `s02_water_flow` | Water flow status | `0xD1` / `COND_1B` | byte 3 bit 2 | status bit | read-only |

## Workflow

When adding protocol behavior:

1. Add or update the menu row in `analysis/hwp_menu_map.py`.
2. Convert supporting tmp/annotation/simulator evidence into a tracked fixture.
3. Add protocol/native/schema tests as appropriate.
4. Only mark `live-echo-validated` after supervised hardware write and heater echo evidence exists.
