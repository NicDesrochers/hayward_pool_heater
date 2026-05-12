# HWP Packet Fixtures

These fixtures are curated from hardware-derived tmp reference material:

- `hwp_demo_packets.json` comes from `tmp/hwp/analysis/simulator/DemoFrames.h`.
- `hwp_hardware_log_2025_06_24.json` comes from the recent ignored
  `tmp/hwp/POOL_esphome_logs.log` hardware trace.

They are packet regression fixtures, not a replacement for supervised live
heater validation.

The fixture format is intentionally simple JSON so it can be validated with
stdlib Python and later consumed by native tests or small generators.

Each packet has:

- `id`: stable fixture id
- `label`: short source label
- `source`: `heater` or `controller`
- `length`: supported packet length, currently `9` or `12`
- `frame_type`: first byte as `0xNN`
- `bytes`: packet bytes as `0xNN` strings, trimmed to `length`
- `checksum_valid`: expected checksum result under current protocol rules
- `expected_checksum`: calculated checksum as `0xNN`
- `notes`: short provenance or interpretation notes

For 9-byte packets, checksum is calculated over bytes 1 through 7. For
12-byte packets, checksum is calculated over bytes 0 through 10.
