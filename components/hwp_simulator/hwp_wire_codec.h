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
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace esphome {
namespace hwp {
namespace wire {

struct PulseSymbol {
    uint32_t duration0;
    uint32_t level0;
    uint32_t duration1;
    uint32_t level1;
};

static constexpr size_t LONG_PACKET_LENGTH = 12;
static constexpr size_t SHORT_PACKET_LENGTH = 9;
static constexpr uint32_t FRAME_START_LOW_US = 9000;
static constexpr uint32_t FRAME_START_HIGH_US = 5000;
static constexpr uint32_t BIT_LOW_US = 1000;
static constexpr uint32_t BIT_SHORT_HIGH_US = 1000;
static constexpr uint32_t BIT_LONG_HIGH_US = 3000;
static constexpr uint8_t HEATER_REPEAT_COUNT = 4;
static constexpr uint8_t CONTROLLER_REPEAT_COUNT = 8;
static constexpr uint32_t HEATER_FRAME_SPACING_US = 152000;
static constexpr uint32_t HEATER_GROUP_SPACING_US = 1000000;
static constexpr uint32_t CONTROLLER_FRAME_SPACING_US = 100000;
static constexpr uint32_t CONTROLLER_GROUP_SPACING_US = 250000;

enum class PacketSource : uint8_t {
    HEATER,
    CONTROLLER,
};

struct Packet {
    std::array<uint8_t, LONG_PACKET_LENGTH> data{};
    size_t length{0};
    PacketSource source{PacketSource::HEATER};
};

inline bool is_supported_length(size_t length) {
    return length == SHORT_PACKET_LENGTH || length == LONG_PACKET_LENGTH;
}

inline uint8_t checksum_position(size_t length) {
    return length >= LONG_PACKET_LENGTH ? LONG_PACKET_LENGTH - 1 : length - 1;
}

inline uint8_t checksum(const uint8_t* data, size_t length) {
    if (data == nullptr || !is_supported_length(length)) {
        return 0;
    }
    uint32_t total = 0;
    const size_t start = length == SHORT_PACKET_LENGTH ? 1 : 0;
    for (size_t index = start; index < length - 1; ++index) {
        total += data[index];
    }
    return static_cast<uint8_t>(total % 256);
}

inline bool checksum_valid(const uint8_t* data, size_t length) {
    if (data == nullptr || !is_supported_length(length)) {
        return false;
    }
    return data[checksum_position(length)] == checksum(data, length);
}

inline void refresh_checksum(uint8_t* data, size_t length) {
    if (data == nullptr || !is_supported_length(length)) {
        return;
    }
    data[checksum_position(length)] = checksum(data, length);
}

inline PulseSymbol make_symbol(uint32_t low_us, uint32_t high_us) {
    return PulseSymbol{low_us, 0, high_us, 1};
}

inline uint8_t wire_byte(uint8_t value, PacketSource source) {
    return source == PacketSource::HEATER ? static_cast<uint8_t>(~value) : value;
}

inline std::vector<PulseSymbol> encode_packet_symbols(
    const uint8_t* data, size_t length, PacketSource source, bool group_end) {
    std::vector<PulseSymbol> symbols;
    if (data == nullptr || !is_supported_length(length)) {
        return symbols;
    }

    symbols.reserve(1 + length * 8 + 1);
    symbols.push_back(make_symbol(FRAME_START_LOW_US, FRAME_START_HIGH_US));
    for (size_t byte_index = 0; byte_index < length; ++byte_index) {
        const uint8_t value = wire_byte(data[byte_index], source);
        for (uint8_t bit_index = 0; bit_index < 8; ++bit_index) {
            const bool bit_set = (value & (1 << bit_index)) != 0;
            symbols.push_back(
                make_symbol(BIT_LOW_US, bit_set ? BIT_LONG_HIGH_US : BIT_SHORT_HIGH_US));
        }
    }
    const uint32_t frame_spacing =
        source == PacketSource::HEATER ? HEATER_FRAME_SPACING_US : CONTROLLER_FRAME_SPACING_US;
    const uint32_t group_spacing =
        source == PacketSource::HEATER ? HEATER_GROUP_SPACING_US : CONTROLLER_GROUP_SPACING_US;
    symbols.push_back(make_symbol(BIT_LOW_US, group_end ? group_spacing : frame_spacing));
    return symbols;
}

inline bool decode_packet_symbols(
    const PulseSymbol* symbols, size_t symbol_count, PacketSource source, Packet& out) {
    if (symbols == nullptr || symbol_count < 1 + SHORT_PACKET_LENGTH * 8 + 1) {
        return false;
    }
    const size_t payload_symbols = symbol_count - 2;
    const size_t length = payload_symbols / 8;
    if (payload_symbols % 8 != 0 || !is_supported_length(length)) {
        return false;
    }
    out = Packet{};
    out.length = length;
    out.source = source;
    for (size_t byte_index = 0; byte_index < length; ++byte_index) {
        uint8_t value = 0;
        for (uint8_t bit_index = 0; bit_index < 8; ++bit_index) {
            const auto& symbol = symbols[1 + byte_index * 8 + bit_index];
            if (symbol.duration1 > 2000) {
                value |= static_cast<uint8_t>(1 << bit_index);
            }
        }
        out.data[byte_index] = wire_byte(value, source);
    }
    return checksum_valid(out.data.data(), out.length);
}

inline size_t packet_symbol_count(size_t length) {
    return is_supported_length(length) ? 1 + length * 8 + 1 : 0;
}

inline bool same_packet(const Packet& left, const Packet& right) {
    if (left.length != right.length || left.source != right.source) {
        return false;
    }
    for (size_t index = 0; index < left.length; ++index) {
        if (left.data[index] != right.data[index]) {
            return false;
        }
    }
    return true;
}

inline std::vector<Packet> decode_packet_group_symbols(
    const PulseSymbol* symbols, size_t symbol_count, PacketSource source) {
    std::vector<Packet> packets;
    if (symbols == nullptr) {
        return packets;
    }

    const size_t long_count = packet_symbol_count(LONG_PACKET_LENGTH);
    const size_t short_count = packet_symbol_count(SHORT_PACKET_LENGTH);
    Packet previous;
    bool have_previous = false;

    for (size_t offset = 0; offset < symbol_count;) {
        Packet packet;
        size_t consumed = 0;
        if (offset + long_count <= symbol_count &&
            decode_packet_symbols(symbols + offset, long_count, source, packet)) {
            consumed = long_count;
        } else if (offset + short_count <= symbol_count &&
                   decode_packet_symbols(symbols + offset, short_count, source, packet)) {
            consumed = short_count;
        }

        if (consumed == 0) {
            ++offset;
            continue;
        }

        if (!have_previous || !same_packet(previous, packet)) {
            packets.push_back(packet);
            previous = packet;
            have_previous = true;
        }
        offset += consumed;
    }
    return packets;
}

} // namespace wire
} // namespace hwp
} // namespace esphome
