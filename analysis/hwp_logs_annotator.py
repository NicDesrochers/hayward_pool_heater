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

import argparse
import asyncio
import getpass
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    from .TagEntry import TagEntry, TagType
    from .hwp_field_dashboard import (
        DashboardState,
        GraphState,
        default_graph_field_ids,
        graph_groups,
        short_field_label,
    )
    from .hwp_fixtures import fixture_index_by_bytes, load_fixture_files
    from .hwp_log_parser import parse_log_line
    from .hwp_packet_view import PacketViewState, render_packet_view_text
    from .hwp_tool_config import (
        DEFAULT_PROFILE_FILE,
        ToolConfigError,
        ToolConnectionConfig,
        load_profile_file,
        require_connection_config,
        resolve_connection_config,
        upsert_profile,
    )
    from .utils import Colors, TimedLogLine, colored, colored_print
except ImportError:
    from TagEntry import TagEntry, TagType
    from hwp_field_dashboard import (
        DashboardState,
        GraphState,
        default_graph_field_ids,
        graph_groups,
        short_field_label,
    )
    from hwp_fixtures import fixture_index_by_bytes, load_fixture_files
    from hwp_log_parser import parse_log_line
    from hwp_packet_view import PacketViewState, render_packet_view_text
    from hwp_tool_config import (
        DEFAULT_PROFILE_FILE,
        ToolConfigError,
        ToolConnectionConfig,
        load_profile_file,
        require_connection_config,
        resolve_connection_config,
        upsert_profile,
    )
    from utils import Colors, TimedLogLine, colored, colored_print


class SharedContext:
    client: Any | None = None
    reconnect_logic: Any | None = None
    log_unsubscribe: Callable[[], None] | None = None
    restart_button: Any | None = None
    subscribe_logs: Callable[[str, bool], None] | None = None


shared_context = SharedContext()
stop_event = threading.Event()
_logs_tagger = None


@dataclass(frozen=True)
class ToolCommand:
    action: str
    log_level: str = ""
    dump_config: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture ESPHome HWP logs with manual field annotation."
    )
    parser.add_argument("--yaml", help="Legacy ESPHome YAML fallback for device/API key.")
    parser.add_argument("--device", help="ESPHome device address or host name.")
    parser.add_argument("--api-key", dest="api_key", help="ESPHome API encryption key.")
    parser.add_argument("--port", type=int, help="ESPHome API port. Default: 6053.")
    parser.add_argument("--profile", help="Saved GUI/tool profile name.")
    parser.add_argument(
        "--profile-file",
        default=str(DEFAULT_PROFILE_FILE),
        help="Profile JSON path. Default: .esphome-config/hwp-tools.json",
    )
    parser.add_argument(
        "--log-prefix",
        dest="log_prefix",
        help="Rotating log file path prefix.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        help="Default reaction delay for event/search windows.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="ESPHome API log level, such as DEBUG or VERBOSE.",
    )
    parser.add_argument(
        "--dump-config",
        dest="dump_config",
        action="store_true",
        default=None,
        help="Request initial ESPHome dump-config log output.",
    )
    parser.add_argument(
        "--no-dump-config",
        dest="dump_config",
        action="store_false",
        help="Skip initial ESPHome dump-config log output.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Use the terminal prompt instead of the Tk field annotator.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create or update a saved connection profile, then exit.",
    )
    parser.add_argument(
        "--show-profiles",
        action="store_true",
        help="List saved profiles without printing API keys, then exit.",
    )
    return parser


