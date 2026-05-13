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

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
build_dir="${TMPDIR:-/tmp}/hayward-native-tests"
protocol_binary="$build_dir/test_protocol_core"
frame_binary="$build_dir/test_frame_contracts"
decoder_binary="$build_dir/test_decoder_pulses"
web_dashboard_binary="$build_dir/test_web_dashboard"

mkdir -p "$build_dir"

/usr/bin/g++ \
  -std=c++17 \
  -Wall \
  -Wextra \
  -Werror \
  -I"$repo_root/components/hwp" \
  "$repo_root/tests/native/hwp/test_protocol_core.cpp" \
  "$repo_root/components/hwp/protocol_core.cpp" \
  -o "$protocol_binary"

"$protocol_binary"

/usr/bin/g++ \
  -std=c++17 \
  -DHWP_NATIVE_TEST \
  -Wall \
  -Wextra \
  -Werror \
  -Wno-unused-parameter \
  -Wno-unused-variable \
  -Wno-unused-but-set-variable \
  -Wno-sign-compare \
  -I"$repo_root/components/hwp" \
  "$repo_root/tests/native/hwp/test_frame_contracts.cpp" \
  "$repo_root/components/hwp/protocol_core.cpp" \
  "$repo_root/components/hwp/Schema.cpp" \
  "$repo_root/components/hwp/base_frame.cpp" \
  "$repo_root/components/hwp/FrameClock.cpp" \
  "$repo_root/components/hwp/FrameConditions1.cpp" \
  "$repo_root/components/hwp/FrameConditions1B.cpp" \
  "$repo_root/components/hwp/FrameConditions2.cpp" \
  "$repo_root/components/hwp/FrameConditions2B.cpp" \
  "$repo_root/components/hwp/FrameConditionsD.cpp" \
  "$repo_root/components/hwp/FrameConf1.cpp" \
  "$repo_root/components/hwp/FrameConf2.cpp" \
  "$repo_root/components/hwp/FrameConf3.cpp" \
  "$repo_root/components/hwp/FrameConf4.cpp" \
  "$repo_root/components/hwp/FrameConf5.cpp" \
  "$repo_root/components/hwp/FrameConf6.cpp" \
  -o "$frame_binary"

"$frame_binary"

/usr/bin/g++ \
  -std=c++17 \
  -DHWP_NATIVE_TEST \
  -Wall \
  -Wextra \
  -Werror \
  -Wno-unused-parameter \
  -Wno-unused-variable \
  -Wno-unused-but-set-variable \
  -Wno-sign-compare \
  -I"$repo_root/components/hwp" \
  "$repo_root/tests/native/hwp/test_decoder_pulses.cpp" \
  "$repo_root/components/hwp/protocol_core.cpp" \
  "$repo_root/components/hwp/Schema.cpp" \
  "$repo_root/components/hwp/base_frame.cpp" \
  "$repo_root/components/hwp/Decoder.cpp" \
  -o "$decoder_binary"

"$decoder_binary"

/usr/bin/g++ \
  -std=c++17 \
  -DHWP_NATIVE_TEST \
  -Wall \
  -Wextra \
  -Werror \
  -Wno-unused-parameter \
  -Wno-unused-variable \
  -Wno-unused-but-set-variable \
  -Wno-sign-compare \
  -I"$repo_root/components/hwp" \
  "$repo_root/tests/native/hwp/test_web_dashboard.cpp" \
  "$repo_root/components/hwp/protocol_core.cpp" \
  "$repo_root/components/hwp/Schema.cpp" \
  "$repo_root/components/hwp/base_frame.cpp" \
  "$repo_root/components/hwp/hwp_web_dashboard.cpp" \
  -o "$web_dashboard_binary"

"$web_dashboard_binary"

echo "Native tests passed."
