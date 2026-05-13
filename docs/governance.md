# Governance Model

## Goal

Keep agent startup cheap. `AGENTS.md` stays operational, `docs/handover.md` stays short and current, and durable project narrative lives in focused tracker docs.

## Source Of Truth

- `AGENTS.md`: repo rules, important paths, default verification commands.
- `docs/handover.md`: current state, next recommended slice, latest verification, active risks.
- `docs/features.md`: feature/status tracker and cross-cutting roadmap.
- `docs/testing/strategy.md`: durable testing approach.
- `docs/testing/backlog.md`: detailed testing task table.
- `docs/protocol/menu-packet-map.md`: manual menu option to packet/frame contract.
- `documents/`: manuals, photos, schematics, and source material.

## Status Values

- `Planned`: agreed direction, not implemented.
- `In Progress`: actively being changed.
- `Done`: implemented and verified.
- `Blocked`: waiting on a dependency, decision, hardware, or upstream support.
- `Deferred`: intentionally out of the current project slice.

## Feature Tracking

Track project work in `docs/features.md` with stable IDs:

- `ENV-*`: devcontainer, Docker, generated file policy, build environment.
- `TEST-*`: testing infrastructure and coverage.
- `CPP-*`: C++ component/runtime behavior.
- `PROTO-*`: protocol interpretation, golden packets, command generation.
- `SAFETY-*`: hardware-facing safety gates and manual hardware-in-the-loop procedures.
- `DOC-*`: docs, governance, handover.

Feature rows should be short. Put details in a linked doc only when they are needed for implementation.

## Handover Rules

- Keep `docs/handover.md` under one screen when possible.
- Link to trackers instead of copying tracker history.
- Update handover only when the current next slice, verification state, or active risks change.
- Move completed narrative into `docs/features.md`, `docs/testing/backlog.md`, or a focused topic doc.
- Do not store secrets, real device configs, generated build output, or local cache paths in handover.

## Slice Workflow

1. Read `AGENTS.md`, then `docs/handover.md`.
2. Check `docs/features.md` and the relevant focused tracker.
3. For protocol, frame, helper, or active-control changes, check `docs/protocol/menu-packet-map.md` and update it when the menu contract changes.
4. Make the smallest coherent change for the current slice.
5. Run verification from `AGENTS.md` or the focused tracker.
6. Update only the tracker rows and handover facts affected by the slice.
