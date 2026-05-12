# Active TX Fixtures

These fixtures capture supervised live command/echo observations.

They are different from passive packet fixtures: each transaction records the
controller command bytes, the heater echo bytes, the target field, and any
explicitly observed heater byte normalization.

The first fixture covers CONFIG_5 D06 defrost eco/normal writes from hardware
testing on 2026-05-12. It proves only that narrow command path; broader active
controls still require one-at-a-time supervised validation.
