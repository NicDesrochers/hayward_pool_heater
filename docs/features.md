# Feature Tracker

## Current Focus

The tmp merge track is closed. The current hardware-test focus has moved from reboot isolation to supervised field validation: ESP-IDF 5 RMT passive RX is stable on hardware, and CONFIG_5 defrost eco/normal active TX is now captured as reusable fixture evidence.

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
| TEST-073 | Active TX echo fixtures | Done | Successful active write/echo windows are tracked and validated as regression evidence | CONFIG_5 D06 defrost eco/normal commands and heater echoes validate checksums, source direction, requested bit value, and observed byte-4 normalization |
| TEST-074 | Annotated evidence inventory | Done | Tmp annotated logs and Arduino simulator packets are inventoried against tracked fixtures | Current scan found 65 annotation windows and 43 simulator packets; see `docs/protocol/evidence-inventory.md` |
| TEST-075 | Menu-to-packet protocol contracts | Done | Manual menu options map to frame/byte/encoding evidence before more active controls are added | `analysis/hwp_menu_map.py` and `docs/protocol/menu-packet-map.md` cover implemented F/D/R/U/H/S options |
| TEST-076 | CONFIG_1/CONFIG_3 demo command fixtures | Done | Demo command examples for R01-R07 and R09-R11 are tracked as menu-backed byte contracts | `hwp_demo_command_contracts.json` pins checksums, menu byte locations, and one-byte pairs where the source supports them |
| TEST-077 | CONFIG_1 extended setpoint regression | Done | R01/R02/R03 setpoints use extended temperature encoding through protocol helpers and runtime frames | Issue #11 regression fixture pins 33.5/34/35C edge bytes so high setpoints do not wrap to low single-digit values |
| TEST-078 | Fan edge annotation fixtures | Done | Remaining fan-control annotation edge values are tracked as read/write fixture contracts | F02 41.0, F03 15.5, F08 1, F10 coil source, F12 50, and F13 99/100 are now proven from the 2024-11-01 annotated hardware log |
| TEST-079 | Defrost demo command fixtures | Done | Demo command examples for D01, D05, and D06 are tracked as menu-backed passive byte contracts | `hwp_defrost_demo_command_contracts.json` pins simulator D01/D05/D06 checksums, menu byte locations, and one-byte pairs; live active-control claims remain limited to the D06 echo fixture |
| TEST-081 | COND_2 demo read fixture | Done | Remaining simulator `COND_2` temperature packet is tracked as passive read/decode evidence | `hwp_demo_packets.json` now includes `p_28`; native protocol and runtime frame tests assert outlet, coil, exhaust, and auxiliary temperature decode |
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
| CPP-120 | Hardware startup diagnostics | Done | HWP boots with bus startup enabled, and startup ordering avoids null data-model access | `start_bus_on_setup` remains available as a diagnostic config knob |

## Protocol And Safety

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| PROTO-010 | Protocol notes organization | Planned | Protocol interpretation notes live under `docs/protocol/` | Keep `AGENTS.md` operational only |
| PROTO-020 | Golden packet fixture format | Done | Packet fixture schema is documented and easy to review | JSON fixture plus stdlib validation tests |
| PROTO-030 | Active command expectations | In Progress | Generated command bytes match known-safe expectations | Fan-control F01-F13, CONFIG_1 R01/R02/R04-R07, CONFIG_2 D01, and CONFIG_5 D05/D06 byte contracts are covered; CONFIG_1 R01-R03 high setpoint encoding is regression-tested from issue #11; CONFIG_5 defrost eco/normal has fixture-backed live TX/echo evidence; broader active command expectations remain safety-sensitive |
| PROTO-040 | `tmp/hwp` salvage closure | Done | Useful copied-tree assets and merge guardrails are documented with final disposition | See `docs/tmp-hwp-salvage.md` |
| PROTO-050 | Menu-to-packet source of truth | Done | Technical manual menu options are linked to frames, byte locations, encodings, evidence, and safety status | Check `docs/protocol/menu-packet-map.md` before protocol or active-control changes |
| PROTO-060 | Protocol research backlog | Done | Unknown or uncertain fields have a human-review backlog instead of being forced into implementation | See `docs/protocol/research-backlog.md` |
| SAFETY-010 | Passive hardware validation | Done | Manual procedure documents setup and expected observations | See `docs/testing/manual-hil.md`; not default CI |
| SAFETY-020 | Active-control safety gates | Done | Procedure includes preconditions, rollback, and stop criteria | Compile success is not safety validation |
| SAFETY-030 | ESP-IDF 5 RMT migration | Done | Component migrates from deprecated legacy RMT driver or blocker is documented | New RX/TX path uses ESP-IDF 5 RMT channels at 312.5 kHz and copy encoder; passive RX is field-stable and CONFIG_5 defrost active TX has initial live validation |

## Governance

| ID | Feature | Status | Acceptance | Notes |
|----|---------|--------|------------|-------|
| DOC-010 | Operational repo instructions | Done | `AGENTS.md` contains rules and links, not project narrative | |
| DOC-020 | Handover model | Done | `docs/handover.md` is concise and links to trackers | |
| DOC-030 | Feature tracker | Done | `docs/features.md` tracks status across testing, tooling, component, protocol, and safety work | |
| DOC-040 | Copied-tree salvage closure | Done | Future work can use `tmp/hwp` findings without redoing the source review | `tmp/hwp` remains ignored archival reference material |
| DOC-050 | Success stories | Done | Community installation reports are preserved with local assets and source provenance | `docs/success-stories/hp55tr-e08-bypass.md` documents discussion #9 |
