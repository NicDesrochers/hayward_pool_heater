# HWP Annotation Fixtures

These fixtures capture manual analysis/tagging windows from ignored hardware logs.
They are intended as proof examples for future parser, frame decode, and command
generation tests.

`hwp_annotated_fan_control_2024_11_01.json` comes from
`tmp/hwp/POOL_esphome_logs.log.2024-11-01`. It keeps a curated set of annotation
windows where the old tagger was used while fan/control settings were changed.
The full log remains ignored.

Fan-control annotations include:

- `packet`: the observed packet from the hardware log window
- `read`: the expected decoded field/value and raw byte evidence
- `write`: a passive command-byte contract from a base packet to expected bytes

The write contract is a byte-generation test input only. It is not a live heater
safety claim.
