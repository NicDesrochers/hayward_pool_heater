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

#include <cassert>
#include <functional>
#include <string>
#include <vector>

using esphome::hwp::wire::Packet;
using esphome::hwp::wire::PacketSource;
using esphome::hwp::wire::checksum_valid;
using esphome::hwp::wire::CONTROLLER_REPEAT_COUNT;
using esphome::hwp::wire::decode_packet_group_symbols;
using esphome::hwp::wire::decode_packet_symbols;
using esphome::hwp::wire::encode_packet_symbols;
using esphome::hwp::wire::refresh_checksum;
using esphome::hwp_simulator::Playbook;
using esphome::hwp_simulator::SimulatorEngine;
using esphome::hwp_simulator::find_catalog_packet;
using esphome::hwp_simulator::playbook_from_string;
using esphome::hwp_simulator::playbook_to_string;

Packet controller_command(
    const char* catalog_id, const std::function<void(Packet&)>& mutate) {
    const auto* catalog_packet = find_catalog_packet(catalog_id);
    assert(catalog_packet != nullptr);
    Packet command = catalog_packet->packet;
    command.source = PacketSource::CONTROLLER;
    mutate(command);
    refresh_checksum(command.data.data(), command.length);
    assert(checksum_valid(command.data.data(), command.length));
    return command;
}

void assert_replayed_config(
    SimulatorEngine& engine, uint8_t frame, const std::function<void(const Packet&)>& check) {
    engine.set_playbook(Playbook::CONFIG_REFRESH);
    engine.set_active(true);
    for (int index = 0; index < 16; ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        if (step.packet.length == 12 && step.packet.data[0] == frame) {
            assert(step.packet.source == PacketSource::HEATER);
            assert(checksum_valid(step.packet.data.data(), step.packet.length));
            check(step.packet);
            return;
        }
    }
    assert(false && "expected config frame was not replayed");
}

void test_wire_codec_round_trip_heater_long_packet() {
    const auto* packet = find_catalog_packet("base-config-5-normal");
    assert(packet != nullptr);
    auto symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::HEATER, true);
    assert(symbols.size() == 1 + packet->packet.length * 8 + 1);

    Packet decoded;
    assert(decode_packet_symbols(symbols.data(), symbols.size(), PacketSource::HEATER, decoded));
    assert(decoded.length == packet->packet.length);
    assert(decoded.data[0] == 0x85);
    assert(decoded.data[11] == 0x45);
}

void test_wire_codec_source_spacing() {
    const auto* packet = find_catalog_packet("base-config-1");
    assert(packet != nullptr);
    auto heater_symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::HEATER, false);
    auto controller_symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::CONTROLLER, false);
    assert(heater_symbols.back().duration1 == esphome::hwp::wire::HEATER_FRAME_SPACING_US);
    assert(controller_symbols.back().duration1 == esphome::hwp::wire::CONTROLLER_FRAME_SPACING_US);

    heater_symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::HEATER, true);
    controller_symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::CONTROLLER, true);
    assert(heater_symbols.back().duration1 == esphome::hwp::wire::HEATER_GROUP_SPACING_US);
    assert(controller_symbols.back().duration1 == esphome::hwp::wire::CONTROLLER_GROUP_SPACING_US);
}

void test_wire_codec_round_trip_short_packet() {
    const auto* packet = find_catalog_packet("base-cond-d");
    assert(packet != nullptr);
    auto symbols = encode_packet_symbols(
        packet->packet.data.data(), packet->packet.length, PacketSource::HEATER, true);
    Packet decoded;
    assert(decode_packet_symbols(symbols.data(), symbols.size(), PacketSource::HEATER, decoded));
    assert(decoded.length == 9);
    assert(decoded.data[0] == 0xDD);
    assert(decoded.data[8] == 0x48);
}

