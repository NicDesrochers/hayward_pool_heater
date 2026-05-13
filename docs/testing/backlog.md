# Testing Backlog

Status values:

- `Planned`: agreed direction, not implemented.
- `In Progress`: being actively changed.
- `Done`: implemented and verified.
- `Blocked`: waiting on a dependency or decision.

## Governance

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| GOV-001 | Repo instructions | Governance | Done | `AGENTS.md` exists and contains only operational instructions | Narrative belongs in `docs/` |
| GOV-002 | Testing strategy | Governance | Done | Strategy document defines layers and slices | See `docs/testing/strategy.md` |
| GOV-003 | Handover | Governance | Done | Current status and next slices are documented | See `docs/handover.md` |
| GOV-004 | Feature tracker | Governance | Done | Cross-cutting feature status is tracked outside handover | See `docs/features.md` |
| GOV-005 | Governance model | Governance | Done | Docs define source-of-truth and handover rules | See `docs/governance.md` |
| GOV-006 | Tmp merge closure | Governance | Done | `tmp/hwp` has final merged/deferred/rejected disposition | See `docs/tmp-hwp-salvage.md` |

## ESPHome Compile Fixtures

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| TST-001 | Minimal hwp config | ESPHome config/compile | Done | `tests/components/hwp/test.esp32-idf.yaml` validates and compiles | Verified with Docker runner |
| TST-002 | Pulse debug build | ESPHome config/compile | Done | Compile passes with `-DHWP_PULSE_DEBUG` | Verified with Docker runner |
| TST-003 | Shared fixture structure | ESPHome config/compile | Done | Common fixture avoids duplicated YAML without hiding test intent | Uses `common.yaml` and substitutions |
| TST-004 | Generated file cleanliness | Integration | Done | Test script fails if compile leaves tracked generated output | Runner compares git status before and after |

## Runner And CI

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| TST-010 | PowerShell runner | Tooling | Done | `scripts/test-esphome.ps1` runs validation and compile via Docker | Verified locally |
| TST-011 | POSIX runner | Tooling | Done | `scripts/test-esphome.sh` runs equivalent checks | Syntax checked locally; used by CI |
| TST-012 | GitHub Actions | CI | Done | CI validates and compiles ESPHome fixtures | Added workflow using official ESPHome Docker image |
| TST-013 | Cache policy | CI | Done | CI caches only rebuildable PlatformIO/ESPHome caches | Uses temporary runner directories; no secrets or real configs |

## Python Config Validation

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| TST-020 | Minimal schema | Python validation | Done | Minimal valid config passes schema validation | Verified with devcontainer-local unittest |
| TST-021 | Required pin | Python validation | Done | Missing `pin_txrx` fails with a useful validation error | Verified with devcontainer-local unittest |
| TST-022 | Update interval lower bound | Python validation | Done | Values below 10 seconds fail | Existing constraint is covered |
| TST-023 | Update interval upper bound | Python validation | Done | Values above 1800 seconds fail | Existing constraint is covered |
| TST-024 | Helper entities | Python validation | Done | Optional helper entities validate when enabled | Covers default helpers plus explicit sensor/number/select config |

## Native C++ Protocol Tests

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| TST-030 | Fan mode conversion | Native C++ unit | Done | Standard and custom fan modes map correctly | Covers raw values, custom strings, unknown formatting, and invalid raw fallback |
| TST-031 | Enum string conversion | Native C++ unit | Done | Defrost, flow meter, and mode restriction strings parse correctly | Includes invalid-string defaults and boolean helpers |
| TST-032 | Packet checksum | Native C++ unit | Done | Known packets produce expected checksums | Covers short and long checksum behavior plus invalid lengths |
| TST-033 | Packet inverse | Native C++ unit | Done | Inversion round-trips packet bytes | Covers requested-length inversion without mutating the full backing array |
| TST-034 | Frame matching | Native C++ unit | Done | Known packets specialize to expected frame classes | Adapter-backed native tests cover `FrameConf1`, `FrameConf2`, `FrameConf4`, and `FrameConf5` |
| TST-035 | Frame parsing | Native C++ unit | Done | Parsed `heat_pump_data_t` fields match golden expectations | F01-F13 runtime parses are compared with `protocol_core` packet-contract helpers |
| TST-036A | Fan field candidate review | Python fixture | Done | F02-F13 candidate byte mappings are documented and fixture-backed | Covers `base-fan`, `base-type-84`, and `base-conf-a` |
| TST-036B | Fan field runtime decode | Native C++ / ESPHome compile | Done | F10/F11 helpers are native-tested and F02-F09/F10/F11/F13 runtime field naming compiles in ESPHome fixtures | Decode-only; helper exposure and command generation remain separate |
| TST-036C | Fan helper schema exposure | Python validation / ESPHome compile | Done | Newly decoded fan fields validate as helper entities and compile in both fixtures | Helpers now feed fan command calls for F02-F13 |
| TST-036 | Command generation | Native C++ unit | Done | Control calls generate expected command frame bytes | Native byte helpers cover F10/F11/F12/F13 and representative F02/F08 mutations; keep hardware safety notes nearby |
| TST-036D | Passive frame matching | Native C++ unit | Done | Passive condition/status/clock/config packets specialize to expected runtime frame classes | Covers `COND_1`, `COND_1B`, `COND_2`, `COND_2_B`, `COND_D`, `CLOCK`, `CONFIG_3`, and `CONFIG_6` |
| TST-036E | Passive frame parsing | Native C++ unit | Done | Runtime parsed passive fields match pure protocol helpers | Covers inlet/outlet/coil/exhaust temperatures, S02 water flow, and config-3 setpoint limits |
| TST-037 | Decoder pulse classification | Native C++ unit | Done | Synthetic RMT pulses classify as start/short/long/end | Uses component-local `hwp_pulse_symbol_t`; covers invalid and null/edge handling without a real RMT driver |
| TST-038 | Queue cap behavior | Native C++ unit | Planned | Queue enforces max length and drops oldest | Needs FreeRTOS stub or abstraction |
| TST-039 | Protocol seam | Native C++ unit | Done | Pure protocol helpers build without ESPHome, FreeRTOS, GPIO, or RMT dependencies | Initial `protocol_core` seam enables native tests and later golden packet coverage |
| TST-040 | Native test runner | Native C++ unit | Done | A devcontainer-local command runs pure C++ tests | `scripts/test-native.sh` uses direct `g++` and assert-based tests |
| TST-041 | QEMU feasibility probe | Target/QEMU | Planned | QEMU prerequisites and a minimal proof path are documented | Devcontainer now declares Debian `qemu-system-xtensa`; `idf.py`, `IDF_PATH`, and an ESP32 QEMU machine remain unresolved |
| TST-042 | ESPHome host feasibility | Host integration | Blocked | Host-platform blockers are documented or host compile fixture exists | Current component is ESP32/RMT-bound |
| TST-043 | ESP-IDF 5 RMT compile coverage | ESPHome config/compile | Done | Normal and pulse-debug fixtures compile using ESP-IDF 5 RMT RX/TX APIs | Confirmed `framework-espidf @ 3.50504.0 (5.5.4)` in devcontainer compile logs; passive RX and CONFIG_5 defrost active TX have initial supervised hardware validation |

