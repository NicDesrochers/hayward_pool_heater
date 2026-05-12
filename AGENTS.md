# AGENTS.md

## Repo Purpose

ESPHome external component for a Hayward pool heat pump controller.

## Ground Rules

- Keep operational instructions here. Put project narrative, protocol notes, research, and review history under `docs/`.
- Keep real ESPHome device YAML and `secrets.yaml` in `.esphome-config/`; this folder is host-persistent and gitignored.
- Do not commit generated ESPHome, PlatformIO, cache, or firmware build output.
- Prefer the official Docker image or the devcontainer layered on `ghcr.io/esphome/esphome:latest` for build verification.
- Keep `ESPHOME_BUILD_PATH=/build` when using Docker/devcontainer so firmware projects do not land in the repo.
- Treat hardware-facing behavior conservatively. Compile success is not proof that active heater control is safe on real equipment.
- When closing a slice or answering status questions, include suggested next step(s) where appropriate.
- New source files should include the project copyright/license notice; use `components/hwp/FrameConf5.h` as the canonical example.

## Important Paths

- `components/hwp/`: ESPHome external component implementation.
- `examples/`: user-facing compile examples.
- `tests/components/hwp/`: ESPHome compile/config fixtures and Python schema tests.
- `.devcontainer/`: VS Code devcontainer definition.
- `.esphome-config/`: local persistent ESPHome configs and secrets, gitignored.
- `docs/handover.md`: short current-state handover and next recommended slice.
- `docs/features.md`: feature tracker and cross-cutting roadmap.
- `docs/governance.md`: documentation and status-tracking rules.
- `docs/testing/`: test strategy, backlog, and testing notes.
- `documents/`: manuals, photos, schematics, and source reference material.

## Agent Startup

For a new slice, read in this order:

1. `AGENTS.md`
2. `docs/handover.md`
3. `docs/features.md`
4. The focused tracker for the slice, usually `docs/testing/backlog.md`

Keep `docs/handover.md` concise. Move durable narrative and completed work history into `docs/features.md` or focused docs.
See `docs/governance.md` before changing the documentation model.

## Current Verification Commands

From the devcontainer:

```sh
esphome version
python -m unittest discover -s tests -p 'test_*.py'
./scripts/test-native.sh
./scripts/test-esphome.sh --local
git diff --check
git status --short
```

From Docker on Windows PowerShell:

```powershell
.\scripts\test-esphome.ps1
```

## Generated File Policy

Expected local-only paths include:

- `.esphome-config/`
- `.esphome/`
- `build/`
- `esphome_build/`
- `.cache/`
- PlatformIO cache/build output
- `*-local.yaml`
- `*-secrets.yaml`

After any compile, run `git status --short` and confirm no generated tracked files were created.

## Testing Direction

- Use ESPHome-style YAML compile fixtures as the baseline test contract.
- Add native C++ unit tests only for protocol logic that can run without ESP32 hardware or a live ESPHome runtime.
- Keep real hardware validation as documented manual hardware-in-the-loop procedures, not as default CI.

See `docs/testing/strategy.md` and `docs/testing/backlog.md` before adding test infrastructure.
