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
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping

try:
    from .utils import load_esphome_yaml
except ImportError:
    from utils import load_esphome_yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_FILE = REPO_ROOT / ".esphome-config" / "hwp-tools.json"
DEFAULT_LOG_PREFIX = str(REPO_ROOT / ".esphome-config" / "logs" / "POOL")
DEFAULT_PORT = 6053
DEFAULT_DELAY = 1.5
DEFAULT_LOG_LEVEL = "DEBUG"


class ToolConfigError(ValueError):
    """Raised when annotator connection configuration cannot be resolved."""


@dataclass(frozen=True)
class ToolConnectionConfig:
    name: str = ""
    address: str = ""
    api_key: str = ""
    port: int = DEFAULT_PORT
    log_prefix: str = DEFAULT_LOG_PREFIX
    default_delay: float = DEFAULT_DELAY
    log_level: str = DEFAULT_LOG_LEVEL
    dump_config: bool = True

    def redacted(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "address": self.address,
            "api_key": "<set>" if self.api_key else "",
            "port": self.port,
            "log_prefix": self.log_prefix,
            "default_delay": self.default_delay,
            "log_level": self.log_level,
            "dump_config": self.dump_config,
        }

    def to_profile(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "api_key": self.api_key,
            "port": self.port,
            "log_prefix": self.log_prefix,
            "default_delay": self.default_delay,
            "log_level": self.log_level,
            "dump_config": self.dump_config,
        }


def load_profile_file(path: Path | str = DEFAULT_PROFILE_FILE) -> dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        return {"schema_version": 1, "default_profile": "", "profiles": {}}

    with profile_path.open(encoding="utf-8") as profile_file:
        raw = json.load(profile_file)

    if raw.get("schema_version", 1) != 1:
        raise ToolConfigError(f"{profile_path}: unsupported schema_version")
    profiles = raw.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ToolConfigError(f"{profile_path}: profiles must be an object")
    return {
        "schema_version": 1,
        "default_profile": raw.get("default_profile", ""),
        "profiles": profiles,
    }


def save_profile_file(
    path: Path | str,
    profiles: Mapping[str, Mapping[str, Any]],
    default_profile: str = "",
) -> None:
    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "default_profile": default_profile,
        "profiles": dict(profiles),
    }
    with profile_path.open("w", encoding="utf-8") as profile_file:
        json.dump(payload, profile_file, indent=2, sort_keys=True)
        profile_file.write("\n")


def upsert_profile(
    path: Path | str,
    name: str,
    config: ToolConnectionConfig,
    make_default: bool = True,
) -> None:
    if not name:
        raise ToolConfigError("profile name is required")
    payload = load_profile_file(path)
    profiles = dict(payload["profiles"])
    profiles[name] = config.to_profile()
    save_profile_file(
        path,
        profiles,
        default_profile=name if make_default else payload.get("default_profile", ""),
    )


def resolve_connection_config(
    args: Any,
    environ: Mapping[str, str] | None = None,
    yaml_loader: Callable[[str], Mapping[str, Any]] = load_esphome_yaml,
    allow_missing_profile: bool = False,
) -> ToolConnectionConfig:
    """
    Resolve connection settings in deterministic precedence order.

    Defaults are overridden by legacy YAML, then saved profile, then environment,
    then explicit CLI arguments. The GUI uses the returned config as the
    prefilled editable state and applies edited fields as the final authority.
    """
    env = os.environ if environ is None else environ
    config = ToolConnectionConfig()

    yaml_path = _arg(args, "yaml")
    if yaml_path:
        config = _merge_config(config, _config_from_yaml(yaml_path, yaml_loader))

    profile_file = Path(_arg(args, "profile_file") or DEFAULT_PROFILE_FILE)
    profile_payload = load_profile_file(profile_file)
    profile_name = _arg(args, "profile") or profile_payload.get("default_profile", "")
    if profile_name:
        profile = profile_payload.get("profiles", {}).get(profile_name)
        if profile is None:
            if allow_missing_profile:
                config = replace(config, name=profile_name)
            else:
                raise ToolConfigError(f"profile {profile_name!r} not found in {profile_file}")
        else:
            config = _merge_config(config, _config_from_mapping(profile_name, profile))

    config = replace(config, **_values_from_env(env))
    config = replace(config, **_values_from_args(args))
    return config


