# Copyright (c) 2024 S. Leclerc (sle118@hotmail.com)
#
# This file is part of the Pool Heater Controller component project.
#
# @project Pool Heater Controller Component
# @developer S. Leclerc (sle118@hotmail.com)
# @license MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .hwp_fixtures import (
    REPO_ROOT,
    SUPPORTED_LENGTHS,
    FixtureValidationError,
    calculate_checksum,
    format_hex_byte,
    parse_hex_byte,
)


DEFAULT_ACTIVE_TX_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "active_tx"
DEFAULT_ACTIVE_TX_FIXTURE = (
    DEFAULT_ACTIVE_TX_FIXTURE_DIR / "hwp_active_tx_config5_defrost_2026_05_12.json"
)


@dataclass(frozen=True)
class ActiveTxPacket:
    label: str
    source: str
    length: int
    frame_type: str
    bytes: tuple[int, ...]
    checksum_valid: bool
    expected_checksum: int

    @property
    def byte_key(self) -> tuple[int, ...]:
        return self.bytes


@dataclass(frozen=True)
class ActiveTxTarget:
    frame_type: str
    raw_byte_index: int
    raw_bit_index: int
    raw_bit_value: int


@dataclass(frozen=True)
class ActiveTxNormalization:
    byte_index: int
    command_value: int
    echo_value: int
    notes: str


@dataclass(frozen=True)
class ActiveTxTransaction:
    fixture_name: str
    id: str
    label: str
    notes: str
    field: str
    requested_value: str
    target: ActiveTxTarget
    command: ActiveTxPacket
    echo: ActiveTxPacket
    allowed_echo_normalizations: tuple[ActiveTxNormalization, ...]


@dataclass(frozen=True)
class ActiveTxFixtureFile:
    path: Path
    schema_version: int
    source: str
    provenance: str
    transactions: tuple[ActiveTxTransaction, ...]

    @property
    def name(self) -> str:
        return self.path.name


def load_active_tx_fixture_file(path: Path | str) -> ActiveTxFixtureFile:
    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as fixture_file:
        raw_fixture = json.load(fixture_file)

    schema_version = raw_fixture.get("schema_version")
    source = raw_fixture.get("source")
    provenance = raw_fixture.get("provenance")
    raw_transactions = raw_fixture.get("transactions")

    if schema_version != 1:
        raise FixtureValidationError(
            f"{fixture_path}: unsupported schema_version {schema_version!r}"
        )
    if not isinstance(source, str) or not source:
        raise FixtureValidationError(f"{fixture_path}: missing source")
    if not isinstance(provenance, str) or not provenance:
        raise FixtureValidationError(f"{fixture_path}: missing provenance")
    if not isinstance(raw_transactions, list) or not raw_transactions:
        raise FixtureValidationError(f"{fixture_path}: missing transactions")

    transactions = tuple(
        _parse_transaction(fixture_path.name, transaction)
        for transaction in raw_transactions
    )
    _validate_unique_transaction_ids(fixture_path.name, transactions)
    return ActiveTxFixtureFile(
        path=fixture_path,
        schema_version=schema_version,
        source=source,
        provenance=provenance,
        transactions=transactions,
    )


def load_active_tx_fixture_files(
    fixture_dir: Path | str = DEFAULT_ACTIVE_TX_FIXTURE_DIR,
) -> tuple[ActiveTxFixtureFile, ...]:
    paths = sorted(Path(fixture_dir).glob("hwp_*.json"))
    return tuple(load_active_tx_fixture_file(path) for path in paths)


def all_active_tx_transactions(
    fixtures: tuple[ActiveTxFixtureFile, ...],
) -> tuple[ActiveTxTransaction, ...]:
    return tuple(transaction for fixture in fixtures for transaction in fixture.transactions)


def command_echo_differences(transaction: ActiveTxTransaction) -> dict[int, tuple[int, int]]:
    return {
        index: (command_value, echo_value)
        for index, (command_value, echo_value) in enumerate(
            zip(transaction.command.bytes, transaction.echo.bytes)
        )
        if index != transaction.command.length - 1 and command_value != echo_value
    }


def allowed_normalization_differences(
    transaction: ActiveTxTransaction,
) -> dict[int, tuple[int, int]]:
    return {
        normalization.byte_index: (
            normalization.command_value,
            normalization.echo_value,
        )
        for normalization in transaction.allowed_echo_normalizations
    }


def _validate_unique_transaction_ids(
    fixture_name: str, transactions: tuple[ActiveTxTransaction, ...]
) -> None:
    seen: set[str] = set()
    for transaction in transactions:
        if transaction.id in seen:
            raise FixtureValidationError(
                f"{fixture_name}: duplicate transaction id {transaction.id!r}"
            )
        seen.add(transaction.id)


def _parse_transaction(fixture_name: str, transaction: dict) -> ActiveTxTransaction:
    for key in (
        "id",
        "label",
        "notes",
        "field",
        "requested_value",
        "target",
        "command",
        "echo",
        "allowed_echo_normalizations",
    ):
        if key not in transaction:
            raise FixtureValidationError(f"{fixture_name}: transaction missing {key!r}")

    transaction_id = transaction["id"]
    command = _parse_packet(fixture_name, transaction_id, "command", transaction["command"])
    echo = _parse_packet(fixture_name, transaction_id, "echo", transaction["echo"])
    target = _parse_target(fixture_name, transaction_id, transaction["target"])
    normalizations = tuple(
        _parse_normalization(fixture_name, transaction_id, normalization)
        for normalization in transaction["allowed_echo_normalizations"]
    )

    if command.source != "controller":
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: command source must be controller")
    if echo.source != "heater":
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: echo source must be heater")
    if command.length != echo.length:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: command/echo length mismatch")
    if command.frame_type != echo.frame_type or command.frame_type != target.frame_type:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: frame_type mismatch")
    if not isinstance(transaction["field"], str) or not transaction["field"]:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad field")
    if transaction["requested_value"] not in {"Eco", "Normal"}:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad requested_value")

    _validate_target_bit(fixture_name, transaction_id, "command", command, target)
    _validate_target_bit(fixture_name, transaction_id, "echo", echo, target)
    _validate_echo_normalizations(fixture_name, transaction_id, command, echo, normalizations)

    return ActiveTxTransaction(
        fixture_name=fixture_name,
        id=transaction_id,
        label=transaction["label"],
        notes=transaction["notes"],
        field=transaction["field"],
        requested_value=transaction["requested_value"],
        target=target,
        command=command,
        echo=echo,
        allowed_echo_normalizations=normalizations,
    )