void test_wire_codec_round_trip_controller_command() {
    const auto* packet = find_catalog_packet("base-config-5-normal");
    assert(packet != nullptr);
    Packet command = packet->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[2] = 0x40;
    command.data[4] = 0x1E;
    refresh_checksum(command.data.data(), command.length);
    assert(command.data[11] == 0x85);

    auto symbols =
        encode_packet_symbols(command.data.data(), command.length, PacketSource::CONTROLLER, true);
    Packet decoded;
    assert(decode_packet_symbols(symbols.data(), symbols.size(), PacketSource::CONTROLLER, decoded));
    assert(decoded.source == PacketSource::CONTROLLER);
    assert(decoded.length == 12);
    assert(decoded.data[0] == 0x85);
    assert(decoded.data[2] == 0x40);
    assert(decoded.data[11] == 0x85);
}

void test_wire_codec_decodes_repeated_controller_group_once() {
    const auto* config_1 = find_catalog_packet("base-config-1");
    assert(config_1 != nullptr);
    Packet command = config_1->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[8] = 0x3C;
    refresh_checksum(command.data.data(), command.length);
    assert(command.data[11] == 0xA6);

    std::vector<esphome::hwp::wire::PulseSymbol> group_symbols;
    for (uint8_t repeat = 0; repeat < CONTROLLER_REPEAT_COUNT; ++repeat) {
        auto symbols = encode_packet_symbols(
            command.data.data(), command.length, PacketSource::CONTROLLER,
            repeat + 1 == CONTROLLER_REPEAT_COUNT);
        group_symbols.insert(group_symbols.end(), symbols.begin(), symbols.end());
    }

    const auto packets = decode_packet_group_symbols(
        group_symbols.data(), group_symbols.size(), PacketSource::CONTROLLER);
    assert(packets.size() == 1);
    assert(packets[0].source == PacketSource::CONTROLLER);
    assert(packets[0].length == 12);
    assert(packets[0].data[0] == 0x81);
    assert(packets[0].data[8] == 0x3C);
    assert(packets[0].data[11] == 0xA6);
}

void test_playbook_mapping() {
    assert(playbook_from_string("normal_idle").value() == Playbook::NORMAL_IDLE);
    assert(std::string(playbook_to_string(Playbook::RX_STRESS)) == "rx_stress");
    assert(!playbook_from_string("surprise").has_value());
}

void test_normal_idle_steps() {
    SimulatorEngine engine;
    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);

    auto step = engine.step_once();
    assert(step.has_packet);
    assert(std::string(step.event) == "normal_idle");
    assert(checksum_valid(step.packet.data.data(), step.packet.length));
    assert(engine.stats().step == 1);
    assert(engine.stats().packet_count == 1);
}

void test_normal_idle_realistic_frame_order() {
    SimulatorEngine engine;
    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);

    const uint8_t expected_frames[] = {
        0x86, 0x84, 0x85, 0xD1, 0xD2, 0x82, 0x81, 0xD1,
        0x83, 0xD2, 0xDD, 0xD1, 0xD2, 0x82, 0x81, 0xD1,
    };
    const uint8_t expected_lengths[] = {
        12, 12, 12, 12, 12, 12, 12, 12,
        12, 9, 9, 12, 12, 12, 12, 12,
    };
    for (size_t index = 0; index < sizeof(expected_frames); ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        assert(step.packet.data[0] == expected_frames[index]);
        assert(step.packet.length == expected_lengths[index]);
        assert(checksum_valid(step.packet.data.data(), step.packet.length));
    }
}

void test_normal_idle_temperature_drift() {
    SimulatorEngine engine;
    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);

    Packet first{};
    bool found_first = false;
    bool found_drift = false;
    for (int index = 0; index < 40; ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        assert(checksum_valid(step.packet.data.data(), step.packet.length));
        if (step.packet.length == 12 && step.packet.data[0] == 0xD2) {
            if (!found_first) {
                first = step.packet;
                found_first = true;
            } else if (first.data[4] != step.packet.data[4]) {
                assert(first.data[5] != step.packet.data[5]);
                assert(first.data[6] != step.packet.data[6]);
                assert(first.data[11] != step.packet.data[11]);
                found_drift = true;
                break;
            }
        }
    }

    assert(found_first);
    assert(found_drift);
}