def require_connection_config(config: ToolConnectionConfig) -> ToolConnectionConfig:
    if not config.address:
        raise ToolConfigError(
            "device address is required; use --device, HWP_DEVICE_ADDRESS, "
            "a saved profile, or --yaml fallback"
        )
    return config


def _arg(args: Any, name: str, default: Any = None) -> Any:
    return getattr(args, name, default)


def _merge_config(
    base: ToolConnectionConfig, override: ToolConnectionConfig
) -> ToolConnectionConfig:
    values = base.__dict__.copy()
    defaults = ToolConnectionConfig()
    for key, value in override.__dict__.items():
        if value != getattr(defaults, key):
            values[key] = value
    return ToolConnectionConfig(**values)


def _config_from_mapping(name: str, raw: Mapping[str, Any]) -> ToolConnectionConfig:
    return ToolConnectionConfig(
        name=name,
        address=str(raw.get("address", "") or raw.get("device", "")),
        api_key=str(raw.get("api_key", "")),
        port=_int_or_default(raw.get("port"), DEFAULT_PORT),
        log_prefix=str(raw.get("log_prefix", DEFAULT_LOG_PREFIX)),
        default_delay=_float_or_default(raw.get("default_delay"), DEFAULT_DELAY),
        log_level=str(raw.get("log_level", DEFAULT_LOG_LEVEL)).upper(),
        dump_config=_bool_or_default(raw.get("dump_config"), True),
    )


def _config_from_yaml(
    yaml_path: str, yaml_loader: Callable[[str], Mapping[str, Any]]
) -> ToolConnectionConfig:
    raw = yaml_loader(yaml_path)
    device_name = raw.get("esphome", {}).get("name", "")
    api_key = raw.get("api", {}).get("encryption", {}).get("key", "")
    address = f"{device_name}.local" if device_name else ""
    return ToolConnectionConfig(address=address, api_key=api_key)


def _config_from_env(env: Mapping[str, str]) -> ToolConnectionConfig:
    return ToolConnectionConfig(**_values_from_env(env))


def _config_from_args(args: Any) -> ToolConnectionConfig:
    return ToolConnectionConfig(**_values_from_args(args))


def _values_from_env(env: Mapping[str, str]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if "HWP_PROFILE" in env:
        updates["name"] = env["HWP_PROFILE"]
    if "HWP_DEVICE_ADDRESS" in env or "HWP_DEVICE" in env:
        updates["address"] = env.get("HWP_DEVICE_ADDRESS", env.get("HWP_DEVICE", ""))
    if "HWP_API_KEY" in env:
        updates["api_key"] = env["HWP_API_KEY"]
    if "HWP_API_PORT" in env:
        updates["port"] = _int_or_default(env["HWP_API_PORT"], DEFAULT_PORT)
    if "HWP_LOG_PREFIX" in env:
        updates["log_prefix"] = env["HWP_LOG_PREFIX"]
    if "HWP_DEFAULT_DELAY" in env:
        updates["default_delay"] = _float_or_default(env["HWP_DEFAULT_DELAY"], DEFAULT_DELAY)
    if "HWP_LOG_LEVEL" in env:
        updates["log_level"] = env["HWP_LOG_LEVEL"].upper()
    if "HWP_DUMP_CONFIG" in env:
        updates["dump_config"] = _bool_or_default(env["HWP_DUMP_CONFIG"], True)
    return updates


def _values_from_args(args: Any) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if _arg(args, "profile"):
        updates["name"] = _arg(args, "profile")
    for arg_name, config_name in (
        ("device", "address"),
        ("api_key", "api_key"),
        ("log_prefix", "log_prefix"),
        ("log_level", "log_level"),
    ):
        value = _arg(args, arg_name)
        if value not in (None, ""):
            updates[config_name] = value.upper() if config_name == "log_level" else value
    for arg_name, config_name, converter in (
        ("port", "port", int),
        ("delay", "default_delay", float),
        ("default_delay", "default_delay", float),
    ):
        value = _arg(args, arg_name)
        if value is not None:
            updates[config_name] = converter(value)
    if _arg(args, "dump_config") is not None:
        updates["dump_config"] = bool(_arg(args, "dump_config"))
    return updates


def _int_or_default(value: Any, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _float_or_default(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _bool_or_default(value: Any, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