async def run_esphome_logs(
    config: ToolConnectionConfig,
    packet_callback: Callable[[str], None] | None = None,
):
    api = _require_aioesphomeapi()
    client_name = "hwp_logger"
    client_info = f"{client_name} 1.0.0.1"
    client = api.APIClient(
        address=config.address,
        port=config.port,
        password="",
        noise_psk=config.api_key,
        client_info=client_info,
    )
    shared_context.client = client

    colored_print(
        f"Connecting to ESPHome device at {config.address}:{config.port}...",
        Colors.cyan,
    )

    def subscribe_logs(log_level: str, dump_config: bool = False):
        if shared_context.log_unsubscribe is not None:
            shared_context.log_unsubscribe()
            shared_context.log_unsubscribe = None
        client.subscribe_logs(
            log_level=api.LogLevel.LOG_LEVEL_NONE,
            on_log=lambda _message: None,
            dump_config=False,
        )()
        shared_context.log_unsubscribe = client.subscribe_logs(
            log_level=_log_level(api.LogLevel, log_level),
            on_log=lambda message: handle_message(message),
            dump_config=dump_config,
        )

    def handle_message(message):
        if message is None:
            return
        line = message.message.decode("utf-8", errors="ignore")
        if packet_callback is not None:
            packet_callback(line)
        get_logs_tagger().add_log(TimedLogLine(line, time.localtime(time.time())))

    async def on_connect():
        try:
            colored_print(f"\nConnected to {config.address}!", Colors.blue)
            shared_context.restart_button = await find_restart_button(client)
            shared_context.subscribe_logs = subscribe_logs
            subscribe_logs(config.log_level, config.dump_config)
        except api.APIConnectionError as err:
            colored_print(
                f"\nError getting initial data for {config.address}: {err}",
                Colors.br_red,
            )
            await client.disconnect()

    async def on_disconnect(expected_disconnect):
        color = Colors.br_green if expected_disconnect else Colors.br_red
        colored_print(f"\nDisconnected from {config.address}!", color)

    async def on_connect_error(err: Exception):
        colored_print(f"Error connecting to {config.address}: {err}", Colors.br_red)

    reconnect_logic = api.ReconnectLogic(
        client=client,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        zeroconf_instance=None,
        name=client_name,
        on_connect_error=on_connect_error,
    )
    shared_context.reconnect_logic = reconnect_logic
    await reconnect_logic.start()


async def input_listener_cli():
    colored_print("Starting terminal annotator...", Colors.cyan)
    while not stop_event.is_set():
        tag_input = await asyncio.to_thread(
            input,
            colored(f"\nPress {TagType.get_prompt()}  \n\tq: quit: ", Colors.br_green),
        )
        tag_input = tag_input.strip().lower()

        if tag_input == "q":
            colored_print("Exiting program...", Colors.br_green)
            stop_event.set()
            break

        tag = TagEntry.parse(tag_input)
        if tag.is_valid():
            await tag.prompt_user()
            get_logs_tagger().enqueue(tag)


async def input_listener_gui(
    config: ToolConnectionConfig,
    packet_lines: queue.Queue[str],
    command_queue: queue.Queue[ToolCommand],
):
    await asyncio.to_thread(run_annotator_window, config, packet_lines, command_queue)
    stop_event.set()


async def handle_tool_commands(command_queue: queue.Queue[ToolCommand]):
    while not stop_event.is_set():
        try:
            command = await asyncio.to_thread(command_queue.get, True, 0.2)
        except queue.Empty:
            continue
        try:
            if command.action == "set_log_level":
                if shared_context.subscribe_logs is None:
                    colored_print("Log subscription is not connected yet.", Colors.br_yellow)
                    continue
                shared_context.subscribe_logs(command.log_level, command.dump_config)
                colored_print(
                    f"Changed live log subscription to {command.log_level}.",
                    Colors.cyan,
                )
            elif command.action == "dump_config":
                if shared_context.subscribe_logs is None:
                    colored_print("Log subscription is not connected yet.", Colors.br_yellow)
                    continue
                shared_context.subscribe_logs(command.log_level, True)
                colored_print(
                    f"Requested dump-config at {command.log_level}.",
                    Colors.cyan,
                )
            elif command.action == "restart":
                await restart_device_from_button()
        finally:
            command_queue.task_done()


async def find_restart_button(client):
    entities, _services = await client.list_entities_services()
    restart_candidates = [
        entity
        for entity in entities
        if is_restart_button_entity(entity)
    ]
    if not restart_candidates:
        colored_print(
            "No restart button entity discovered; add `button: - platform: restart` "
            "to enable annotator restarts.",
            Colors.br_yellow,
        )
        return None
    restart = restart_candidates[0]
    colored_print(
        f"Discovered restart button: {restart.name or restart.object_id}",
        Colors.cyan,
    )
    return restart


def is_restart_button_entity(entity) -> bool:
    if entity.__class__.__name__ != "ButtonInfo":
        return False
    device_class = getattr(entity, "device_class", "") or ""
    name = (getattr(entity, "name", "") or "").lower()
    object_id = (getattr(entity, "object_id", "") or "").lower()
    return (
        device_class == "restart"
        or "restart" in name
        or "reboot" in name
        or "restart" in object_id
        or "reboot" in object_id
    )


