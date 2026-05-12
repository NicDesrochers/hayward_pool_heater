/**
 *
 * Copyright (c) 2024 S. Leclerc (sle118@hotmail.com)
 *
 * This file is part of the Pool Heater Controller component project.
 *
 * @project Pool Heater Controller Component
 * @developer S. Leclerc (sle118@hotmail.com)
 *
 * @license MIT License
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * @disclaimer Use at your own risk. The developer assumes no responsibility
 * for any damage or loss caused by the use of this software.
 */
#include "Decoder.h"

#include <cassert>

namespace hwp = esphome::hwp;

hwp::hwp_pulse_symbol_t pulse(uint32_t low_us, uint32_t high_us) {
    return hwp::hwp_pulse_symbol_t{low_us, 0, high_us, 1};
}

void test_duration_accessors() {
    auto item = pulse(1000, 3000);
    assert(hwp::Decoder::get_low_duration(&item) == 1000);
    assert(hwp::Decoder::get_high_duration(&item) == 3000);
    assert(hwp::Decoder::get_low_duration(nullptr) == 0);
    assert(hwp::Decoder::get_high_duration(nullptr) == 0);
}

void test_pulse_classification() {
    auto start = pulse(9000, 5000);
    auto short_bit = pulse(1000, 1000);
    auto long_bit = pulse(1000, 3000);
    auto end = pulse(1000, 50000);
    auto invalid = pulse(2500, 2500);

    assert(hwp::Decoder::is_start_frame(&start));
    assert(!hwp::Decoder::is_short_bit(&start));
    assert(!hwp::Decoder::is_long_bit(&start));

    assert(hwp::Decoder::is_short_bit(&short_bit));
    assert(!hwp::Decoder::is_long_bit(&short_bit));

    assert(hwp::Decoder::is_long_bit(&long_bit));
    assert(!hwp::Decoder::is_short_bit(&long_bit));

    assert(hwp::Decoder::is_frame_end(&end));
    assert(!hwp::Decoder::is_start_frame(&invalid));
    assert(!hwp::Decoder::is_short_bit(&invalid));
    assert(!hwp::Decoder::is_long_bit(&invalid));
    assert(!hwp::Decoder::is_frame_end(&invalid));
}

void test_append_bits_still_builds_bytes() {
    hwp::Decoder decoder;
    decoder.start_new_frame();
    decoder.append_bit(true);
    decoder.append_bit(false);
    decoder.append_bit(true);
    decoder.append_bit(false);
    decoder.append_bit(false);
    decoder.append_bit(false);
    decoder.append_bit(false);
    decoder.append_bit(true);

    assert(decoder.packet.data_len == 1);
    assert(decoder.packet.data[0] == 0x85);
}

int main() {
    test_duration_accessors();
    test_pulse_classification();
    test_append_bits_still_builds_bytes();
}
