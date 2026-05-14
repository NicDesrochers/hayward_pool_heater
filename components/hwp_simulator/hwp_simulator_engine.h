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

#include "hwp_wire_codec.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace esphome {
namespace hwp_simulator {

using esphome::hwp::wire::Packet;
using esphome::hwp::wire::PacketSource;

enum class Playbook : uint8_t {
    PAUSED,
    NORMAL_IDLE,
    CONFIG_REFRESH,
    ACTIVE_DEFROST_ECHO,
    RX_STRESS,
};

struct CatalogPacket {
    const char* id;
    const char* label;
    Packet packet;
};

struct SimulatorStep {
    bool has_packet{false};
    Packet packet{};
    const char* packet_id{""};
    const char* label{""};
    const char* event{""};
    uint32_t delay_ms{0};
};

struct SimulatorStats {
    uint32_t step{0};
    uint32_t packet_count{0};
    uint32_t rx_packet_count{0};
    uint32_t echo_count{0};
    uint32_t error_count{0};
};

struct ControllerPacketResult {
    bool accepted{false};
    bool has_echo{false};
    SimulatorStep echo{};
    const char* status{""};
};

const char* playbook_to_string(Playbook playbook);
std::optional<Playbook> playbook_from_string(const std::string& value);
const CatalogPacket* find_catalog_packet(const std::string& id);
const CatalogPacket* catalog_packets(size_t& count);

class SimulatorEngine {
  public:
    void set_playbook(Playbook playbook);
    Playbook playbook() const { return playbook_; }
    void set_active(bool active) { active_ = active; }
    bool active() const { return active_; }
    void set_interval_scale(float value);
    float interval_scale() const { return interval_scale_; }
    void reset();
    SimulatorStep step_once();
    std::optional<SimulatorStep> handle_controller_packet(const Packet& packet);
    ControllerPacketResult receive_controller_packet(const Packet& packet);
    void record_error() { stats_.error_count++; }
    const SimulatorStats& stats() const { return stats_; }

  private:
    SimulatorStep packet_step(const CatalogPacket& packet, const char* event, uint32_t delay_ms);
    SimulatorStep normal_idle_step();
    SimulatorStep config_refresh_step();
    SimulatorStep active_defrost_step();
    SimulatorStep rx_stress_step();

    Playbook playbook_{Playbook::PAUSED};
    bool active_{false};
    float interval_scale_{1.0f};
    size_t cursor_{0};
    SimulatorStats stats_{};
};

} // namespace hwp_simulator
} // namespace esphome
