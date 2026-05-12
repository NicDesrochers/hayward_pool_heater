# Handover

## Start Here

This repo is now developed inside the ESPHome devcontainer. Read:

1. `AGENTS.md` for operational rules and verification commands.
2. `docs/features.md` for project status and next feature slices.
3. `docs/testing/backlog.md` for detailed testing tasks.
4. `docs/tmp-hwp-salvage.md` only if a task explicitly needs archival tmp reference material.

## Current State

- ESPHome external component lives in `components/hwp/`.
- Devcontainer builds from `ghcr.io/esphome/esphome:latest`, adds declared native/QEMU-adjacent tools, and keeps generated firmware output outside the repo through `/build`.
- ESPHome compile fixtures, Python schema tests, packet fixture validation, native protocol tests, runners, and CI are in place.
- Headless analysis tooling is packaged under `analysis/`. Use `python -m analysis.hwp_analyze fixtures`, `log`, and `prove` to validate fixtures, summarize hardware logs, and prove fixture packets appear in traces.
- Manual annotation windows are parsed by the same CLI. Use `python -m analysis.hwp_analyze annotations --input tmp/hwp/POOL_esphome_logs.log.2024-11-01` and `prove-annotations` for curated tagger windows.
- The first native C++ seam lives in `components/hwp/protocol_core.*` and covers dependency-light packet helpers plus fan mode, defrost, flow-meter, and heat-pump restriction conversions.
- Component-local adapter headers keep climate/logger/time/RMT coupling out of core frame tests where practical. `HWP_NATIVE_TEST` uses those adapters to compile runtime frame contracts without full ESPHome or hardware RMT dependencies.
- Curated packet fixtures from `tmp/hwp/analysis/simulator/DemoFrames.h` live under `tests/fixtures/packets/` and validate with stdlib Python tests. Those simulator packets are hardware-derived reference frames, not synthetic-only samples.
- A curated subset from the recent ignored `tmp/hwp/POOL_esphome_logs.log` trace is tracked as `tests/fixtures/packets/hwp_hardware_log_2025_06_24.json`; it covers representative real RX/change frames for `0x81`, `0x82`, `0x83`, `0x84`, `0x85`, `0x86`, `0xD1`, `0xD2`, `0xDD`, plus clock/controller frames. The proof CLI found all 15 checksum-valid packets from that fixture in the full ignored log.
- A curated annotation fixture from `tmp/hwp/POOL_esphome_logs.log.2024-11-01` lives under `tests/fixtures/annotations/`; it captures fan-control tagger windows for F01 and F02-F13 as read/write packet contracts.
- Fan field candidates from the tmp tree are reviewed in `docs/protocol/fan-field-review.md` and covered by fixture-backed Python tests.
- Runtime decode naming for F02-F09, F10, F11, and F13 is merged in the frame structs. F10/F11 dependency-light conversions are covered in `protocol_core`.
- Runtime `FrameConf1/2/4/5` matching and parsing are covered by adapter-backed native tests against the F01-F13 packet contracts.
- Passive runtime frame contracts are covered by the same adapter-backed native executable. `FrameConditions1/1B/2/2B/D`, `FrameClock`, `FrameConf3`, and `FrameConf6` now match tracked fixture packets; parsed condition temperatures, S02 water flow, and config-3 setpoint limits are compared with pure `protocol_core` helpers.
- Fan helper exposure and command parity are merged for F02-F13. Helpers publish decoded values and feed command calls; native byte-helper tests pin F01-F13 read decode and passive command byte mutations before live hardware validation.
- The copied `tmp/hwp` merge track is closed. It is ignored and summarized in `docs/tmp-hwp-salvage.md` as archival reference only.
- Manual hardware-in-the-loop validation gates live in `docs/testing/manual-hil.md`; active fan writes are byte-tested and based on tmp/hardware-derived packet evidence, but each live setting still needs supervised field confirmation before claiming operational safety.
- The bus implementation now uses ESP-IDF 5 RMT RX/TX channels on the same half-duplex GPIO. RX is initialized before TX, both channels use 100 kHz resolution, TX uses the copy encoder, and decoder-facing pulse durations are normalized to microseconds through `hwp_pulse_symbol_t`.
- `climate.py` includes the built-in `esp_driver_rmt` IDF component during codegen; the default normal and pulse-debug compile fixtures now target `framework: type: esp-idf`.
- Current ESPHome version verified in the devcontainer: `2026.4.5`.
- Compile logs confirmed `framework-espidf @ 3.50504.0 (5.5.4)`. The normal and pulse-debug fixtures compile without the legacy RMT deprecation warning.

## Last Verified

Inside the devcontainer:

```sh
./scripts/test-native.sh
python -m unittest discover -s tests -p 'test_*.py'
python -m analysis.hwp_analyze fixtures
python -m analysis.hwp_analyze prove --input tmp/hwp/POOL_esphome_logs.log --fixture tests/fixtures/packets/hwp_hardware_log_2025_06_24.json
python -m analysis.hwp_analyze prove-annotations --input tmp/hwp/POOL_esphome_logs.log.2024-11-01 --fixture tests/fixtures/annotations/hwp_annotated_fan_control_2024_11_01.json
./scripts/test-esphome.sh --local
git diff --check
bash -n scripts/test-esphome.sh scripts/test-native.sh
```

The local runner validated and compiled both ESPHome fixtures after Python and native tests. Generated output stayed outside the repo.

## Suggested Next Steps

Choose the next slice from normal project priorities rather than tmp merge work.

Good candidates:

- run supervised passive RX validation for the new ESP-IDF 5 RMT receive path
- run supervised active TX validation for one byte-tested command path after passive RX is stable
- add the next low-level native seam for queue behavior
- run supervised manual validation for any active-control setting whose bytes are already covered
- extract capture conversion as repo-native tooling
- document simulator feasibility using fixture replay versus Arduino/PlatformIO versus ESPHome/QEMU
- probe QEMU or ESPHome `host:` only as feasibility work

QEMU and ESPHome `host:` remain later feasibility slices, not the default runner.

## Active Risks

- Active heater control remains safety-sensitive and needs manual procedures before new real-device claims.
- ESPHome compile success does not prove electrical safety or live heater behavior.
- The ESP-IDF 5 RMT RX/TX path is compile/native verified only; real bus receive timing, half-duplex turnaround, and active transmission still need supervised hardware validation.
- Debian `qemu-system-xtensa` is available in the devcontainer, but `idf.py`, `IDF_PATH`, and an ESP32 QEMU machine are not present.
- `tmp/hwp` is closed as an active merge source, but its recent logs are valid archival evidence to mine into small tracked fixtures. Future runtime changes still need focused tests and hardware-safety review.

## Working Tree Note

The repo currently has broad uncommitted work from environment, testing, and component stabilization slices. Do not revert existing changes unless explicitly asked.
