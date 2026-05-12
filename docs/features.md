# Feature Tracker

## Current Focus

The tmp merge track is closed. The next recommended slice should come from normal feature priorities: supervised hardware validation for the new RMT path, frame parse coverage, manual active-control validation, capture tooling, simulator feasibility, or QEMU/host feasibility.

## Testing Track

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| TEST-010 | ESPHome compile fixtures | Done | Normal and pulse-debug ESP-IDF YAML fixtures validate and compile | See `tests/components/hwp/` |
| TEST-020 | Docker/devcontainer/CI runners | Done | POSIX, PowerShell, and GitHub Actions paths compile fixtures without tracked generated output | Docker remains CI default |
| TEST-030 | Python schema validation | Done | `climate.py` schema behavior covered by stdlib unittest | Runs in `./scripts/test-esphome.sh --local` |
| TEST-040 | Native C++ protocol harness | Done | Pure C++ tests run without ESP32 hardware, ESPHome runtime, FreeRTOS, or RMT | Covers inversion, checksums, and defrost/flow/restrict enum strings |
| TEST-050 | Protocol seam extraction | Done | Protocol helpers can be included by native tests without ESP32-only headers | Fan mode, enum strings, checksums, and inversion are covered in `protocol_core` |
| TEST-060 | Golden packet fixtures | Done | Curated `tmp/hwp` base/demo packets have a documented fixture format and checksum validation | Stored under `tests/fixtures/packets/`; frame decode/generate assertions continue under TST-034/TST-035/TST-052 |
| TEST-065 | Recent hardware log fixtures | Done | A small curated fixture set is extracted from the newest hardware log without importing full logs | `hwp_hardware_log_2025_06_24.json` covers representative unique RX/change packets from ignored `tmp/hwp/POOL_esphome_logs.log` |
| TEST-066 | Fixture-backed analysis CLI | Done | Analysis tooling can validate fixtures, parse logs, and prove fixture packets appear in hardware traces | `python -m analysis.hwp_analyze`; full recent log proves all valid hardware fixture packets |
| TEST-067 | Annotation window fixtures | Done | Manual tagger windows from hardware logs are parsed and curated into reusable proof fixtures | `hwp_annotated_fan_control_2024_11_01.json` covers F01/F02-F13 fan-control examples |
| TEST-068 | Packet read/write contracts | Done | Curated fan-control annotation fixtures prove observed read decode and passive write bytes | Annotation JSON now carries read/write expectations; native tests assert F01-F13 decode and command-byte mutation |
| TEST-069 | Runtime frame contracts | Done | Runtime frame structs match and parse the packet contracts | Adapter-backed native tests cover `FrameConf1/2/4/5` matching and F01-F13 parsing |
| TEST-071 | Passive runtime frame contracts | Done | Passive condition/status/clock/config frames match tracked fixtures and parsed fields agree with pure protocol helpers | Adapter-backed native tests cover `FrameConditions1/1B/2/2B/D`, `FrameClock`, `FrameConf3`, and `FrameConf6` |
| TEST-072 | ESP-IDF 5 RMT compile coverage | Done | Normal and pulse-debug ESPHome fixtures compile against the new RMT RX/TX driver path | Devcontainer compile confirmed `framework-espidf @ 3.50504.0 (5.5.4)` and no legacy RMT deprecation warning |
| TEST-070 | QEMU target test feasibility | Planned | Document install needs and prove one minimal ESP-IDF/ESP32 QEMU test app can run | Devcontainer has Debian `qemu-system-xtensa`, but not ESP-IDF or an ESP32 QEMU machine yet |
| TEST-080 | ESPHome host-platform feasibility | Blocked | Host compile/run path exists or blocker is documented | Current component is ESP32/RMT-bound |
| TEST-090 | Manual hardware-in-the-loop procedures | Done | Passive and active-control validation procedures are documented | See `docs/testing/manual-hil.md`; not default CI |