void test_interval_scale_and_pause() {
    SimulatorEngine engine;
    engine.set_playbook(Playbook::CONFIG_REFRESH);
    engine.set_interval_scale(0.5f);
    engine.set_active(true);
    auto step = engine.step_once();
    assert(step.delay_ms > 0);
    assert(step.delay_ms < 11000);

    engine.set_active(false);
    auto paused = engine.step_once();
    assert(!paused.has_packet);
    assert(std::string(paused.event) == "paused");
}

void test_config5_command_echo() {
    const auto* command = find_catalog_packet("base-config-5-normal");
    assert(command != nullptr);
    Packet controller_packet = command->packet;
    controller_packet.source = PacketSource::CONTROLLER;
    controller_packet.data[2] = 0x40;
    controller_packet.data[4] = 0x1E;
    controller_packet.data[11] = 0x85;

    SimulatorEngine engine;
    auto echo = engine.handle_controller_packet(controller_packet);
    assert(echo.has_value());
    assert(echo->has_packet);
    assert(std::string(echo->packet_id) == "config-registry");
    assert(echo->packet.data[2] == 0x40);
    assert(echo->packet.data[4] == 0x1E);
    assert(echo->packet.data[11] == 0x85);
}

void test_receive_controller_config5_eco_echo() {
    const auto* command_base = find_catalog_packet("base-config-5-normal");
    assert(command_base != nullptr);
    Packet command = command_base->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[2] = 0x40;
    command.data[4] = 0x1E;
    refresh_checksum(command.data.data(), command.length);

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(std::string(result.status) == "updated simulator registry");
    assert(std::string(result.echo.packet_id) == "config-registry");
    assert(result.echo.packet.data[2] == 0x40);
    assert(result.echo.packet.data[4] == 0x1E);
    assert(result.echo.packet.data[11] == 0x85);
    assert(engine.stats().rx_packet_count == 1);
    assert(engine.stats().echo_count == 1);
}

void test_receive_controller_config5_normal_echo() {
    const auto* eco_echo = find_catalog_packet("base-config-5-eco-echo");
    assert(eco_echo != nullptr);
    Packet command = eco_echo->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[2] = 0x00;
    command.data[4] = 0x4A;
    refresh_checksum(command.data.data(), command.length);
    assert(command.data[11] == 0x71);

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(std::string(result.status) == "updated simulator registry");
    assert(std::string(result.echo.packet_id) == "config-registry");
    assert(result.echo.packet.data[2] == 0x00);
    assert(result.echo.packet.data[4] == 0x4A);
    assert(result.echo.packet.data[11] == 0x71);
}

void test_receive_controller_same_config_records_without_echo() {
    const auto* config_3 = find_catalog_packet("base-config-3");
    assert(config_3 != nullptr);
    Packet command = config_3->packet;
    command.source = PacketSource::CONTROLLER;

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(!result.has_echo);
    assert(std::string(result.status) == "accepted controller packet");
    assert(engine.stats().rx_packet_count == 1);
    assert(engine.stats().echo_count == 0);
    assert(engine.stats().error_count == 0);
}

void test_receive_controller_config1_updates_replayed_state() {
    const auto* config_1 = find_catalog_packet("base-config-1");
    assert(config_1 != nullptr);
    Packet command = config_1->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[10] = 0x2D;
    refresh_checksum(command.data.data(), command.length);
    assert(command.data[11] == 0xA2);

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(std::string(result.status) == "updated simulator registry");
    assert(result.echo.packet.data[10] == 0x2D);
    assert(result.echo.packet.data[11] == 0xA2);
    assert(engine.stats().rx_packet_count == 1);
    assert(engine.stats().echo_count == 1);
    assert(engine.stats().error_count == 0);

    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);
    bool saw_config_1 = false;
    for (int index = 0; index < 12; ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        if (step.packet.length == 12 && step.packet.data[0] == 0x81) {
            saw_config_1 = true;
            assert(step.packet.source == PacketSource::HEATER);
            assert(step.packet.data[10] == 0x2D);
            assert(step.packet.data[11] == 0xA2);
            assert(checksum_valid(step.packet.data.data(), step.packet.length));
            break;
        }
    }
    assert(saw_config_1);
}