def _parse_packet(
    fixture_name: str, transaction_id: str, role: str, packet: dict
) -> ActiveTxPacket:
    for key in (
        "label",
        "source",
        "length",
        "frame_type",
        "bytes",
        "checksum_valid",
        "expected_checksum",
    ):
        if key not in packet:
            raise FixtureValidationError(
                f"{fixture_name}: {transaction_id}: {role} missing {key!r}"
            )

    length = packet["length"]
    if length not in SUPPORTED_LENGTHS:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad {role} length")
    if packet["source"] not in {"controller", "heater"}:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad {role} source")
    if not isinstance(packet["checksum_valid"], bool):
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} checksum_valid must be bool"
        )

    data = tuple(parse_hex_byte(value) for value in packet["bytes"])
    expected_checksum = parse_hex_byte(packet["expected_checksum"])
    if len(data) != length:
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} byte length mismatch"
        )
    if packet["frame_type"] != format_hex_byte(data[0]):
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} frame_type mismatch"
        )
    calculated_checksum = calculate_checksum(data, length)
    if expected_checksum != calculated_checksum:
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} checksum mismatch"
        )
    if packet["checksum_valid"] != (data[length - 1] == calculated_checksum):
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} checksum_valid mismatch"
        )

    return ActiveTxPacket(
        label=packet["label"],
        source=packet["source"],
        length=length,
        frame_type=packet["frame_type"],
        bytes=data,
        checksum_valid=packet["checksum_valid"],
        expected_checksum=expected_checksum,
    )


def _parse_target(fixture_name: str, transaction_id: str, target: dict) -> ActiveTxTarget:
    for key in ("frame_type", "raw_byte_index", "raw_bit_index", "raw_bit_value"):
        if key not in target:
            raise FixtureValidationError(
                f"{fixture_name}: {transaction_id}: target missing {key!r}"
            )
    raw_byte_index = target["raw_byte_index"]
    raw_bit_index = target["raw_bit_index"]
    raw_bit_value = target["raw_bit_value"]
    if not isinstance(raw_byte_index, int) or raw_byte_index < 0:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad raw_byte_index")
    if not isinstance(raw_bit_index, int) or raw_bit_index < 0 or raw_bit_index > 7:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad raw_bit_index")
    if raw_bit_value not in {0, 1}:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad raw_bit_value")
    return ActiveTxTarget(
        frame_type=target["frame_type"],
        raw_byte_index=raw_byte_index,
        raw_bit_index=raw_bit_index,
        raw_bit_value=raw_bit_value,
    )


def _parse_normalization(
    fixture_name: str, transaction_id: str, normalization: dict
) -> ActiveTxNormalization:
    for key in ("byte_index", "command_value", "echo_value", "notes"):
        if key not in normalization:
            raise FixtureValidationError(
                f"{fixture_name}: {transaction_id}: normalization missing {key!r}"
            )
    byte_index = normalization["byte_index"]
    if not isinstance(byte_index, int) or byte_index < 0:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: bad normalization index")
    notes = normalization["notes"]
    if not isinstance(notes, str) or not notes:
        raise FixtureValidationError(f"{fixture_name}: {transaction_id}: missing normalization notes")
    return ActiveTxNormalization(
        byte_index=byte_index,
        command_value=parse_hex_byte(normalization["command_value"]),
        echo_value=parse_hex_byte(normalization["echo_value"]),
        notes=notes,
    )


def _validate_target_bit(
    fixture_name: str,
    transaction_id: str,
    role: str,
    packet: ActiveTxPacket,
    target: ActiveTxTarget,
) -> None:
    if target.raw_byte_index >= packet.length:
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: target byte out of range"
        )
    raw_value = (packet.bytes[target.raw_byte_index] >> target.raw_bit_index) & 0x01
    if raw_value != target.raw_bit_value:
        raise FixtureValidationError(
            f"{fixture_name}: {transaction_id}: {role} target bit mismatch"
        )


def _validate_echo_normalizations(
    fixture_name: str,
    transaction_id: str,
    command: ActiveTxPacket,
    echo: ActiveTxPacket,
    normalizations: tuple[ActiveTxNormalization, ...],
) -> None:
    allowed = {
        normalization.byte_index: (
            normalization.command_value,
            normalization.echo_value,
        )
        for normalization in normalizations
    }
    checksum_index = command.length - 1
    for index, (command_value, echo_value) in enumerate(zip(command.bytes, echo.bytes)):
        if index == checksum_index:
            continue
        if command_value == echo_value:
            continue
        if index not in allowed:
            raise FixtureValidationError(
                f"{fixture_name}: {transaction_id}: unallowed echo difference at byte {index}"
            )
        if allowed[index] != (command_value, echo_value):
            raise FixtureValidationError(
                f"{fixture_name}: {transaction_id}: normalization value mismatch at byte {index}"
            )
