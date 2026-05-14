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

"""Agent-oriented orchestration CLI for the HWP simulator ESPHome node."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


SIM_ENTITY_HINTS = {
    "playbook": "playbook",
    "active": "active",
    "command": "command",
    "last_frame": "last_frame",
}


@dataclass(frozen=True)
class EntitySummary:
    key: int
    name: str
    object_id: str
    kind: str

    @classmethod
    def from_api_entity(cls, entity) -> "EntitySummary":
        return cls(
            key=getattr(entity, "key", 0),
            name=getattr(entity, "name", "") or "",
            object_id=getattr(entity, "object_id", "") or "",
            kind=entity.__class__.__name__,
        )


def entity_matches(entity: EntitySummary, hint: str) -> bool:
    needle = hint.lower()
    return needle in entity.name.lower() or needle in entity.object_id.lower()


def find_entity(entities: Iterable[EntitySummary], hint: str) -> EntitySummary | None:
    for entity in entities:
        if entity_matches(entity, hint):
            return entity
    return None


def entities_by_key(entities: Iterable[EntitySummary]) -> dict[int, EntitySummary]:
    return {entity.key: entity for entity in entities}


def state_value(state):
    for attr in ("state", "value", "missing_state"):
        if hasattr(state, attr):
            value = getattr(state, attr)
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return str(value)
    return None


def transcript_event_json(device: str, state, entity_map: dict[int, EntitySummary] | None = None) -> str:
    key = getattr(state, "key", 0)
    entity = entity_map.get(key) if entity_map is not None else None
    payload = {
        "event": "entity.state",
        "device": device,
        "key": key,
        "name": entity.name if entity else "",
        "object_id": entity.object_id if entity else "",
        "kind": entity.kind if entity else state.__class__.__name__,
        "state": state_value(state),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload, sort_keys=True)


async def connect_client(args):
    try:
        from aioesphomeapi import APIClient
    except ModuleNotFoundError as err:
        raise SystemExit(
            "aioesphomeapi is required for live orchestration. "
            "Install with `python -m pip install -r requirements-annotator.txt`."
        ) from err

    client = APIClient(
        address=args.device,
        port=args.port,
        password="",
        noise_psk=args.api_key,
        client_info="hwp_sim_orchestrate 1.0",
    )
    await client.connect(login=True)
    return client


async def list_entities(args) -> int:
    client = await connect_client(args)
    try:
        entity_infos, _ = await client.list_entities_services()
        entities = [EntitySummary.from_api_entity(entity) for entity in entity_infos]
        for entity in entities:
            print(json.dumps(entity.__dict__, sort_keys=True))
    finally:
        await client.disconnect()
    return 0


async def send_command(args) -> int:
    client = await connect_client(args)
    try:
        entity_infos, _ = await client.list_entities_services()
        entities = [EntitySummary.from_api_entity(entity) for entity in entity_infos]
        command_entity = find_entity(entities, SIM_ENTITY_HINTS["command"])
        if command_entity is None:
            raise SystemExit("Could not find HWP simulator command text entity")
        client.text_command(command_entity.key, args.command)
        print(json.dumps({"event": "command.sent", "command": args.command}, sort_keys=True))
    finally:
        await client.disconnect()
    return 0


async def set_playbook(args) -> int:
    return await send_command(
        argparse.Namespace(
            device=args.device,
            port=args.port,
            api_key=args.api_key,
            command=f"playbook {args.playbook}",
        )
    )


async def transcript(args) -> int:
    clients = []
    output = sys.stdout if args.out == "-" else open(args.out, "w", encoding="utf-8")
    try:
        sim_client = await connect_client(args)
        clients.append(sim_client)
        sim_entity_infos, _ = await sim_client.list_entities_services()
        sim_entities = entities_by_key(EntitySummary.from_api_entity(entity) for entity in sim_entity_infos)

        def sim_state(state):
            output.write(transcript_event_json(args.device, state, sim_entities) + "\n")
            output.flush()

        sim_client.subscribe_states(sim_state)

        if args.firmware_device:
            firmware_args = argparse.Namespace(
                device=args.firmware_device,
                port=args.firmware_port,
                api_key=args.firmware_api_key,
            )
            firmware_client = await connect_client(firmware_args)
            clients.append(firmware_client)
            firmware_entity_infos, _ = await firmware_client.list_entities_services()
            firmware_entities = entities_by_key(
                EntitySummary.from_api_entity(entity) for entity in firmware_entity_infos
            )

            def firmware_state(state):
                output.write(transcript_event_json(args.firmware_device, state, firmware_entities) + "\n")
                output.flush()

            firmware_client.subscribe_states(firmware_state)

        await asyncio.sleep(args.duration)
    finally:
        for client in clients:
            await client.disconnect()
        if output is not sys.stdout:
            output.close()
    return 0


async def run(args) -> int:
    if args.action == "list":
        return await list_entities(args)
    if args.action == "set-playbook":
        return await set_playbook(args)
    if args.action == "command":
        return await send_command(args)
    if args.action == "transcript":
        return await transcript(args)
    raise SystemExit(f"Unsupported action {args.action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Simulator ESPHome node address")
    parser.add_argument("--api-key", default="", help="ESPHome native API encryption key")
    parser.add_argument("--port", type=int, default=6053, help="ESPHome native API port")

    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("list", help="List simulator API entities as JSONL")
    playbook = subparsers.add_parser("set-playbook", help="Select simulator playbook")
    playbook.add_argument("playbook")
    command = subparsers.add_parser("command", help="Send raw simulator command text")
    command.add_argument("command")
    transcript_parser = subparsers.add_parser(
        "transcript", help="Record simulator state updates as JSONL"
    )
    transcript_parser.add_argument("--duration", type=float, default=30.0)
    transcript_parser.add_argument("--out", required=True, help="Output JSONL path, or '-' for stdout")
    transcript_parser.add_argument("--firmware-device", help="Optional production firmware node address")
    transcript_parser.add_argument("--firmware-api-key", default="", help="Firmware node API key")
    transcript_parser.add_argument("--firmware-port", type=int, default=6053, help="Firmware node API port")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