## Environment And Tooling

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| ENV-010 | Devcontainer | Done | VS Code devcontainer layers declared native/QEMU-adjacent tools on `ghcr.io/esphome/esphome:latest` with `/config`, `/build`, `/cache`, and PlatformIO volumes | Main development environment |
| ENV-020 | Generated file policy | Done | ESPHome, PlatformIO, cache, firmware, local YAML, and secrets paths are gitignored | Verify with `git status --short` after compiles |
| ENV-030 | User examples | Done | User-facing compile examples exist under `examples/` | Separate from test fixtures |
| ENV-040 | CI compile path | Done | GitHub Actions runs fixture compile through official ESPHome image | Python schema tests are local-only for now |
| ENV-050 | Native build tools | Done | Devcontainer declares `build-essential`, `cmake`, `ninja-build`, `pkg-config`, `qemu-system-misc`, and `qemu-utils` | Prevents local native/QEMU feasibility work from depending on incidental image contents |
| ENV-060 | Reference tree hygiene | Done | Copied research trees stay ignored and documented as reference-only | `tmp/` is ignored; see `docs/tmp-hwp-salvage.md` |

## Component Stabilization

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| CPP-010 | Current ESPHome climate schema/codegen | Done | Component validates and compiles with ESPHome 2026.4.5 | Python schema tests cover local config decisions |
| CPP-020 | Climate fan mode compatibility | Done | Standard/custom fan modes compile against current ESPHome APIs | Native tests should cover conversions next |
| CPP-030 | Climate/offline publishing behavior | Done | Heater does not report connected while offline; climate state publishes after refreshed fields | Hardware validation still needed |
| CPP-040 | Bus/task startup hardening | Done | Runtime state initializes and allocation/task creation failures are checked | Compile verified only |
| CPP-050 | Pulse debug flag | Done | Pulse logging is disabled by default and enabled with `HWP_PULSE_DEBUG` | Pulse-debug fixture compiles |
| CPP-060 | Queue cap behavior | Done | Queue enforces max length by dropping oldest entries | Native/FreeRTOS-seam tests still planned |
| CPP-070 | Fan parameter field review | Done | F02-F13 candidate fields from `tmp/hwp` are reviewed against fixtures before runtime changes | See `docs/protocol/fan-field-review.md` and fixture-backed candidate tests |
| CPP-080 | Fan parameter runtime mapping | Done | Missing F10/F11/F13 and F02-F09 frame fields are named in runtime structs with fixture-backed tests | Pure F10/F11 helpers are in `protocol_core`; runtime decode naming is merged without HA helper exposure or command generation |
| CPP-090 | Fan field schema/helper exposure | Done | Newly decoded fan fields can be exposed as optional helper entities with schema and compile coverage | F02-F09/F12/F13 number helpers and F10/F11 select helpers publish decoded values and feed command calls |
| CPP-100 | Fan field command parity | Done | Known fan config changes have expected command-frame bytes documented in tests | Restores tmp fan control surface for F02-F13; native byte helpers assert F10/F11/F12/F13 and representative F02/F08 packet mutations |
| CPP-110 | Final tmp closure | Done | Remaining tmp-only items are documented as merged, deferred, or rejected | `tmp/hwp` is archival reference only, not an active merge source |

## Protocol And Safety

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| PROTO-010 | Protocol notes organization | Planned | Protocol interpretation notes live under `docs/protocol/` | Keep `AGENTS.md` operational only |
| PROTO-020 | Golden packet fixture format | Done | Packet fixture schema is documented and easy to review | JSON fixture plus stdlib validation tests |
| PROTO-030 | Active command expectations | In Progress | Generated command bytes match known-safe expectations | Fan-control F01-F13 byte contracts are covered; broader active command expectations remain safety-sensitive |
| PROTO-040 | `tmp/hwp` salvage closure | Done | Useful copied-tree assets and merge guardrails are documented with final disposition | See `docs/tmp-hwp-salvage.md` |
| SAFETY-010 | Passive hardware validation | Done | Manual procedure documents setup and expected observations | See `docs/testing/manual-hil.md`; not default CI |
| SAFETY-020 | Active-control safety gates | Done | Procedure includes preconditions, rollback, and stop criteria | Compile success is not safety validation |
| SAFETY-030 | ESP-IDF 5 RMT migration | Done | Component migrates from deprecated legacy RMT driver or blocker is documented | New RX/TX path uses ESP-IDF 5 RMT channels and copy encoder; compile/native verified only, live bus validation still required |

## Governance

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| DOC-010 | Operational repo instructions | Done | `AGENTS.md` contains rules and links, not project narrative | |
| DOC-020 | Handover model | Done | `docs/handover.md` is concise and links to trackers | |
| DOC-030 | Feature tracker | Done | `docs/features.md` tracks status across testing, tooling, component, protocol, and safety work | |
| DOC-040 | Copied-tree salvage closure | Done | Future work can use `tmp/hwp` findings without redoing the source review | `tmp/hwp` remains ignored archival reference material |
