# `tmp/hwp` Salvage Closure

## Summary

`tmp/hwp` is closed as an active merge source. It remains an ignored reference tree only. Do not copy generated output, logs, local IDE files, secrets, copied `.git` content, or the alternate `components/hwp - Copy` tree into the repo.

The useful protocol and fan-control work has been folded into this repo through tested slices. Any future use of `tmp/hwp` should start from this document and create a new feature ID; do not cherry-pick from the copied tree opportunistically. Recent hardware logs are the exception to the "closed merge source" framing: they are archival evidence that can be mined into small tracked fixtures without reopening the tmp code merge.

## Final Disposition

| Source Material | Disposition | Notes |
|-----------------|-------------|-------|
| `analysis/simulator/DemoFrames.h` base/demo packets | Merged | Curated JSON fixtures live under `tests/fixtures/packets/`; includes checksum validation and one explicit invalid checksum case |
| `POOL_esphome_logs.log` recent hardware trace | Merged | A curated subset lives in `tests/fixtures/packets/hwp_hardware_log_2025_06_24.json`; do not import the full log |
| F02-F13 fan field names | Merged | Runtime decode naming is in `FrameConf1`, `FrameConf2`, `FrameConf4`, and `FrameConf5` |
| F10/F11 pure enum/string behavior | Merged | Dependency-light conversions live in `components/hwp/protocol_core.*` with native tests |
| F02-F13 helper exposure | Merged | Helpers validate through Python schema tests and compile in ESPHome fixtures |
| F02-F13 fan command surface | Merged | Helper controls feed `HWPCall`; frame control paths restore tmp parity; representative byte mutations are covered by native tests |
| `convert_capture.py` capture conversion | Deferred | Rebuild as a repo-native tool with stdlib tests if capture import becomes a priority |
| Log tagger/annotator workflow | Deferred | Keep as workflow reference; do not import Tk/UI tooling without a manual-analysis feature slice |
| Arduino simulator shell and scheduling model | Replaced | Old architecture remains reference-only; packet corpus and timing/playbook concepts now feed the first-class ESPHome `hwp_simulator` component |
| Generic `SensorCtrl`/`BoundaryCtrl` helper model | Deferred | Could reduce boilerplate later, but current explicit helpers are easier to audit around active heater control |
| Wholesale `climate.py` rewrite | Rejected | Too broad and mixed with unrelated design changes; useful schema ideas were imported in smaller slices |
| `global_hp_data_members` / `HWPCall` inheritance model | Rejected | Current explicit `HWPCall` fields are simpler to review and avoid a broad core-design shift |
| tmp `PoolHeater.cpp` behavior | Rejected | It appeared to comment out current sensor publishing paths and risked offline/status regressions |
| `components/hwp - Copy`, generated outputs, logs, IDE files, copied `.git` | Rejected | Do not import |

## Remaining Reference Topics

- Capture/log tooling can become a repo-native tool after a new feature ID is created.
- Hardware log fixture extraction should start with `tmp/hwp/POOL_esphome_logs.log` from June 24, 2025 because tracing is newer and includes verbose packet annotations. Older `POOL_esphome_logs.*`, `NEW_esphome_logs.log`, and `analysis/*logs*` files are secondary sources.
- Simulator automation should be evaluated as fixture replay, PlatformIO Arduino simulation, or ESPHome/QEMU work; it should not become default CI without a reliability slice.
- Active fan writes are compile-tested and byte-tested against hardware-derived protocol evidence. Use supervised manual procedures before claiming a setting is operationally safe on a live heater.

## Closure Rules

- Treat `tmp/hwp` as archival reference, not a branch.
- Do not ask future agents to rediscover or merge it before normal feature work.
- If a future task needs tmp material, name the exact file and expected output, then add focused tests before changing runtime behavior.
- Keep `/tmp/` ignored.
