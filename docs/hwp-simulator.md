# HWP Simulator Component

The `hwp_simulator` component builds a separate ESPHome firmware target for a
separate ESP32 bench device. It acts like a small, API-controlled heat-pump
side of the HWP bus so the production `hwp` firmware can be exercised without a
live heater.

This simulator is a test and discovery aid. It is not a heater safety proof.

## When To Use It

Use the simulator when you want to:

- replay known heater packets with realistic cadence
- test that the production HWP firmware stays stable while receiving traffic
- exercise known command/echo behavior in a repeatable bench setup
- collect API transcripts that agents and humans can inspect later

Do not use it to claim that a new active heater command is safe. New active
behavior still needs fixture evidence and supervised hardware validation.

## Hardware Setup

Use two ESP32 devices:

- Simulator node: runs `components/hwp_simulator/`.
- Production node: runs `components/hwp/`.

Connect the two HWP bus GPIOs through the same low-voltage half-duplex bus
interface circuit used for bench testing. Do not connect either node to a live
heater while running simulator HIL unless a specific manual procedure says so.

Keep the devices powered from USB or a known-safe bench supply. Share ground
only as required by the interface circuit.

The simulator biases its `pin_txrx` line high with the ESP32 internal pull-up
while driving the line open-drain. This helps direct two-node bench wiring,
where the real heater bus pull-up is absent. For longer wiring or noisy bench
setups, use the same external pull-up/interface circuit intended for the HWP
bus instead of relying only on the internal pull-up.

## Minimal YAML

Start from [examples/hwp-simulator.yaml](../examples/hwp-simulator.yaml).

```yaml
esphome:
  name: hwp-simulator
  friendly_name: HWP Simulator

logger:

api:

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

external_components:
  - source: github://sle118/hayward_pool_heater
    components: [hwp_simulator]
    refresh: 0s

esp32:
  board: esp32dev
  framework:
    type: esp-idf

hwp_simulator:
  id: hwp_sim
  pin_txrx: GPIO16
  startup_playbook: normal_idle
  packet_buffer_size: 120
  active_on_boot: false
```

For reproducible bench sessions, pin `external_components.source` to a commit
SHA instead of a moving branch once you know which build you want to validate.

## Configuration

| Option | Default | Notes |
|--------|---------|-------|
| `id` | Required by ESPHome if referenced | Component id. |
| `pin_txrx` | Required | Half-duplex HWP bus GPIO. RX is initialized before TX. |
| `startup_playbook` | `normal_idle` | Initial playbook after boot. |
| `packet_buffer_size` | `120` | Internal packet/history buffer size. Valid range is 8 to 512. |
| `active_on_boot` | `false` | Whether packet playback starts automatically after boot. |

Available playbooks:

| Playbook | Purpose |
|----------|---------|
| `paused` | No scheduled packet output. |
| `normal_idle` | Replays the observed heater cadence: `CONFIG_6`, `CONFIG_4`, `CONFIG_5`, fast condition/config frames, then `CONFIG_3`, `COND_2_B`, `COND_D`, and another fast condition/config cluster. |
| `config_refresh` | Favors configuration packets. |
| `active_defrost_echo` | Alternates CONFIG_5 normal/ECO echo examples. |
| `rx_stress` | Emits repeated fixture traffic for stability testing. |

## Bus Sharing And Timing

The simulator follows the documented HWP half-duplex sharing rules used by the
production component:

- Heater-originated simulator packets are repeated in groups of four.
- Heater repeat spacing is about 152 ms with the line idle high.
- The line remains idle high between heater groups; playbook delays provide the
  longer group cadence.
- Controller-originated packets are decoded as controller source, with the
  controller bit polarity and 100 ms repeat spacing. The production component
  sends controller packets in groups of eight.
- The simulator disables RX while it is transmitting, then re-enables RX on the
  same shared GPIO after the transmit burst.
- Known command echoes are delayed before transmit so the simulator does not
  talk over the controller burst. CONFIG_5 D06 echo uses the documented
  post-controller delay boundary instead of responding immediately.
- The default `normal_idle` playbook models the higher-level packet order seen
  in real heater logs: slower config/status groups are interleaved with repeated
  `COND_1`, `COND_2`, `CONFIG_2`, `CONFIG_1`, and `COND_1B` clusters.

This is still a bench approximation. It intentionally models the bus ownership,
repeat grouping, bit polarity, and idle-high spacing, but it is not a substitute
for supervised validation against a real heater.

## ESPHome Entities

The simulator exposes a control surface through ESPHome native API entities:

