# Fan Field Fixture Review

## Summary

This review compares the current frame structs with fan-related field names found in the copied
`tmp/hwp` reference tree. It uses the curated packet fixtures in
`tests/fixtures/packets/hwp_demo_packets.json` as the source of bytes.

These notes are regression tripwires, not live-heater safety claims.

## Fixture Findings

| Fixture | Frame | Current state | Tmp-resolved candidate fields |
|---------|-------|---------------|-------------------------------|
| `base-fan` | `0x82` / `FrameConf2` | F01 fan mode is named; low flag bits and byte 10 are still treated as unknown | F10 speed-control temperature source is bit 3 of byte 2; F13 max fan voltage percent is byte 10 |
| `base-type-84` | `0x84` / `FrameConf4` | Payload bytes are all unknown fields | F02-F07 are temperature-extended bytes, F08-F09 are raw integer time bytes, final payload byte remains unknown |
| `base-conf-a` | `0x85` / `FrameConf5` | Flow meter, defrost eco, D05, and U02 are named | F11 speed-control module disabled bit is bit 3 of byte 2 |

## Candidate Decode Values

From `base-fan`:

- F01 fan mode raw: `0x01`, high speed
- F10 speed-control temperature source raw: `0`, interpreted by tmp as coil-temperature controlled
- F13 max fan voltage percent: `100`

From `base-type-84`:

- F02 fan high-speed cooling setpoint: `40.0C`
- F03 fan low-speed cooling setpoint: `15.0C`
- F04 fan stop cooling setpoint: `10.0C`
- F05 fan high-speed heating setpoint: `10.0C`
- F06 fan low-speed heating setpoint: `20.0C`
- F07 fan stop heating setpoint: `30.0C`
- F08 fan low-speed running time: `0`
- F09 fan stop low-speed running time: `0`
- trailing unknown byte: `0x78`

From `base-conf-a`:

- U01 flow meter raw: `0`, disabled
- F11 speed-control module disabled raw: `0`, interpreted by tmp as enabled
- D06 defrost eco raw: `0`, normal
- D05 minimum economy defrost time: `3.0` minutes
- U02 pulses per liter: `205`

## Runtime Merge Status

The decode-only runtime mapping is merged:

1. `FrameConf2`: F10 speed-control temperature source and F13 max fan voltage percent are named and parsed into `heat_pump_data_t`.
2. `FrameConf4`: F02-F09 fan temperature/time fields are named and parsed into `heat_pump_data_t`.
3. `FrameConf5`: F11 speed-control module is named and parsed into `heat_pump_data_t`.
4. `protocol_core`: F10/F11 raw/string/log conversions are covered by native tests.

Home Assistant helper exposure and command parity are now merged for F02-F13. Native byte-helper tests pin representative fan command mutations and checksums, but live heater behavior still needs manual hardware-in-the-loop validation before treating active fan writes as field-proven.