async def restart_device_from_button():
    client = shared_context.client
    restart = shared_context.restart_button
    if client is None:
        colored_print("Cannot restart: ESPHome API client is not connected.", Colors.br_red)
        return
    if restart is None:
        restart = await find_restart_button(client)
        shared_context.restart_button = restart
    if restart is None:
        return
    colored_print(
        f"Sending restart button command to {restart.name or restart.object_id}.",
        Colors.br_yellow,
    )
    client.button_command(restart.key, device_id=getattr(restart, "device_id", 0))


async def stop_all():
    if shared_context.log_unsubscribe:
        shared_context.log_unsubscribe()
        shared_context.log_unsubscribe = None
    if shared_context.reconnect_logic:
        await shared_context.reconnect_logic.stop()

    if shared_context.client:
        await shared_context.client.disconnect()


async def main_task(
    config: ToolConnectionConfig,
    use_cli: bool,
    packet_lines: queue.Queue[str],
):
    command_queue: queue.Queue[ToolCommand] = queue.Queue(maxsize=20)

    def packet_callback(line: str) -> None:
        try:
            packet_lines.put_nowait(line)
        except queue.Full:
            pass

    log_task = asyncio.create_task(run_esphome_logs(config, packet_callback))
    input_task = asyncio.create_task(
        input_listener_cli() if use_cli else input_listener_gui(config, packet_lines, command_queue)
    )
    command_task = asyncio.create_task(handle_tool_commands(command_queue))
    await input_task
    await stop_all()
    command_task.cancel()
    await log_task


def show_connection_manager(
    initial: ToolConnectionConfig, profile_file: Path | str
) -> ToolConnectionConfig | None:
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception as err:
        colored_print(
            f"Tkinter is unavailable ({err}); rerun with --cli or rebuild the devcontainer.",
            Colors.br_red,
        )
        return None

    root = tk.Tk()
    root.title("HWP Log Annotator Connection")
    result: dict[str, ToolConnectionConfig | None] = {"config": None}
    payload = load_profile_file(profile_file)
    profiles = payload["profiles"]

    fields = {
        "name": tk.StringVar(value=initial.name or payload.get("default_profile", "")),
        "address": tk.StringVar(value=initial.address),
        "api_key": tk.StringVar(value=initial.api_key),
        "port": tk.StringVar(value=str(initial.port)),
        "log_prefix": tk.StringVar(value=initial.log_prefix),
        "default_delay": tk.StringVar(value=str(initial.default_delay)),
        "log_level": tk.StringVar(value=initial.log_level),
        "dump_config": tk.BooleanVar(value=initial.dump_config),
    }

    def selected_profile(_event=None):
        name = fields["name"].get()
        profile = profiles.get(name)
        if not profile:
            return
        fields["address"].set(profile.get("address", ""))
        fields["api_key"].set(profile.get("api_key", ""))
        fields["port"].set(str(profile.get("port", 6053)))
        fields["log_prefix"].set(profile.get("log_prefix", "POOL"))
        fields["default_delay"].set(str(profile.get("default_delay", 1.5)))
        fields["log_level"].set(profile.get("log_level", "DEBUG"))
        fields["dump_config"].set(bool(profile.get("dump_config", True)))

    def build_config() -> ToolConnectionConfig:
        return ToolConnectionConfig(
            name=fields["name"].get().strip(),
            address=fields["address"].get().strip(),
            api_key=fields["api_key"].get(),
            port=int(fields["port"].get() or 6053),
            log_prefix=fields["log_prefix"].get().strip(),
            default_delay=float(fields["default_delay"].get() or 1.5),
            log_level=fields["log_level"].get().strip().upper() or "DEBUG",
            dump_config=bool(fields["dump_config"].get()),
        )

    def save_profile():
        cfg = build_config()
        upsert_profile(profile_file, cfg.name or cfg.address, cfg)

    def connect():
        result["config"] = build_config()
        root.destroy()

    def quit_window():
        root.destroy()

    row = 0
    ttk.Label(root, text="Profile").grid(row=row, column=0, sticky="e", padx=4, pady=4)
    profile_combo = ttk.Combobox(root, textvariable=fields["name"], values=sorted(profiles))
    profile_combo.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
    profile_combo.bind("<<ComboboxSelected>>", selected_profile)
    for label, key, show in (
        ("Device address", "address", ""),
        ("API key", "api_key", "*"),
        ("Port", "port", ""),
        ("Log prefix", "log_prefix", ""),
        ("Default delay", "default_delay", ""),
        ("Log level", "log_level", ""),
    ):
        row += 1
        ttk.Label(root, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(root, textvariable=fields[key], show=show).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
    row += 1
    ttk.Checkbutton(root, text="Dump config", variable=fields["dump_config"]).grid(
        row=row, column=1, sticky="w", padx=4, pady=4
    )
    row += 1
    buttons = ttk.Frame(root)
    buttons.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=8)
    ttk.Button(buttons, text="Save Profile", command=save_profile).pack(side="left")
    ttk.Button(buttons, text="Connect", command=connect).pack(side="right")
    ttk.Button(buttons, text="Quit", command=quit_window).pack(side="right", padx=4)
    root.columnconfigure(1, weight=1)
    root.mainloop()
    return result["config"]


