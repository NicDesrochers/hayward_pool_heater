# ESPHome Testing Strategy

## Goal

Build a test program that follows ESPHome conventions first, then adds faster unit coverage around this component's protocol-heavy logic. The baseline contract is that representative YAML configs validate and compile against the current stable ESPHome Docker image.

## Test Layers

### 1. ESPHome Config And Compile Fixtures

This is the standard ESPHome component testing layer. Fixtures should live under:

```text
tests/components/hwp/
```

Initial fixtures:

- `common.yaml`: shared external component and entity configuration.
- `test.esp32-idf.yaml`: minimal ESP32 ESP-IDF compile target.
- `test.esp32-idf-pulse-debug.yaml`: same target with `-DHWP_PULSE_DEBUG`.

Acceptance:

- `esphome config` passes for each fixture.
- `esphome compile` passes for each fixture.
- Compiles do not create tracked generated files in the repo.

### 2. Runner Scripts

Add scripts so local development, devcontainer use, and CI use the same commands.

Candidate scripts:

- `scripts/test-esphome.ps1`
- `scripts/test-esphome.sh`

Expected checks:

- Print `esphome version`.
- Validate all fixture YAML files.
- Compile all fixture YAML files.
- Verify `git status --short` does not show generated build output.

The scripts should support Docker as the default stable path and optionally a local ESPHome executable for faster inner-loop work.

### 3. CI

Use `ghcr.io/esphome/esphome:latest` for CI so the test surface matches the devcontainer and local Docker workflow.

Initial CI should stay small:

- Validate and compile ESP32 ESP-IDF fixture.
- Validate and compile pulse-debug fixture.
- Cache only rebuildable PlatformIO and ESPHome cache data.
- Never cache `.esphome-config/` or secrets.

Later CI can pin a known-good ESPHome image in addition to `latest` if upstream breakage becomes noisy.

### 4. Python Config Validation Tests

The component schema in `components/hwp/climate.py` should eventually have focused validation coverage.

Candidate cases:

- Minimal valid config.
- Missing `pin_txrx`.
- Invalid `update_interval` below 10 seconds.
- Invalid `update_interval` above 1800 seconds.
- Helper entity declarations enabled and disabled.
- Default entity naming and icon assumptions.

These tests should avoid duplicating ESPHome internals. Use them to cover local schema decisions and defaults.

### 5. Native C++ Unit Tests

Native C++ tests are not the first ESPHome baseline, but they are valuable for this repo because most risk lives in protocol parsing and frame generation.

Recommended track:

1. Add a native Linux C++ harness for pure protocol helpers.
2. Extract or isolate protocol code so tests do not include ESPHome, FreeRTOS, GPIO, or hardware RMT headers.
3. Add golden packet fixtures once parse/generate behavior has a stable seam.
4. Evaluate QEMU target tests only after the protocol seam exists.
5. Keep ESPHome `host:` platform work separate from QEMU; the current component is ESP32/RMT-bound and is not host-ready.

Good candidates:

- `FanMode` standard/custom fan mode conversion.
- `DefrostEcoMode`, `FlowMeterEnable`, and `HeatPumpRestrict` string conversion.
- Packet checksum calculation and inverse behavior.
- Temperature, decimal, and bitfield helper encoding.
- Frame `matches()`, `parse()`, `control()`, and `format()` behavior.
- `Decoder` pulse classification using synthetic component-local `hwp_pulse_symbol_t` values.
- `SpinLockQueue` max-size and drop-oldest behavior, with FreeRTOS calls isolated or stubbed.

Avoid deep native tests for `PoolHeater` and `Bus` until hardware/runtime dependencies are better isolated.

### 6. Golden Packet Tests

Golden tests should use captured packet examples and assert stable protocol behavior.

Recommended fixture shape:

```text
tests/fixtures/packets/
```

Each golden case should record:

- Raw packet bytes.
- Source direction when known.
- Expected frame class.
- Expected parsed fields.
- Expected checksum status.
- Expected generated command bytes when applicable.

Keep protocol interpretation notes in `docs/protocol/`, not in `AGENTS.md`.

### 7. Hardware-In-Loop And Manual Tests

Real heater validation should be documented but not required for default CI.

Manual hardware-in-the-loop procedures should cover:

- Passive bus monitoring.
- Safe active-control smoke tests.
- Offline/online transition behavior.
- Frame queue behavior under bursty command input.
- Recovery after invalid or partial frames.

### 8. QEMU And ESPHome Host Feasibility

QEMU is useful for target-style ESP-IDF tests, but it should not be the first native test layer for this component. The devcontainer now declares Debian's `qemu-system-xtensa` package, but it still does not provide `idf.py`, `IDF_PATH`, or an ESP32-specific QEMU machine. The component also currently depends on ESP32/RMT behavior.

QEMU acceptance for a future slice:

- Document required devcontainer packages and ESP-IDF setup.
- Prove one minimal ESP32 QEMU test app can build and run.
- Keep QEMU tests non-default until they are reliable in the devcontainer and CI.
- Use QEMU for target/runtime smoke tests, not for the fastest protocol unit tests.

ESPHome `host:` platform acceptance for a future slice:

- Document which component dependencies block host compilation.
- Add mocks or conditional compile seams only where they also improve protocol testability.
- Do not weaken the ESP32 compile fixtures to make host builds pass.

## Slice Plan

### Slice 0: Governance And Handover

Add:

- `AGENTS.md`
- `docs/testing/strategy.md`
- `docs/testing/backlog.md`
- `docs/handover.md`

### Slice 1: ESPHome Compile Fixtures

Add `tests/components/hwp/` fixture YAMLs modeled after ESPHome component tests.

### Slice 2: Test Runner Scripts

Add Docker-backed scripts for local/devcontainer/CI parity.

### Slice 3: CI

Add GitHub Actions for fixture validation and compile.

### Slice 4: Config Validation Tests

Add focused Python tests for local schema behavior.

### Slice 5: Native C++ Protocol Tests

Add a lightweight C++ test harness for pure protocol logic.

### Slice 6: Protocol Seam Extraction

Separate pure protocol helpers from ESPHome, FreeRTOS, GPIO, and RMT dependencies.

### Slice 7: Golden Packet Tests

Add captured frame fixtures and expected parse/generate assertions.

### Slice 8: QEMU And Host Feasibility

Document and probe QEMU/ESPHome host test options after the native protocol seam exists.

### Slice 9: Hardware-In-Loop Notes

Document real-device validation procedures and safety gates.

## Current Constraints

- The component targets ESP32 and uses ESP-IDF 5 RMT RX/TX APIs.
- ESP-IDF framework is the current compile target.
- ESPHome compile success verifies integration, not electrical safety or live heater behavior.
- `.esphome-config/` is critical local data and must remain host-persistent and untracked.