void test_receive_controller_config2_updates_replayed_state() {
    const auto* config_2 = find_catalog_packet("base-config-2");
    assert(config_2 != nullptr);
    Packet command = config_2->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[3] = 0x04;
    refresh_checksum(command.data.data(), command.length);
    assert(command.data[11] == 0x99);

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(std::string(result.status) == "updated simulator registry");
    assert(result.echo.packet.data[3] == 0x04);
    assert(result.echo.packet.data[11] == 0x99);
    assert(engine.stats().rx_packet_count == 1);
    assert(engine.stats().echo_count == 1);
    assert(engine.stats().error_count == 0);

    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);
    bool saw_config_2 = false;
    for (int index = 0; index < 12; ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        if (step.packet.length == 12 && step.packet.data[0] == 0x82) {
            saw_config_2 = true;
            assert(step.packet.source == PacketSource::HEATER);
            assert(step.packet.data[3] == 0x04);
            assert(step.packet.data[11] == 0x99);
            assert(checksum_valid(step.packet.data.data(), step.packet.length));
            break;
        }
    }
    assert(saw_config_2);
}

void test_receive_controller_config3_registry_write_echoes_once() {
    const auto* config_3 = find_catalog_packet("base-config-3");
    assert(config_3 != nullptr);
    Packet command = config_3->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[8] = 0x84;
    refresh_checksum(command.data.data(), command.length);

    SimulatorEngine engine;
    auto first = engine.receive_controller_packet(command);
    auto repeat = engine.receive_controller_packet(command);

    assert(first.accepted);
    assert(first.has_echo);
    assert(first.echo.packet.source == PacketSource::HEATER);
    assert(first.echo.packet.data[0] == 0x83);
    assert(first.echo.packet.data[8] == 0x84);
    assert(checksum_valid(first.echo.packet.data.data(), first.echo.packet.length));
    assert(repeat.accepted);
    assert(!repeat.has_echo);
    assert(std::string(repeat.status) == "accepted controller packet");
    assert(engine.stats().rx_packet_count == 2);
    assert(engine.stats().echo_count == 1);
}

void test_config1_writable_inventory_persists_and_replays() {
    Packet command = controller_command("base-config-1", [](Packet& packet) {
        packet.data[2] = 0x18;  // power/mode/H02 byte
        packet.data[3] = 0x70;  // R01
        packet.data[4] = 0x54;  // R02
        packet.data[5] = 0x74;  // R03
        packet.data[6] = 0x40;  // R04
        packet.data[7] = 0x41;  // R05
        packet.data[8] = 0x42;  // R06
        packet.data[9] = 0x43;  // R07
        packet.data[10] = 0x2D; // F12
    });

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(result.echo.packet.data[0] == 0x81);
    assert(result.echo.packet.data[10] == 0x2D);
    assert_replayed_config(engine, 0x81, [](const Packet& packet) {
        assert(packet.data[2] == 0x18);
        assert(packet.data[3] == 0x70);
        assert(packet.data[4] == 0x54);
        assert(packet.data[5] == 0x74);
        assert(packet.data[6] == 0x40);
        assert(packet.data[7] == 0x41);
        assert(packet.data[8] == 0x42);
        assert(packet.data[9] == 0x43);
        assert(packet.data[10] == 0x2D);
    });
}

void test_config2_writable_inventory_persists_and_replays() {
    Packet command = controller_command("base-config-2", [](Packet& packet) {
        packet.data[2] = 0x1E;  // F01/F10
        packet.data[3] = 0x04;  // D01
        packet.data[4] = 0x58;  // D02
        packet.data[5] = 0x46;  // D03
        packet.data[6] = 0x12;  // D04
        packet.data[10] = 0x63; // F13
    });

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(result.echo.packet.data[0] == 0x82);
    assert(result.echo.packet.data[3] == 0x04);
    assert_replayed_config(engine, 0x82, [](const Packet& packet) {
        assert(packet.data[2] == 0x1E);
        assert(packet.data[3] == 0x04);
        assert(packet.data[4] == 0x58);
        assert(packet.data[5] == 0x46);
        assert(packet.data[6] == 0x12);
        assert(packet.data[10] == 0x63);
    });
}

