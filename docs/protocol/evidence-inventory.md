# Evidence Inventory

This note records the current reusable evidence map from ignored `tmp/hwp`
reference material. The full logs and copied simulator remain ignored; this
document and the `analysis.hwp_analyze evidence` command are the tracked entry
points.

## Command

```sh
python -m analysis.hwp_analyze evidence --limit 25
```

## Current Scan

As of the latest scan, the inventory covers:

- `tmp/hwp/POOL_esphome_logs - Copy.log`
- `tmp/hwp/POOL_esphome_logs.log.2024-11-01`
- `tmp/hwp/POOL_esphome_logs.log.2024-10-31`
- `tmp/hwp/analysis/POOL_esphome_logs.log.2024-10-30`
- `tmp/hwp/analysis/POOL_esphome_logs.log.2024-11-09`
- `tmp/hwp/analysis/simulator/DemoFrames.h`

Summary:

| Source | Count | Tracked today | Remaining |
|----|----:|----:|----:|
| Annotated windows | 65 | 35 packet-window matches | 19 packet windows not yet covered |
| Annotated windows with packets | 54 | 35 | 19 |
| Arduino demo packets | 43 | 16 | 27 |

The simulator packet corpus is broader than the first golden packet fixture
slice. It includes proven command-style examples for R01-R07, R09-R11,
D01/D05/D06, and temperature/status packets. These should be imported as
focused fixtures before changing related command generation.

## Notable Remaining Evidence

Annotated windows not yet tracked as fixtures include:

- `F10 - 0` in `POOL_esphome_logs - Copy.log`
- `F12 - 50` in both copied and 2024-11-01 logs
- `F13 - 99` and `F13 - 100` in both copied and 2024-11-01 logs
- Additional `F02 - 41`, `F03 - 15.5`, and `F08 - 1` windows
- Several 2024-10-31 `test` windows for condition/clock packets

Uncovered simulator packets include:

- `CONFIG_1`: mode auto plus R01-R07 setpoint/differential examples
- `CONFIG_3`: R09-R11 limit examples
- `CONFIG_2`: D01 defrost start examples
- `CONFIG_5`: D05 and another D06 example with a different adjacent byte state
- `COND_2`/`COND_D`: additional temperature/status examples

## Interpretation

The annotated logs and Arduino simulator are valid reverse-engineering
evidence. They should not be treated as speculative tmp code. However, they
should still be imported in small tracked fixture slices, with checksums,
field expectations, and command/echo or read/write contracts where the source
supports them.

## Suggested Import Order

1. Add a simulator command-fixture slice for `CONFIG_1` R01-R07 and
   `CONFIG_3` R09-R11 because the simulator has many checksum-valid examples.
2. Expand fan-control annotation fixtures for the uncovered F02/F03/F08/F10/F12/F13
   windows so duplicate/edge values are tracked.
3. Add `CONFIG_5` D05/D06 simulator examples as passive command-byte fixtures,
   keeping live active-TX claims limited to the already captured D06 echo
   fixture until more hardware echo logs exist.
4. Mine the 2024-10-31 condition/clock `test` windows only if they add new
   decode coverage beyond the current passive runtime contracts.