def setup_profile_interactive(
    initial: ToolConnectionConfig,
    profile_file: Path | str,
    input_func=input,
    secret_func=getpass.getpass,
) -> ToolConnectionConfig:
    profile_name = _prompt(
        "Profile name",
        initial.name or "pool",
        input_func=input_func,
    )
    address = _prompt("Device address", initial.address, input_func=input_func)
    port = int(_prompt("API port", str(initial.port), input_func=input_func))
    current_key_hint = "<keep existing>" if initial.api_key else ""
    api_key = secret_func(f"API key {current_key_hint}: ").strip()
    if not api_key:
        api_key = initial.api_key
    log_prefix = _prompt("Log prefix", initial.log_prefix, input_func=input_func)
    default_delay = float(
        _prompt("Default window delay seconds", str(initial.default_delay), input_func=input_func)
    )
    log_level = _prompt("Log level", initial.log_level, input_func=input_func).upper()
    dump_config = _prompt_bool(
        "Dump config on connect",
        initial.dump_config,
        input_func=input_func,
    )

    config = ToolConnectionConfig(
        name=profile_name,
        address=address,
        api_key=api_key,
        port=port,
        log_prefix=log_prefix,
        default_delay=default_delay,
        log_level=log_level,
        dump_config=dump_config,
    )
    require_connection_config(config)
    upsert_profile(profile_file, profile_name, config)
    return config


def format_profiles(profile_file: Path | str) -> str:
    payload = load_profile_file(profile_file)
    profiles = payload.get("profiles", {})
    if not profiles:
        return f"No profiles found in {profile_file}"
    lines = [f"Profiles in {profile_file}:"]
    default_profile = payload.get("default_profile", "")
    for name, profile in sorted(profiles.items()):
        marker = " (default)" if name == default_profile else ""
        api_key = "<set>" if profile.get("api_key") else ""
        lines.append(
            f"  {name}{marker}: {profile.get('address', '')}:"
            f"{profile.get('port', 6053)} log={profile.get('log_prefix', '')} "
            f"level={profile.get('log_level', 'DEBUG')} api_key={api_key}"
        )
    return "\n".join(lines)


