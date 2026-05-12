# Manual Hardware-In-The-Loop Validation

## Purpose

Compile, schema, fixture, and native byte tests are necessary but not sufficient for real heater safety. The tmp Arduino simulator frames and recent ESPHome logs provide hardware-derived packet evidence; this procedure records the minimum manual gates before claiming a live control behavior is operationally safe.

## Passive Validation

1. Use a known-good wiring setup and keep active mode disabled.
2. Confirm ESPHome boots, logs frames, and does not enqueue control frames.
3. Confirm decoded climate state, temperatures, flow, fan fields, and helper entities update from heater-originated packets.
4. Confirm offline/online transitions do not publish connected or stale state as current truth.
5. Capture logs for any unknown frames or checksum failures and convert them into fixtures before changing decode logic.

## Active-Control Smoke Test

Run active-control tests only when the heater can be supervised locally and stopped quickly.

Preconditions:

- Passive validation has already passed in the same wiring setup.
- The heater is in a safe operating state for the setting being changed.
- The operator knows how to disable active mode, power down the controller, and restore keypad settings.
- Only one setting is changed at a time.
- The expected command bytes are already covered by tests or reviewed against fixtures.

Procedure:

1. Enable active mode.
2. Change one low-risk helper or climate setting.
3. Watch the queued command log and the next heater-originated config frame.
4. Confirm the heater echoes the expected value and no unrelated fields changed.
5. Disable active mode after the observation window.

Stop criteria:

- Unexpected command bytes are logged.
- Heater state changes outside the targeted field.
- Unknown, invalid, or repeated frames appear after a command.
- Physical heater behavior is surprising or unsafe.

## Fan Control Notes

F02-F13 fan controls have compile coverage and native byte-helper tests based on hardware-derived packet evidence. Start with read/echo validation and the least disruptive settings before touching fan voltage limits or timing behavior.
