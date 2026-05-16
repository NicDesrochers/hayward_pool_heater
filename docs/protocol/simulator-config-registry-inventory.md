# HWP Simulator Config Registry Inventory

This inventory defines which controller-originated config packets the simulator
must listen to and persist in its runtime model. It is a simulator contract for
bench HIL only; it does not expand live heater-control safety claims.

The simulator treats config packets as heater-side registers. A checksum-valid
controller packet for `CONFIG_1` through `CONFIG_6` updates the full stored
packet bytes, normalized to heater source. Generated simulator config packets
then replay those stored bytes until simulator reset or reboot. Sensor and
status packets remain simulator-owned playbook values.

Persistence is runtime-only. The simulator does not write these register values
to flash/NVS.

## Writable Home Assistant Surface

| Packet | Stored fields from current writable surface |
|--------|---------------------------------------------|
| `CONFIG_1` / `0x81` | Climate power/mode bits, H02 mode restrictions, R01 cooling setpoint, R02 heating setpoint, R03 auto setpoint, R04 cooling return differential, R05 cooling shutdown differential, R06 heating return differential, R07 heating shutdown differential, F12 minimum fan voltage percent |
| `CONFIG_2` / `0x82` | F01 fan mode, F10 fan speed-control temperature source, D01 defrost start temperature, D02 defrost end temperature, D03 defrost cycle time, D04 maximum defrost time, F13 maximum fan voltage percent |
| `CONFIG_4` / `0x84` | F02 high-speed cooling setpoint, F03 low-speed cooling setpoint, F04 cooling stop setpoint, F05 high-speed heating setpoint, F06 low-speed heating setpoint, F07 heating stop setpoint, F08 low-speed run time, F09 low-speed stop time |
| `CONFIG_5` / `0x85` | U01 flow meter enable, D05 minimum economy defrost time, D06 defrost economy mode, F11 speed-control module, U02 pulses per liter |

## Raw Config Registers

| Packet | Current writable surface | Simulator behavior |
|--------|--------------------------|--------------------|
| `CONFIG_3` / `0x83` | None; R08-R11 are read-only setpoint limits today | Accept, store, echo if changed, and replay full packet bytes |
| `CONFIG_6` / `0x86` | None; fields are currently unknown/reserved | Accept, store, echo if changed, and replay full packet bytes |

## Echo Rule

When a decoded controller burst contains multiple changed config packets, the
simulator stores all changed registry packets but schedules only the first
changed packet as the immediate heater-originated echo. Identical repeated
controller packets are accepted and de-duplicated; they do not schedule another
echo.

The simulator currently keeps heater-originated TX repeats at four packets per
group. Real-heater captures often appear as one logical decoded packet; that
timing difference is tracked as a separate HIL tuning topic.
