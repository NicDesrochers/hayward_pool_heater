# Evidence Inventory

This note records the current reusable evidence map from ignored `tmp/hwp`
reference material. The full logs and copied simulator remain ignored; this
document and the `analysis.hwp_analyze evidence` command are the tracked entry
points.

Use `docs/protocol/menu-packet-map.md` for the technical-menu-to-frame source of
truth before importing more fixtures or broadening active controls.

## Command

```sh
python -m analysis.hwp_analyze evidence --limit 25
python -m analysis.hwp_analyze evidence --menu --limit 25
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
| Annotated windows | 65 | 47 packet-window matches | 7 packet windows not yet covered |
| Annotated windows with packets | 54 | 47 | 7 |
| Arduino demo packets | 43 | 35 | 8 |

The simulator packet corpus is broader than the first golden packet fixture
slice. `CONFIG_1` R01-R07 and `CONFIG_3` R09-R11 command-style examples are
now tracked as menu-backed fixtures. Remaining useful simulator examples cover
D01/D05/D06 and additional temperature/status packets.

## Notable Remaining Evidence

Annotated fan-control windows are now tracked for F01-F13, including the
previously loose F02/F03/F08/F10/F12/F13 edge values. Annotated windows not yet
tracked as fixtures are non-fan windows from 2024-10-31:

- Several 2024-10-31 `test` windows for condition/clock packets

Uncovered simulator packets include:

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

1. Add `CONFIG_2`/`CONFIG_5` defrost simulator examples for D01/D05/D06 as
   passive command-byte fixtures,
   keeping live active-TX claims limited to the already captured D06 echo
   fixture until more hardware echo logs exist.
2. Mine the 2024-10-31 condition/clock `test` windows only if they add new
   decode coverage beyond the current passive runtime contracts.
