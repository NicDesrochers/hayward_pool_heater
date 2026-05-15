# HWP Simulator Hardware-In-The-Loop

The HWP simulator is a separate ESPHome firmware target for a separate ESP32 bridge device. It is meant to exercise the production HWP firmware with realistic packet cadence and fixture-backed command/echo behavior while keeping the control surface available through ESPHome native API entities.

This is a test aid, not a heater safety proof.

## Firmware Target

Use `examples/hwp-simulator.yaml` as the starting point:

```yaml
hwp_simulator:
  id: hwp_sim
  pin_txrx: GPIO16
  startup_playbook: normal_idle
  packet_buffer_size: 120
  active_on_boot: false
```

The simulator exposes:

- `select`: playbook, with `normal_idle`, `config_refresh`, `active_defrost_echo`, `rx_stress`, and `paused`
- `switch`: active/run state
- `number`: interval scale
- `button`: start, pause, step, reset, inject
- `text`: command input for agent commands such as `playbook normal_idle`, `step`, and `inject frame=config5_normal`
- diagnostics: current playbook, status, step, last frame, last RX frame, last echo, packet count, and error count

The simulator emits playbook packets with software-timed open-drain GPIO pulses
and listens for controller-originated packets through ESP-IDF 5 RMT RX on the
same half-duplex GPIO. Software TX is used because bench testing showed ESP-IDF
RMT TX could report completion on the simulator node without moving the shared
GPIO pad, while software GPIO pulses were visible and reliable.

Bus-sharing behavior is modeled after the protocol notes in
`components/hwp/PoolHeater.h`: heater packets are sent in repeated groups of
four with about 152 ms idle-high spacing, controller packets are decoded using
controller polarity and 100 ms repeat spacing, and simulator RX is disabled
while simulator TX owns the shared half-duplex line. Known command echoes are
scheduled after the controller burst instead of being emitted immediately.

The implemented wire reaction is deliberately narrow: checksum-valid controller
`CONFIG_5` D06 defrost ECO/NORMAL commands produce the fixture-backed heater
echo packets, and checksum-valid controller `CONFIG_1` packets update the
simulator's internal CONFIG_1 state for later heater-originated replay. Other
valid controller packets update diagnostics only; invalid packets increment
error counters and do not emit an echo.

## Wiring

Use two ESP32 devices:

- Production node: runs `components/hwp/`.
- Simulator node: runs `components/hwp_simulator/`.

Connect the configured HWP bus GPIOs through the same low-voltage bus interface circuit you use for bench testing. Do not connect either simulator or production firmware to a live heater during simulator HIL unless the procedure explicitly calls for it.

Power both devices from a known-safe bench supply or USB. Keep grounds common only where the interface circuit requires it.

The simulator configures its HWP GPIO as open-drain with the ESP32 internal
pull-up enabled so a short direct two-node bench connection has a defined
idle-high line. Treat that as a convenience for close bench testing only; for
real wiring lengths or noisy setups, prefer the same external pull-up/interface
circuit used for HWP bus validation.

## Agent Workflow

Prefer ESPHome native API over raw UART:

```sh
python -m analysis.hwp_sim_orchestrate --device <sim-node> list
python -m analysis.hwp_sim_orchestrate --device <sim-node> set-playbook normal_idle
python -m analysis.hwp_sim_orchestrate --device <sim-node> command step
python -m analysis.hwp_sim_orchestrate --device <sim-node> transcript --duration 60 --out sim-session.jsonl --firmware-device <firmware-node>
```

From the repo root, the CLI reads `.env` by default. If `SIMULATOR_NET_NAME`
and `SIMULATOR_API_KEY` are present, the simulator connection arguments can be
omitted:

```sh
python -m analysis.hwp_sim_orchestrate list
python -m analysis.hwp_sim_orchestrate command step
```

For oscilloscope bring-up, use the software GPIO diagnostic before chasing RMT
timing:

```sh
python -m analysis.hwp_sim_orchestrate command wiggle
```

`wiggle` drives the configured simulator GPIO low/high slowly five times. If it
is not visible at the probe point, verify the simulator YAML pin, wiring,
ground/reference, and pull-up/interface circuit before debugging packet timing.

Run production firmware logs separately from Home Assistant, ESPHome dashboard, or the firmware web dashboard at `/hwp`.

The transcript command subscribes to ESPHome native API state updates from the simulator node and, optionally, the production firmware node. It records JSONL entries with device, entity key/name/object id, entity kind, state value, and UTC timestamp. This is meant to help agents correlate simulator playbook steps, controller commands, simulator echoes, and firmware diagnostics without exposing raw UART passthrough.

For branch testing, use `external_components.refresh: 0s` or commit-pin both firmware targets so the ESPHome builder does not reuse stale external component code.

## Evidence Boundary

Simulator playbooks are built from tracked packet fixtures and active-TX evidence. They are useful for stability testing, decode regression checks, timing stress, and repeatable field-tool development.

They do not prove that a new active command is safe on real heater hardware. New active behavior still needs fixture evidence, supervised hardware validation, and documentation in `docs/testing/manual-hil.md`.