def run_annotator_window(
    config: ToolConnectionConfig,
    packet_lines: queue.Queue[str] | None = None,
    command_queue: queue.Queue[ToolCommand] | None = None,
) -> None:
    import tkinter as tk
    from tkinter import ttk

    packet_queue = packet_lines or queue.Queue()
    tool_commands = command_queue or queue.Queue()
    fixture_index = fixture_index_by_bytes(load_fixture_files())
    view_state = PacketViewState(fixture_index)
    dashboard_state = DashboardState()
    graph_state = GraphState()

    root = tk.Tk()
    root.title("HWP Field Annotator")
    root.geometry("1100x720")

    left = ttk.Frame(root)
    left.pack(side="left", fill="y", padx=8, pady=8)
    right = ttk.Frame(root)
    right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

    text_var = tk.StringVar()
    value_var = tk.StringVar()
    duration_var = tk.StringVar(value=str(config.default_delay))
    log_level_var = tk.StringVar(value=config.log_level)
    status_var = tk.StringVar(value=f"Connected profile: {config.name or config.address}")
    start_time: dict[TagType, time.struct_time] = {}

    ttk.Label(left, textvariable=status_var, wraplength=320).pack(fill="x", pady=(0, 8))
    form = ttk.LabelFrame(left, text="Annotation")
    form.pack(fill="x", pady=4)
    ttk.Label(form, text="Label").grid(row=0, column=0, sticky="e", padx=4, pady=4)
    ttk.Entry(form, textvariable=text_var, width=34).grid(row=0, column=1, padx=4, pady=4)
    ttk.Label(form, text="Value").grid(row=1, column=0, sticky="e", padx=4, pady=4)
    ttk.Entry(form, textvariable=value_var, width=34).grid(row=1, column=1, padx=4, pady=4)
    ttk.Label(form, text="Window seconds").grid(row=2, column=0, sticky="e", padx=4, pady=4)
    ttk.Entry(form, textvariable=duration_var, width=34).grid(row=2, column=1, padx=4, pady=4)

    def duration() -> float:
        try:
            return float(duration_var.get())
        except ValueError:
            return config.default_delay

    def start(tag_type: TagType):
        start_time[tag_type] = time.localtime(time.time())
        status_var.set(f"Started {tag_type.description}")

    def submit(tag_type: TagType):
        tag = TagEntry.from_params(
            tag_type=tag_type,
            delay=duration(),
            text=text_var.get(),
            value=value_var.get(),
            start_time=start_time.get(tag_type),
        )
        get_logs_tagger().enqueue(tag)
        status_var.set(f"Submitted {tag_type.description}: {tag.text}")

    controls = ttk.LabelFrame(left, text="Tools")
    controls.pack(fill="x", pady=8)
    for tag_type in (
        TagType.CHANGE,
        TagType.EVENT,
        TagType.NUMBER,
        TagType.INTEGER,
        TagType.TEMPERATURE,
        TagType.TEMPERATURE_EXTENDED,
    ):
        frame = ttk.Frame(controls)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text=tag_type.description, width=34).pack(side="left")
        if tag_type.has_start_button:
            ttk.Button(frame, text="Start", command=lambda t=tag_type: start(t)).pack(
                side="left"
            )
        ttk.Button(frame, text="Submit", command=lambda t=tag_type: submit(t)).pack(
            side="right"
        )

    ttk.Button(
        left,
        text="Flush Buffer",
        command=lambda: get_logs_tagger().enqueue(TagEntry(TagType.FLUSH_BUFFER)),
    ).pack(fill="x", pady=4)
    ttk.Button(left, text="Quit", command=root.destroy).pack(fill="x", pady=4)

    device_controls = ttk.LabelFrame(left, text="Device")
    device_controls.pack(fill="x", pady=8)
    ttk.Label(device_controls, text="Log level").grid(row=0, column=0, sticky="e", padx=4, pady=4)
    ttk.Combobox(
        device_controls,
        textvariable=log_level_var,
        values=("NONE", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE", "VERY_VERBOSE"),
        width=18,
        state="readonly",
    ).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

    def enqueue_command(command: ToolCommand, message: str):
        try:
            tool_commands.put_nowait(command)
            status_var.set(message)
        except queue.Full:
            status_var.set("Command queue is full")

    ttk.Button(
        device_controls,
        text="Apply Log Level",
        command=lambda: enqueue_command(
            ToolCommand("set_log_level", log_level=log_level_var.get()),
            f"Requested log level {log_level_var.get()}",
        ),
    ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
    ttk.Button(
        device_controls,
        text="Dump Config / Refresh",
        command=lambda: enqueue_command(
            ToolCommand("dump_config", log_level=log_level_var.get(), dump_config=True),
            f"Requested dump config at {log_level_var.get()}",
        ),
    ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
    ttk.Button(
        device_controls,
        text="Restart Device",
        command=lambda: enqueue_command(
            ToolCommand("restart"),
            "Requested device restart",
        ),
    ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
    device_controls.columnconfigure(1, weight=1)

    notebook = ttk.Notebook(right)
    notebook.pack(fill="both", expand=True)

    dashboard_tab = ttk.Frame(notebook)
    packets_tab = ttk.Frame(notebook)
    graphs_tab = ttk.Frame(notebook)
    notebook.add(dashboard_tab, text="Dashboard")
    notebook.add(packets_tab, text="Packets")
    notebook.add(graphs_tab, text="Graphs")

    dashboard_columns = (
        "value",
        "unit",
        "raw",
        "frame",
        "source",
        "age",
        "last_seen",
        "evidence",
        "safety",
    )
    dashboard_tree = ttk.Treeview(
        dashboard_tab,
        columns=dashboard_columns,
        show="tree headings",
        height=26,
    )
    dashboard_tree.heading("#0", text="Field")
    dashboard_tree.column("#0", width=280, stretch=True)
    for column, label, width in (
        ("value", "Value", 90),
        ("unit", "Unit", 50),
        ("raw", "Raw", 110),
        ("frame", "Frame", 95),
        ("source", "Source", 80),
        ("age", "Age", 70),
        ("last_seen", "Last Seen", 145),
        ("evidence", "Evidence", 160),
        ("safety", "Status", 100),
    ):
        dashboard_tree.heading(column, text=label)
        dashboard_tree.column(column, width=width, stretch=column == "evidence")
    dashboard_tree.tag_configure("changed", background="#fff2a8")
    dashboard_tree.tag_configure("recent", background="#e8f7e8")
    dashboard_tree.tag_configure("stale", foreground="#777777")
    dashboard_tree.pack(fill="both", expand=True)
    dashboard_changed_until: dict[str, float] = {}

    viewer = tk.Text(packets_tab, wrap="none", height=40)
    viewer.pack(fill="both", expand=True)
    for tag, opts in {
        "frame": {"foreground": "#1f4e79"},
        "checksum": {"foreground": "#555555"},
        "checksum-invalid": {"background": "#ffd6d6"},
        "known-menu": {"background": "#e8f3ff"},
        "known-field": {"background": "#edf7ed"},
        "changed": {"background": "#fff2a8"},
        "fixture-match": {"underline": True},
    }.items():
        viewer.tag_configure(tag, **opts)

    graph_controls = ttk.Frame(graphs_tab)
    graph_controls.pack(side="left", fill="y", padx=(0, 8))
    graph_notebook = ttk.Notebook(graphs_tab)
    graph_notebook.pack(side="right", fill="both", expand=True)
    graph_field_vars: dict[str, tk.BooleanVar] = {}
    graph_labels: dict[str, str] = {}
    graph_canvases: dict[str, tk.Canvas] = {}
    for group in graph_groups():
        tab = ttk.Frame(graph_notebook)
        graph_notebook.add(tab, text=group.title)
        graph_canvases[group.group_id] = tk.Canvas(tab, background="white", height=420)
        graph_canvases[group.group_id].pack(fill="both", expand=True)
        group_controls = ttk.LabelFrame(graph_controls, text=group.title)
        group_controls.pack(fill="x", pady=(0, 8))
        for field_id in group.field_ids:
            graph_field_vars[field_id] = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                group_controls,
                text=_graph_checkbox_label(field_id),
                variable=graph_field_vars[field_id],
                command=lambda: draw_graphs(),
            ).pack(anchor="w")

    def insert_view(line: str):
        packet = parse_log_line(line)
        if packet is None:
            return
        observations = dashboard_state.update(packet)
        graph_state.update(observations)
        update_dashboard()
        draw_graphs()
        view = view_state.build(packet)
        viewer.insert("end", view.title + "\n")
        viewer.insert("end", "[")
        for cell in view.cells:
            labels = [field.menu for field in cell.menu_fields]
            labels.extend(field.field for field in cell.known_fields)
            label = ",".join(labels)
            prefix = "*" if cell.changed else ""
            suffix = f"<{label}>" if label else ""
            viewer.insert("end", f"{prefix}{cell.text}{suffix} ", cell.tags)
        viewer.insert("end", f"]\n{view.summary}\n\n")
        viewer.see("end")

    def update_dashboard():
        existing = set(dashboard_tree.get_children(""))
        for observation in dashboard_state.latest:
            existing.discard(observation.field_id)
            graph_labels[observation.field_id] = short_field_label(observation)
            if observation.changed:
                dashboard_changed_until[observation.field_id] = time.time() + 4.0
            age_seconds = _observation_age_seconds(observation.timestamp)
            values = (
                observation.display_value,
                observation.unit,
                f"0x{observation.raw_value:02X} @ {observation.raw_location}",
                observation.frame_label,
                observation.source,
                _format_age(age_seconds),
                observation.timestamp,
                observation.evidence,
                observation.safety_status,
            )
            tags = _dashboard_tags(observation.field_id, age_seconds)
            if dashboard_tree.exists(observation.field_id):
                dashboard_tree.item(
                    observation.field_id,
                    text=observation.label,
                    values=values,
                    tags=tags,
                )
            else:
                dashboard_tree.insert(
                    "",
                    "end",
                    iid=observation.field_id,
                    text=observation.label,
                    values=values,
                    tags=tags,
                )
        for item_id in existing:
            dashboard_tree.delete(item_id)
            dashboard_changed_until.pop(item_id, None)

    def refresh_dashboard_age():
        for observation in dashboard_state.latest:
            if not dashboard_tree.exists(observation.field_id):
                continue
            age_seconds = _observation_age_seconds(observation.timestamp)
            values = list(dashboard_tree.item(observation.field_id, "values"))
            if len(values) >= len(dashboard_columns):
                values[5] = _format_age(age_seconds)
                dashboard_tree.item(
                    observation.field_id,
                    values=tuple(values),
                    tags=_dashboard_tags(observation.field_id, age_seconds),
                )
        root.after(1000, refresh_dashboard_age)

    def _dashboard_tags(field_id: str, age_seconds: float | None) -> tuple[str, ...]:
        tags = []
        now = time.time()
        if dashboard_changed_until.get(field_id, 0) > now:
            tags.append("changed")
        elif age_seconds is not None and age_seconds <= 5:
            tags.append("recent")
        if age_seconds is not None and age_seconds >= 60:
            tags.append("stale")
        return tuple(tags)

    def draw_graphs():
        history = graph_state.history
        for group in graph_groups():
            graph_canvas = graph_canvases[group.group_id]
            graph_canvas.delete("all")
            selected = [
                field_id
                for field_id in group.field_ids
                if graph_field_vars.get(field_id, tk.BooleanVar(value=False)).get()
                and history.get(field_id)
            ]
            if not selected:
                graph_canvas.create_text(
                    20,
                    20,
                    anchor="nw",
                    text=f"Waiting for {group.title.lower()} values...",
                    fill="#555555",
                )
                continue
            _draw_graph_group(graph_canvas, history, selected, graph_labels)


    def _draw_graph_group(graph_canvas, history, selected, labels):
        width = max(graph_canvas.winfo_width(), 640)
        height = max(graph_canvas.winfo_height(), 360)
        margin_left = 48
        margin_right = 220
        margin_top = 24
        margin_bottom = 36
        plot_width = max(width - margin_left - margin_right, 100)
        plot_height = max(height - margin_top - margin_bottom, 100)
        all_points = [point for field_id in selected for point in history[field_id]]
        min_x = min(point[0] for point in all_points)
        max_x = max(point[0] for point in all_points)
        min_y = min(point[1] for point in all_points)
        max_y = max(point[1] for point in all_points)
        if min_x == max_x:
            max_x += 1
        if min_y == max_y:
            min_y -= 1.0
            max_y += 1.0
        graph_canvas.create_rectangle(
            margin_left,
            margin_top,
            margin_left + plot_width,
            margin_top + plot_height,
            outline="#cccccc",
        )
        graph_canvas.create_text(
            8,
            margin_top,
            anchor="nw",
            text=f"{max_y:.1f}",
            fill="#555555",
        )
        graph_canvas.create_text(
            8,
            margin_top + plot_height - 12,
            anchor="nw",
            text=f"{min_y:.1f}",
            fill="#555555",
        )
        colors = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf")
        for index, field_id in enumerate(selected):
            points = history[field_id]
            coords = []
            for x_value, y_value in points:
                x = margin_left + ((x_value - min_x) / (max_x - min_x)) * plot_width
                y = margin_top + plot_height - ((y_value - min_y) / (max_y - min_y)) * plot_height
                coords.extend((x, y))
            color = colors[index % len(colors)]
            if len(coords) >= 4:
                graph_canvas.create_line(*coords, fill=color, width=2)
            else:
                graph_canvas.create_oval(
                    coords[0] - 2,
                    coords[1] - 2,
                    coords[0] + 2,
                    coords[1] + 2,
                    fill=color,
                    outline=color,
                )
            graph_canvas.create_text(
                margin_left + plot_width + 12,
                margin_top + index * 18,
                anchor="nw",
                text=labels.get(field_id, _graph_checkbox_label(field_id)),
                fill=color,
            )

    def poll_packets():
        while True:
            try:
                insert_view(packet_queue.get_nowait())
            except queue.Empty:
                break
        root.after(200, poll_packets)

    poll_packets()
    refresh_dashboard_age()
    root.mainloop()


def _observation_age_seconds(timestamp: str) -> float | None:
    if not timestamp:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S",):
        try:
            observed = datetime.strptime(timestamp, fmt)
            return max(0.0, time.time() - observed.timestamp())
        except ValueError:
            continue
    return None


def _format_age(age_seconds: float | None) -> str:
    if age_seconds is None:
        return ""
    seconds = int(age_seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _graph_checkbox_label(field_id: str) -> str:
    known_labels = {
        "t02_inlet": "Inlet water",
        "t03_outlet": "Outlet water",
        "t04_coil": "Coil",
        "t06_exhaust": "Exhaust",
        "t_aux_cond2": "Auxiliary",
        "r01_setpoint_cooling": "R01 Cooling setpoint",
        "r02_setpoint_heating": "R02 Heating setpoint",
        "r03_setpoint_auto": "R03 Auto setpoint",
        "r08_min_cool_setpoint": "R08 Min cool",
        "r09_max_cooling_setpoint": "R09 Max cool",
        "r10_min_heating_setpoint": "R10 Min heat",
        "r11_max_heating_setpoint": "R11 Max heat",
        "r04_return_diff_cooling": "R04 Cool return diff",
        "r05_shutdown_temp_diff_when_cooling": "R05 Cool shutdown diff",
        "r06_return_diff_heating": "R06 Heat return diff",
        "r07_shutdown_diff_heating": "R07 Heat shutdown diff",
        "d03_defrosting_cycle_time_minutes": "D03 Defrost cycle",
        "d04_max_defrost_time_minutes": "D04 Max defrost",
        "d05_min_economy_defrost_time_minutes": "D05 Min eco defrost",
        "f08_fan_low_speed_running_time": "F08 Low run time",
        "f09_fan_stop_low_speed_running_time": "F09 Stop low run",
        "f12_min_fan_voltage_pct": "F12 Min fan voltage",
        "f13_max_fan_voltage_pct": "F13 Max fan voltage",
    }
    return known_labels.get(field_id, field_id)


def _require_aioesphomeapi():
    try:
        import aioesphomeapi
    except ModuleNotFoundError as err:
        raise RuntimeError(
            "hwp_logs_annotator live logging requires aioesphomeapi. "
            "Install workstation dependencies with "
            "`python -m pip install -r requirements-annotator.txt`. "
            "Commands such as --help, --setup without --yaml, and "
            "--show-profiles do not need this package."
        ) from err
    return aioesphomeapi


def get_logs_tagger():
    global _logs_tagger
    if _logs_tagger is None:
        try:
            from .hwp_logs_tagger import LogsTagger
        except ImportError:
            from hwp_logs_tagger import LogsTagger
        _logs_tagger = LogsTagger
    return _logs_tagger


def _log_level(log_level_enum, name: str):
    normalized = (name or "DEBUG").strip().upper()
    attr = f"LOG_LEVEL_{normalized}"
    return getattr(log_level_enum, attr, log_level_enum.LOG_LEVEL_DEBUG)


def _prompt(label: str, default: str, input_func=input) -> str:
    suffix = f" [{default}]" if default else ""
    value = input_func(f"{label}{suffix}: ").strip()
    return value or default


def _prompt_bool(label: str, default: bool, input_func=input) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input_func(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "1", "true", "on"}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = resolve_connection_config(args, allow_missing_profile=args.setup)
        if args.show_profiles:
            print(format_profiles(args.profile_file))
            return 0
        if args.setup:
            saved = setup_profile_interactive(config, args.profile_file)
            colored_print(
                f"Saved HWP annotator profile: {saved.redacted()}",
                Colors.cyan,
            )
            return 0
        if not args.cli:
            selected = show_connection_manager(config, args.profile_file)
            if selected is None:
                return 1
            config = selected
        config = require_connection_config(config)
    except ToolConfigError as err:
        parser.error(str(err))

    args.log_prefix = config.log_prefix
    args.delay = config.default_delay
    get_logs_tagger().initialize(args)
    colored_print(f"Resolved connection: {config.redacted()}", Colors.cyan)

    packet_lines: queue.Queue[str] = queue.Queue(maxsize=1000)
    try:
        asyncio.run(main_task(config, args.cli, packet_lines))
    except KeyboardInterrupt:
        colored_print("Shutting down...", Colors.br_red)
        stop_event.set()
    return 0


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    raise SystemExit(main())