void test_config4_writable_inventory_persists_and_replays() {
    Packet command = controller_command("base-config-4", [](Packet& packet) {
        packet.data[2] = 0x8A; // F02
        packet.data[3] = 0x5B; // F03
        packet.data[4] = 0x52; // F04
        packet.data[5] = 0x54; // F05
        packet.data[6] = 0x66; // F06
        packet.data[7] = 0x76; // F07
        packet.data[8] = 0x01; // F08
        packet.data[9] = 0x02; // F09
    });

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(result.echo.packet.data[0] == 0x84);
    assert_replayed_config(engine, 0x84, [](const Packet& packet) {
        assert(packet.data[2] == 0x8A);
        assert(packet.data[3] == 0x5B);
        assert(packet.data[4] == 0x52);
        assert(packet.data[5] == 0x54);
        assert(packet.data[6] == 0x66);
        assert(packet.data[7] == 0x76);
        assert(packet.data[8] == 0x01);
        assert(packet.data[9] == 0x02);
    });
}

void test_config5_writable_inventory_persists_and_replays() {
    Packet command = controller_command("base-config-5-normal", [](Packet& packet) {
        packet.data[2] = 0x4C;  // U01/D06/F11 flags
        packet.data[3] = 0x08;  // D05
        packet.data[9] = 0x01;  // U02 high byte
        packet.data[10] = 0x00; // U02 low byte
    });

    SimulatorEngine engine;
    auto result = engine.receive_controller_packet(command);

    assert(result.accepted);
    assert(result.has_echo);
    assert(result.echo.packet.data[0] == 0x85);
    assert_replayed_config(engine, 0x85, [](const Packet& packet) {
        assert(packet.data[2] == 0x4C);
        assert(packet.data[3] == 0x08);
        assert(packet.data[9] == 0x01);
        assert(packet.data[10] == 0x00);
    });
}

void test_config3_and_config6_raw_registry_packets_persist_and_replay() {
    Packet config_3 = controller_command("base-config-3", [](Packet& packet) {
        packet.data[7] = 0x4E;
        packet.data[8] = 0x84;
        packet.data[9] = 0x48;
        packet.data[10] = 0x8A;
    });
    Packet config_6 = controller_command("base-config-6", [](Packet& packet) {
        packet.data[2] = 0x01;
        packet.data[10] = 0x02;
    });

    SimulatorEngine engine;
    auto first = engine.receive_controller_packet(config_3);
    auto second = engine.receive_controller_packet(config_6);

    assert(first.accepted);
    assert(first.has_echo);
    assert(second.accepted);
    assert(second.has_echo);
    assert_replayed_config(engine, 0x83, [](const Packet& packet) {
        assert(packet.data[7] == 0x4E);
        assert(packet.data[8] == 0x84);
        assert(packet.data[9] == 0x48);
        assert(packet.data[10] == 0x8A);
    });
    assert_replayed_config(engine, 0x86, [](const Packet& packet) {
        assert(packet.data[2] == 0x01);
        assert(packet.data[10] == 0x02);
    });
}

void test_multiple_changed_controller_packets_echo_first_and_store_all() {
    Packet config_2 = controller_command("base-config-2", [](Packet& packet) {
        packet.data[3] = 0x04;
    });
    Packet config_1 = controller_command("base-config-1", [](Packet& packet) {
        packet.data[10] = 0x2D;
    });

    SimulatorEngine engine;
    auto result = engine.receive_controller_packets({config_2, config_1});

    assert(result.accepted);
    assert(result.has_echo);
    assert(result.echo.packet.data[0] == 0x82);
    assert(result.echo.packet.data[3] == 0x04);
    assert(engine.stats().rx_packet_count == 2);
    assert(engine.stats().echo_count == 1);
    assert_replayed_config(engine, 0x82, [](const Packet& packet) {
        assert(packet.data[3] == 0x04);
    });
    assert_replayed_config(engine, 0x81, [](const Packet& packet) {
        assert(packet.data[10] == 0x2D);
    });
}

