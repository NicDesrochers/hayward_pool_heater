#!/usr/bin/env bash
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

set -euo pipefail

image="ghcr.io/esphome/esphome:latest"
mode="docker"
bind_cache="0"
run_python="1"
run_native="1"
fixtures=(
  "tests/components/hwp/test.esp32-idf.yaml"
  "tests/components/hwp/test.esp32-idf-pulse-debug.yaml"
)

while [ "$#" -gt 0 ]; do
  case "$1" in
    --local)
      mode="local"
      shift
      ;;
    --image)
      image="$2"
      shift 2
      ;;
    --bind-cache)
      bind_cache="1"
      shift
      ;;
    --skip-python)
      run_python="0"
      shift
      ;;
    --skip-native)
      run_native="0"
      shift
      ;;
    --fixture)
      fixtures+=("$2")
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
work_dir="/workspaces/hayward_pool_heater"
temp_root="${TMPDIR:-/tmp}/hayward-esphome-tests"
config_dir="$temp_root/config"
build_dir="$temp_root/build"
platformio_dir="$temp_root/platformio"
cache_dir="$temp_root/cache"
root_cache_dir="$temp_root/root-cache"

mkdir -p "$config_dir" "$build_dir" "$platformio_dir" "$cache_dir" "$root_cache_dir"

git_status() {
  git -C "$repo_root" status --short
}

run_esphome() {
  if [ "$mode" = "local" ]; then
    ESPHOME_BUILD_PATH="$build_dir" esphome "$@"
    return
  fi

  cache_mounts=()
  if [ "$bind_cache" = "1" ]; then
    cache_mounts=(
      -v "$build_dir:/build"
      -v "$platformio_dir:/root/.platformio"
      -v "$cache_dir:/cache"
      -v "$root_cache_dir:/root/.cache"
    )
  else
    cache_mounts=(
      -v "hayward-esphome-test-build:/build"
      -v "hayward-esphome-test-platformio:/root/.platformio"
      -v "hayward-esphome-test-cache:/cache"
      -v "hayward-esphome-test-root-cache:/root/.cache"
    )
  fi

  docker run --rm \
    -v "$repo_root:$work_dir" \
    -v "$config_dir:/config" \
    "${cache_mounts[@]}" \
    -e ESPHOME_BUILD_PATH=/build \
    -w "$work_dir" \
    "$image" \
    "$@"
}

status_before="$(git_status)"

if [ "$mode" = "local" ] && [ "$run_python" = "1" ]; then
  python -m unittest discover -s tests -p 'test_*.py'
fi

if [ "$mode" = "local" ] && [ "$run_native" = "1" ]; then
  "$repo_root/scripts/test-native.sh"
fi

run_esphome version

for fixture in "${fixtures[@]}"; do
  echo "Validating $fixture"
  run_esphome config "$fixture"
done

for fixture in "${fixtures[@]}"; do
  echo "Compiling $fixture"
  run_esphome compile "$fixture"
done

status_after="$(git_status)"
if [ "$status_before" != "$status_after" ]; then
  {
    echo "Git status changed during ESPHome tests."
    echo
    echo "Before:"
    echo "$status_before"
    echo
    echo "After:"
    echo "$status_after"
  } >&2
  exit 1
fi

echo "ESPHome fixture tests completed without repo status changes."
