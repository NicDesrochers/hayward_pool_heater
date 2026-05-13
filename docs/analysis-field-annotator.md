# HWP Field Annotator

The field annotator captures ESPHome API logs while you manipulate the heat-pump menu and writes tagged windows that remain compatible with `python -m analysis.hwp_analyze annotations` and `prove-annotations`.

## Connection Profiles

## Workstation Setup

When running outside the ESPHome devcontainer, create a local virtual environment and install the annotator dependencies first.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-annotator.txt
python -m analysis.hwp_logs_annotator --help
```

If pip previously started backtracking through many ESPHome versions, interrupt it and rerun the install after pulling this update. The annotator requirements intentionally avoid installing the full `esphome` package; live log capture only needs `aioesphomeapi`, and `--yaml` fallback uses lightweight PyYAML.

Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-annotator.txt
python -m analysis.hwp_logs_annotator --help
```

The `--help`, `--setup` without `--yaml`, and `--show-profiles` commands do not import `aioesphomeapi`; live logging imports it only when a connection starts. You can avoid YAML parsing entirely by running `--setup` with `--device` and entering the API key when prompted.

## Connection Profiles

The GUI no longer requires copying a full ESPHome YAML beside the tool. It resolves connection settings in this order:

1. explicit GUI fields or saved profile values
2. command-line arguments
3. environment variables
4. legacy `--yaml` fallback

Saved profiles live in `.esphome-config/hwp-tools.json`, which is gitignored because it can contain API keys. Supported fields are profile name, device address, API key, port, log prefix, default delay, log level, and dump-config.

The easiest first-time setup is the interactive profile creator:

```sh
python -m analysis.hwp_logs_annotator --setup
```

You can prefill it from an ESPHome YAML, environment variables, or CLI arguments:

```sh
python -m analysis.hwp_logs_annotator --setup --profile pool --yaml .esphome-config/hayward-heater-test.yaml
python -m analysis.hwp_logs_annotator --setup --profile pool --device hayward-heater-test.local
```

List saved profiles without printing API keys:

```sh
python -m analysis.hwp_logs_annotator --show-profiles
```

Useful environment variables:

```sh
HWP_DEVICE_ADDRESS=hayward-heater-test.local
HWP_API_KEY=...
HWP_API_PORT=6053
HWP_LOG_PREFIX=.esphome-config/logs/POOL
HWP_DEFAULT_DELAY=1.5
HWP_LOG_LEVEL=VERBOSE
HWP_DUMP_CONFIG=false
```

Run the GUI:

```sh
python -m analysis.hwp_logs_annotator --profile pool
```

Run the terminal fallback:

```sh
python -m analysis.hwp_logs_annotator --cli --device hayward-heater-test.local --api-key "$HWP_API_KEY"
```

Legacy YAML remains supported:

```sh
python -m analysis.hwp_logs_annotator --yaml .esphome-config/hayward-heater-test.yaml
```

## Annotation Workflow

Use **Start** before changing a writable heat-pump menu value, then **Submit** after the expected change appears in the log stream. This produces the same BEGIN/END window shape used by `prove-annotations`.

Observed events and searches use duration windows. The GUI supports number, integer, normal temperature, and extended-temperature searches. The extended-temperature search is for menu/setpoint bytes that use the linear `raw / 2 - 30` encoding; the normal temperature search keeps the existing signed and low-range decoders.

## Packet Shape Viewer

The packet viewer is parser-backed. It uses `analysis.hwp_log_parser.parse_log_line()` and `analysis.hwp_packet_view`, then renders the resulting cells in Tk. The widget does not carry a separate packet regex.

The viewer highlights:

- checksum failures
- tracked fixture matches
- known menu-map byte locations from `analysis/hwp_menu_map.py`
- bytes changed versus the previous packet with the same frame, source, and length

The viewer is a discovery aid, not a decoder authority. Unknown bytes stay unknown until menu metadata or tracked fixtures name them.