| Entity | Purpose |
|--------|---------|
| `HWP Simulator Playbook` select | Change the active playbook. |
| `HWP Simulator Active` switch | Start or pause scheduled playback. |
| `HWP Simulator Interval Scale` number | Speed up or slow down playback intervals. |
| `HWP Simulator Command` text | Send advanced commands. |
| `HWP Simulator Start` button | Start scheduled playback. |
| `HWP Simulator Pause` button | Pause scheduled playback. |
| `HWP Simulator Step Once` button | Emit one playbook step. |
| `HWP Simulator Reset` button | Reset scheduler state and counters. |
| `HWP Simulator Inject` button | Emit the next event manually. |
| `HWP Simulator Current Playbook` text sensor | Current playbook name. |
| `HWP Simulator Last Frame` text sensor | Last simulator-originated packet. |
| `HWP Simulator Last RX Frame` text sensor | Last controller-originated packet heard by the simulator. |
| `HWP Simulator Last Echo` text sensor | Last fixture-backed echo/action emitted in response to RX. |
| `HWP Simulator Status` text sensor | Current simulator status. |
| `HWP Simulator Step` sensor | Current scheduler step counter. |
| `HWP Simulator Packet Count` sensor | Count of emitted/accepted packets. |
| `HWP Simulator Error Count` sensor | Decode, checksum, or RX error count. |

## Text Commands

The `HWP Simulator Command` text entity accepts:

```text
playbook normal_idle
playbook config_refresh
playbook active_defrost_echo
playbook rx_stress
start
pause
step
wiggle
reset
inject frame=base-config-1
inject frame=base-config-5-normal
inject frame=base-config-5-eco-echo
inject frame=base-cond-2
```

Use `wiggle` as a bench wiring/scope diagnostic. It drives the configured
simulator GPIO low/high slowly five times using software GPIO, outside the RMT
packet encoder. If `wiggle` is visible on the scope but `step` is not, the fault
is in the RMT TX path. If neither is visible, check the configured pin, wiring,
ground/reference, and pull-up/interface circuit first.

Fixture packet ids currently include:

- `base-config-1`
- `base-config-2`
- `base-config-3`
- `base-config-4`
- `base-config-5-normal`
- `base-config-5-eco-echo`
- `base-config-6`
- `base-cond-1`
- `base-cond-1b`
- `base-cond-2`
- `base-cond-2b`
- `base-cond-d`
- `stress-invalid-checksum`

## RX And Echo Boundary

The simulator emits playbook packets with software-timed open-drain GPIO pulses
and listens for controller-originated packets through ESP-IDF 5 RMT RX on the
same configured GPIO. Software TX is used because bench testing showed ESP-IDF
RMT TX could report completion on the simulator node without moving the shared
GPIO pad, while software GPIO pulses were visible and reliable.

In the current implementation, simulator RX behavior is intentionally narrow:

- Checksum-valid controller `CONFIG_5` D06 defrost ECO/NORMAL commands produce
  the fixture-backed heater echo packets after the bus-sharing delay.
- Checksum-valid controller `CONFIG_1` packets update the simulator's internal
  CONFIG_1 state and are replayed by later heater-originated CONFIG_1 frames.
- Other valid controller packets update diagnostics only.
- Invalid checksum or invalid length packets increment the error counter and do
  not emit an echo.

This boundary keeps the simulator useful for stability testing without
inventing unproven heater behavior.

## Orchestration CLI

Install the optional annotator/API dependencies on the workstation that will run
the orchestration command:

```sh
python -m pip install -r requirements-annotator.txt
```

List simulator entities:

```sh
python -m analysis.hwp_sim_orchestrate --device hwp-simulator.local list
```

Change playbook and step once:

```sh
python -m analysis.hwp_sim_orchestrate --device hwp-simulator.local set-playbook normal_idle
python -m analysis.hwp_sim_orchestrate --device hwp-simulator.local command step
```

When running from the repo root, the CLI also reads `.env` by default. If that
file contains `SIMULATOR_NET_NAME` and `SIMULATOR_API_KEY`, the simulator
address and API key can be omitted:

```sh
python -m analysis.hwp_sim_orchestrate list
python -m analysis.hwp_sim_orchestrate command step
```

Capture a two-node API transcript:

```sh
python -m analysis.hwp_sim_orchestrate \
  --device hwp-simulator.local \
  transcript \
  --duration 60 \
  --out sim-session.jsonl \
  --firmware-device hayward-heater-test.local
```

If you pass `--firmware-device ""` and `.env` contains `TEST_DEVICE_NET_NAME`,
the CLI fills the firmware address and `TEST_DEVICE_API_KEY` from `.env`.

The transcript is JSONL. Each line records a simulator or firmware entity state
change with device, entity key/name/object id, entity kind, state, and UTC
timestamp.

## Compile Checks

From the devcontainer or an ESPHome environment:

```sh
esphome config examples/hwp-simulator.yaml
esphome compile examples/hwp-simulator.yaml
./scripts/test-esphome.sh --local --fixture examples/hwp-simulator.yaml
```

The normal project runner also validates and compiles the simulator fixture:

```sh
./scripts/test-esphome.sh --local
```

## Related Docs

- [Simulator HIL procedure](testing/simulator-hil.md)
- [Manual hardware validation gates](testing/manual-hil.md)
- [Protocol research backlog](protocol/research-backlog.md)
