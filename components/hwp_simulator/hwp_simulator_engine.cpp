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
#include "hwp_simulator_engine.h"

#include <algorithm>
#include <cstring>

namespace esphome {
namespace hwp_simulator {

namespace {

Packet make_packet(const std::array<uint8_t, 12>& data, size_t length, PacketSource source) {
    Packet packet;
    packet.data = data;
    packet.length = length;
    packet.source = source;
    return packet;
}

static const CatalogPacket CATALOG[] = {
    {"base-config-1", "CONFIG_1",
        make_packet({0x81, 0xB1, 0x1A, 0x72, 0x51, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xA7},
            12, PacketSource::HEATER)},
    {"base-config-2", "CONFIG_2",
        make_packet({0x82, 0xB1, 0x26, 0x13, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xA8},
            12, PacketSource::HEATER)},
    {"base-config-3", "CONFIG_3",
        make_packet({0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x4C, 0x82, 0x46, 0x8C, 0x8D},
            12, PacketSource::HEATER)},
    {"base-config-4", "CONFIG_4",
        make_packet({0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x0F},
            12, PacketSource::HEATER)},
    {"base-config-5-normal", "CONFIG_5",
        make_packet({0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45},
            12, PacketSource::HEATER)},
    {"base-config-5-eco-echo", "CONFIG_5 D06 ECO echo",
        make_packet({0x85, 0xB1, 0x40, 0x06, 0x4A, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0xB1},
            12, PacketSource::HEATER)},
    {"base-config-6", "CONFIG_6",
        make_packet({0x86, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x37},
            12, PacketSource::HEATER)},
    {"base-cond-1", "COND_1",
        make_packet({0xD1, 0xB1, 0x05, 0x00, 0x00, 0x00, 0x00, 0x78, 0x5E, 0x56, 0x1B, 0xCE},
            12, PacketSource::HEATER)},
    {"base-cond-1b", "COND_1B",
        make_packet({0xD1, 0xB1, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x78, 0x5E, 0x56, 0x1B, 0xD8},
            12, PacketSource::HEATER)},
    {"base-cond-2", "COND_2",
        make_packet({0xD2, 0xB1, 0x11, 0x5E, 0x56, 0x56, 0x5C, 0x00, 0x64, 0x00, 0x00, 0x5E},
            12, PacketSource::HEATER)},
    {"base-cond-2b", "COND_2_B",
        make_packet({0xD2, 0x1B, 0x0A, 0x28, 0x15, 0x0D, 0xA0, 0xAA, 0xB9, 0x00, 0x00, 0x00},
            9, PacketSource::HEATER)},
    {"base-cond-d", "COND_D",
        make_packet({0xDD, 0x0D, 0x0D, 0x0D, 0x11, 0x10, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00},
            9, PacketSource::HEATER)},
    {"stress-invalid-checksum", "Invalid checksum",
        make_packet({0xD2, 0xB1, 0x11, 0x5E, 0x56, 0x56, 0x5C, 0x00, 0x64, 0x00, 0x00, 0x00},
            12, PacketSource::HEATER)},
};

const CatalogPacket& catalog_by_index(size_t index) {
    return CATALOG[index % (sizeof(CATALOG) / sizeof(CATALOG[0]))];
}

const CatalogPacket* catalog_config_by_frame(uint8_t frame) {
    for (const auto& packet : CATALOG) {
        if (packet.packet.length == 12 && packet.packet.data[0] == frame) {
            return &packet;
        }
    }
    return nullptr;
}

bool is_config_registry_frame(const Packet& packet) {
    return packet.length == 12 && packet.data[0] >= 0x81 && packet.data[0] <= 0x86;
}

size_t config_registry_index(const Packet& packet) {
    return static_cast<size_t>(packet.data[0] - 0x81);
}

bool packet_bytes_equal(const Packet& left, const Packet& right) {
    if (left.length != right.length) {
        return false;
    }
    for (size_t index = 0; index < left.length; ++index) {
        if (left.data[index] != right.data[index]) {
            return false;
        }
    }
    return true;
}

} // namespace

const char* playbook_to_string(Playbook playbook) {
    switch (playbook) {
    case Playbook::PAUSED:
        return "paused";
    case Playbook::NORMAL_IDLE:
        return "normal_idle";
    case Playbook::CONFIG_REFRESH:
        return "config_refresh";
    case Playbook::ACTIVE_DEFROST_ECHO:
        return "active_defrost_echo";
    case Playbook::RX_STRESS:
        return "rx_stress";
    }
    return "paused";
}

std::optional<Playbook> playbook_from_string(const std::string& value) {
    if (value == "paused") return Playbook::PAUSED;
    if (value == "normal_idle") return Playbook::NORMAL_IDLE;
    if (value == "config_refresh") return Playbook::CONFIG_REFRESH;
    if (value == "active_defrost_echo") return Playbook::ACTIVE_DEFROST_ECHO;
    if (value == "rx_stress") return Playbook::RX_STRESS;
    return std::nullopt;
}

const CatalogPacket* find_catalog_packet(const std::string& id) {
    for (const auto& packet : CATALOG) {
        if (id == packet.id) {
            return &packet;
        }
    }
    return nullptr;
}

const CatalogPacket* catalog_packets(size_t& count) {
    count = sizeof(CATALOG) / sizeof(CATALOG[0]);
    return CATALOG;
}

void SimulatorEngine::set_playbook(Playbook playbook) {
    playbook_ = playbook;
    cursor_ = 0;
}

void SimulatorEngine::set_interval_scale(float value) {
    interval_scale_ = std::max(0.1f, std::min(value, 10.0f));
}

void SimulatorEngine::reset() {
    cursor_ = 0;
    stats_ = {};
    config_registry_ = {};
}

std::optional<Packet> SimulatorEngine::current_registry_packet_(const CatalogPacket& packet) const {
    if (!is_config_registry_frame(packet.packet)) {
        return std::nullopt;
    }
    const auto& stored = config_registry_[config_registry_index(packet.packet)];
    if (stored.has_value()) {
        return stored.value();
    }
    Packet registry_packet = packet.packet;
    registry_packet.source = PacketSource::HEATER;
    return registry_packet;
}

SimulatorStep SimulatorEngine::packet_step(
    const CatalogPacket& packet, const char* event, uint32_t delay_ms) {
    SimulatorStep step;
    step.has_packet = true;
    step.packet = packet.packet;
    if (auto registry_packet = current_registry_packet_(packet); registry_packet.has_value()) {
        step.packet = registry_packet.value();
    }
    step.packet_id = packet.id;
    step.label = packet.label;
    step.event = event;
    step.delay_ms = static_cast<uint32_t>(delay_ms * interval_scale_);
    stats_.step++;
    stats_.packet_count++;
    return step;
}

SimulatorStep SimulatorEngine::step_once() {
    if (!active_ || playbook_ == Playbook::PAUSED) {
        return SimulatorStep{false, {}, "", "", "paused", 1000};
    }
    switch (playbook_) {
    case Playbook::NORMAL_IDLE:
        return normal_idle_step();
    case Playbook::CONFIG_REFRESH:
        return config_refresh_step();
    case Playbook::ACTIVE_DEFROST_ECHO:
        return active_defrost_step();
    case Playbook::RX_STRESS:
        return rx_stress_step();
    case Playbook::PAUSED:
        break;
    }
    return SimulatorStep{false, {}, "", "", "paused", 1000};
}

SimulatorStep SimulatorEngine::normal_idle_step() {
    struct ScheduledPacket {
        size_t catalog_index;
        uint32_t delay_ms;
    };
    static const ScheduledPacket ORDER[] = {
        {6, 500},   // CONFIG_6
        {3, 500},   // CONFIG_4
        {4, 500},   // CONFIG_5
        {7, 1350},  // COND_1
        {9, 500},   // COND_2
        {1, 450},   // CONFIG_2
        {0, 500},   // CONFIG_1
        {8, 1350},  // COND_1B
        {2, 400},   // CONFIG_3
        {10, 400},  // COND_2_B
        {11, 500},  // COND_D
        {7, 1350},  // COND_1
        {9, 500},   // COND_2
        {1, 450},   // CONFIG_2
        {0, 500},   // CONFIG_1
        {8, 1350},  // COND_1B
    };
    static constexpr size_t ORDER_LENGTH = sizeof(ORDER) / sizeof(ORDER[0]);
    const size_t order_index = cursor_++ % ORDER_LENGTH;
    const auto& scheduled = ORDER[order_index];
    const auto& packet = catalog_by_index(scheduled.catalog_index);
    if (packet.packet.length == 12 && packet.packet.data[0] == 0xD2) {
        CatalogPacket drifting_packet = packet;
        const uint8_t phase = static_cast<uint8_t>((cursor_ / ORDER_LENGTH) % 6);
        drifting_packet.packet.data[4] = static_cast<uint8_t>(0x56 + phase);
        drifting_packet.packet.data[5] = static_cast<uint8_t>(0x56 + phase);
        drifting_packet.packet.data[6] = static_cast<uint8_t>(0x5C + phase);
        esphome::hwp::wire::refresh_checksum(
            drifting_packet.packet.data.data(), drifting_packet.packet.length);
        return packet_step(drifting_packet, "normal_idle", scheduled.delay_ms);
    }
    return packet_step(packet, "normal_idle", scheduled.delay_ms);
}

SimulatorStep SimulatorEngine::config_refresh_step() {
    static const size_t ORDER[] = {2, 10, 11, 7, 9, 1, 0, 8, 6, 3, 4};
    const auto& packet = catalog_by_index(ORDER[cursor_++ % (sizeof(ORDER) / sizeof(ORDER[0]))]);
    return packet_step(packet, "config_refresh", cursor_ % 4 == 0 ? 11000 : 500);
}

SimulatorStep SimulatorEngine::active_defrost_step() {
    const auto& packet = catalog_by_index(cursor_++ % 2 == 0 ? 4 : 5);
    return packet_step(packet, "active_defrost_echo", 5000);
}

SimulatorStep SimulatorEngine::rx_stress_step() {
    static const size_t ORDER[] = {9, 12, 10, 11, 7};
    const auto& packet = catalog_by_index(ORDER[cursor_++ % (sizeof(ORDER) / sizeof(ORDER[0]))]);
    if (!esphome::hwp::wire::checksum_valid(packet.packet.data.data(), packet.packet.length)) {
        stats_.error_count++;
    }
    return packet_step(packet, "rx_stress", cursor_ % 3 == 0 ? 15000 : 300);
}

std::optional<SimulatorStep> SimulatorEngine::handle_controller_packet(const Packet& packet) {
    return update_config_registry_(packet);
}

std::optional<SimulatorStep> SimulatorEngine::update_config_registry_(const Packet& packet) {
    if (!is_config_registry_frame(packet)) {
        return std::nullopt;
    }

    Packet stored_packet = packet;
    stored_packet.source = PacketSource::HEATER;
    const size_t index = config_registry_index(stored_packet);
    const auto* default_packet = catalog_config_by_frame(stored_packet.data[0]);
    const Packet* current_packet = config_registry_[index].has_value()
                                       ? &config_registry_[index].value()
                                       : (default_packet != nullptr ? &default_packet->packet : nullptr);
    const bool changed =
        current_packet == nullptr || !packet_bytes_equal(*current_packet, stored_packet);
    config_registry_[index] = stored_packet;
    if (!changed) {
        return std::nullopt;
    }

    SimulatorStep echo;
    echo.has_packet = true;
    echo.packet = stored_packet;
    echo.packet_id = "config-registry";
    echo.label = "CONFIG";
    echo.event = "command_echo";
    echo.delay_ms = static_cast<uint32_t>(2000 * interval_scale_);
    stats_.step++;
    stats_.packet_count++;
    return echo;
}

ControllerPacketResult SimulatorEngine::receive_controller_packet(const Packet& packet) {
    if (packet.source != PacketSource::CONTROLLER) {
        stats_.error_count++;
        return ControllerPacketResult{false, false, {}, "ignored non-controller packet"};
    }
    if (!esphome::hwp::wire::is_supported_length(packet.length) ||
        !esphome::hwp::wire::checksum_valid(packet.data.data(), packet.length)) {
        stats_.error_count++;
        return ControllerPacketResult{false, false, {}, "invalid controller packet"};
    }

    stats_.rx_packet_count++;
    auto echo = handle_controller_packet(packet);
    if (!echo.has_value()) {
        return ControllerPacketResult{true, false, {}, "accepted controller packet"};
    }

    stats_.echo_count++;
    return ControllerPacketResult{true, true, *echo, "updated simulator registry"};
}

} // namespace hwp_simulator
} // namespace esphome