## Golden Packet And Hardware Validation

| ID | Area | Test Type | Status | Acceptance | Notes |
|----|------|-----------|--------|------------|-------|
| TST-050 | Golden packet fixture format | Fixture design | Done | Packet fixture schema is documented and easy to review | JSON fixtures validate with stdlib Python |
| TST-051 | Curated passive/demo frames | Golden packet | Done | Known passive/demo frames validate consistently | Seeded from `tmp/hwp/analysis/simulator/DemoFrames.h`; includes one explicit invalid checksum negative fixture |
| TST-052 | Active command frames | Golden packet | Planned | Generated command bytes match known-safe expectations | Treat as safety-sensitive |
| TST-053 | Recent hardware log fixtures | Golden packet | Done | Curated unique RX/change frames from the newest hardware log validate as packet fixtures | Tracks a small JSON subset only; the full ignored log stays out of git |
| TST-054 | Fixture-backed analysis CLI | Analysis tooling | Done | CLI validates fixtures, parses ESPHome HWP logs, and proves tracked packets appear in logs | `python -m analysis.hwp_analyze prove --input tmp/hwp/POOL_esphome_logs.log --fixture tests/fixtures/packets/hwp_hardware_log_2025_06_24.json` |
| TST-055 | Annotation window fixtures | Analysis tooling / Golden packet | Done | Manual tagger windows parse as first-class evidence and prove against the source log | Covers curated F01/F02-F13 windows from `POOL_esphome_logs.log.2024-11-01` |
| TST-056 | Packet read/write contracts | Analysis tooling / Native C++ unit | Done | Fan-control annotation fixtures prove read decode and passive write bytes | F01-F13 read helpers and command mutation helpers are pinned to hardware-log-derived examples |
| TST-057 | Active TX echo fixtures | Analysis tooling / Golden packet | Done | Successful live write/echo windows are captured as reusable fixture evidence | CONFIG_5 defrost eco/normal command and heater echo packets are tracked under `tests/fixtures/active_tx/`; validation documents byte-4 heater normalization |
| TST-058 | Annotated evidence inventory | Analysis tooling / Golden packet | Done | Ignored annotated logs and Arduino simulator packets can be inventoried against tracked fixtures | `python -m analysis.hwp_analyze evidence --limit 25`; see `docs/protocol/evidence-inventory.md` |
| TST-059 | Menu-to-packet contracts | Analysis tooling / Golden packet | Done | Implemented menu options have frame, byte/bit, encoding, evidence, and safety status metadata | `analysis/hwp_menu_map.py`; `python -m analysis.hwp_analyze evidence --menu --limit 25` |
| TST-059A | CONFIG_1/CONFIG_3 demo command contracts | Analysis tooling / Native C++ unit | Done | Demo command packets validate menu byte locations and passive write/read contracts | R01/R02/R04-R07 have one-byte pair contracts; R03 and R09-R11 are fixture-backed read evidence without enabling new live writes |
| TST-060 | Manual passive test | Manual hardware-in-the-loop | Done | Procedure documents setup and expected observations | See `docs/testing/manual-hil.md`; not default CI |
| TST-061 | Manual active-control smoke test | Manual hardware-in-the-loop | Done | Procedure includes safety gates and rollback steps | CONFIG_5 defrost eco/normal passed supervised TX/echo smoke testing; broader settings remain one-at-a-time validation |
