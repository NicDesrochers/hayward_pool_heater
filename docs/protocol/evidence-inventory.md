# Evidence Inventory

This note records the current reusable evidence map from ignored `tmp/hwp`
reference material. The full logs and copied simulator remain ignored; this
document and the `analysis.hwp_analyze evidence` command are the tracked entry
points.

Use `docs/protocol/menu-packet-map.md` for the technical-menu-to-frame source of
truth before importing more fixtures or broadening active controls.
Use `docs/protocol/research-backlog.md` for uncertain fields that need human
analysis before implementation.

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
| Arduino demo packets | 43 | 42 | 1 |

The simulator packet corpus is broader than the first golden packet fixture
slice. `CONFIG_1` R01-R07, `CONFIG_2` D01, `CONFIG_3` R09-R11, and
`CONFIG_5` D05/D06 command-style examples are now tracked as menu-backed
fixtures. The remaining useful simulator example is an uncertain `COND_D`
status packet.

## Notable Remaining Evidence

Annotated fan-control windows are now tracked for F01-F13, including the
previously loose F02/F03/F08/F10/F12/F13 edge values. Annotated windows not yet
tracked as fixtures are non-fan windows from 2024-10-31:

- Several 2024-10-31 `test` windows for condition/clock packets

Uncovered simulator packets include:

- `COND_D`: additional status example with unclear field meanings

## Interpretation

The annotated logs and Arduino simulator are valid reverse-engineering
evidence. They should not be treated as speculative tmp code. However, they
should still be imported in small tracked fixture slices, with checksums,
field expectations, and command/echo or read/write contracts where the source
supports them.

Not every annotation window represents a writable menu action. Some annotation
sessions were created while checking values in read-only technical menus or
status screens. For those packets, the evidence can prove observed read/decode
behavior and byte changes, but it should not be promoted to a command/write
contract unless there is a separate controller-originated packet, simulator
command example, or live hardware echo.

## Suggested Import Order

1. Mine the 2024-10-31 condition/clock `test` windows only if they add new
   decode coverage beyond the current passive runtime contracts.
2. Track unresolved or ambiguous findings in `docs/protocol/research-backlog.md`
   until the analysis tooling or a human review can turn them into fixtures.