void test_receive_controller_config1_group_updates_replayed_state() {
    const auto* config_1 = find_catalog_packet("base-config-1");
    assert(config_1 != nullptr);
    Packet command = config_1->packet;
    command.source = PacketSource::CONTROLLER;
    command.data[8] = 0x3C;
    refresh_checksum(command.data.data(), command.length);

    std::vector<esphome::hwp::wire::PulseSymbol> group_symbols;
    for (uint8_t repeat = 0; repeat < CONTROLLER_REPEAT_COUNT; ++repeat) {
        auto symbols = encode_packet_symbols(
            command.data.data(), command.length, PacketSource::CONTROLLER,
            repeat + 1 == CONTROLLER_REPEAT_COUNT);
        group_symbols.insert(group_symbols.end(), symbols.begin(), symbols.end());
    }
    const auto packets = decode_packet_group_symbols(
        group_symbols.data(), group_symbols.size(), PacketSource::CONTROLLER);

    SimulatorEngine engine;
    for (const auto& packet : packets) {
        auto result = engine.receive_controller_packet(packet);
        assert(result.accepted);
        assert(std::string(result.status) == "updated simulator registry");
    }
    assert(engine.stats().rx_packet_count == 1);

    engine.set_playbook(Playbook::NORMAL_IDLE);
    engine.set_active(true);
    bool saw_config_1 = false;
    for (int index = 0; index < 12; ++index) {
        auto step = engine.step_once();
        assert(step.has_packet);
        if (step.packet.length == 12 && step.packet.data[0] == 0x81) {
            saw_config_1 = true;
            assert(step.packet.source == PacketSource::HEATER);
            assert(step.packet.data[8] == 0x3C);
            assert(step.packet.data[11] == 0xA6);
            break;
        }
    }
    assert(saw_config_1);
}

void test_receive_controller_rejects_invalid_packets_without_echo() {
    const auto* config_5 = find_catalog_packet("base-config-5-normal");
    assert(config_5 != nullptr);

    Packet bad_checksum = config_5->packet;
    bad_checksum.source = PacketSource::CONTROLLER;
    bad_checksum.data[11] ^= 0x01;

    SimulatorEngine engine;
    auto checksum_result = engine.receive_controller_packet(bad_checksum);
    assert(!checksum_result.accepted);
    assert(!checksum_result.has_echo);
    assert(engine.stats().error_count == 1);

    Packet wrong_source = config_5->packet;
    auto source_result = engine.receive_controller_packet(wrong_source);
    assert(!source_result.accepted);
    assert(!source_result.has_echo);
    assert(engine.stats().error_count == 2);
}

void test_stress_playbook_counts_invalid_checksum() {
    SimulatorEngine engine;
    engine.set_playbook(Playbook::RX_STRESS);
    engine.set_active(true);
    engine.step_once();
    engine.step_once();
    assert(engine.stats().error_count == 1);
}

int main() {
    test_wire_codec_round_trip_heater_long_packet();
    test_wire_codec_source_spacing();
    test_wire_codec_round_trip_short_packet();
    test_wire_codec_round_trip_controller_command();
    test_wire_codec_decodes_repeated_controller_group_once();
    test_playbook_mapping();
    test_normal_idle_steps();
    test_normal_idle_realistic_frame_order();
    test_normal_idle_temperature_drift();
    test_interval_scale_and_pause();
    test_config5_command_echo();
    test_receive_controller_config5_eco_echo();
    test_receive_controller_config5_normal_echo();
    test_receive_controller_same_config_records_without_echo();
    test_receive_controller_config1_updates_replayed_state();
    test_receive_controller_config2_updates_replayed_state();
    test_receive_controller_config3_registry_write_echoes_once();
    test_config1_writable_inventory_persists_and_replays();
    test_config2_writable_inventory_persists_and_replays();
    test_config4_writable_inventory_persists_and_replays();
    test_config5_writable_inventory_persists_and_replays();
    test_config3_and_config6_raw_registry_packets_persist_and_replay();
    test_multiple_changed_controller_packets_echo_first_and_store_all();
    test_receive_controller_config1_group_updates_replayed_state();
    test_receive_controller_rejects_invalid_packets_without_echo();
    test_stress_playbook_counts_invalid_checksum();
    return 0;
}
