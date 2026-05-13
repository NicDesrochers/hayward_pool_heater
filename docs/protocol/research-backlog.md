# Protocol Research Backlog

This backlog tracks protocol observations that are not ready to become runtime
behavior, helper entities, or command contracts. It is meant for human review
using logs, annotations, manuals, hardware observations, and the analysis tools.

Use this file when evidence is interesting but uncertain. Do not convert an item
into implementation until it has a clear field hypothesis, packet source,
decoder expectation, and safety status.

## Evidence Levels

- `Observed`: packet bytes or log output exist, but field meaning is unknown.
- `Annotated`: a human marked a packet window while checking a menu/status value.
- `Fixture-backed`: tracked fixtures prove packet shape/checksum/read behavior.
- `Menu-mapped`: field is tied to a technical-manual menu/status item.
- `Command-backed`: controller-originated or simulator command bytes exist.
- `Live-echo-backed`: supervised hardware write and heater echo exist.

Read-only menu/status observations can reach `Annotated`, `Fixture-backed`, and
`Menu-mapped`, but they should not be treated as `Command-backed` without a
separate command packet or simulator command example.

## Open Items

| ID | Area | Evidence | Current State | Human Work Needed | Implementation Gate |
|----|------|----------|---------------|-------------------|---------------------|
| RES-001 | `COND_D` / `0xDD` fields | Arduino simulator `p_30`; hardware logs show repeated `COND_D` packets | Packet shape and checksum are known, but field meanings are unclear | Compare `COND_D` changes against heater display/status screens and operating state; identify whether bytes map to errors, counters, temperatures, or state bits | Add fixture read contracts only after at least one field has a named hypothesis |
| RES-002 | `COND_2` / `0xD2` temperature edge evidence | Arduino simulator `p_28`; 2024-10-31 annotation windows | Current decode matches observed log output for common temperatures | Find higher/edge temperature values that distinguish short vs extended temperature encoding, if available | Add regression fixture only for the specific decode claim proven by the source |
| RES-003 | `CLOCK` / `0xCF` controller frame | 2024-10-31 annotation windows around time changes | Frame is parsed as controller clock; time byte behavior appears visible | Confirm byte layout from multiple minute/hour/day/month transitions | Add passive clock field contracts after layout is confirmed |
| RES-004 | `U01` flow meter enable | Implemented CONFIG_5 bit; no dedicated tracked command fixture yet | Field is named in runtime but evidence is weaker than fan/defrost fields | Find simulator, annotation, or hardware echo evidence for U01 changes | Require command-byte fixture before broadening active-control claims |
| RES-005 | `U02` pulses per liter | Implemented CONFIG_5 byte; candidate future active TX | Runtime field exists; active behavior remains safety-sensitive | Capture command and echo packets during supervised hardware change; watch for adjacent CONFIG_5 normalization | Add active-TX fixture before claiming field operation |
| RES-006 | `D02`/`D03`/`D04` defrost fields | Runtime CONFIG_2 fields and manual descriptions exist | Implemented but no dedicated tracked command fixture | Locate simulator or annotated menu examples for each field | Add passive byte fixtures before active validation |

## Analysis Tooling Follow-Up

The current headless CLI can parse logs, validate packet fixtures, prove fixture
presence in logs, and inventory annotation/demo evidence. Future tooling work
should help humans close the backlog above:

- Generate candidate byte-diff reports for selected annotation windows.
- Group repeated packets by frame type and changing byte positions.
- Compare annotated read-only menu/status values against decoded fixture fields.
- Emit draft fixture snippets for human review without automatically accepting
  field meanings.
- Keep full logs ignored; only curated fixtures and notes should be tracked.

