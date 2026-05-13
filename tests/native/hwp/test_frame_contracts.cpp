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
#include "FrameClock.h"
#include "FrameConditions1.h"
#include "FrameConditions1B.h"
#include "FrameConditions2.h"
#include "FrameConditions2B.h"
#include "FrameConditionsD.h"
#include "FrameConf1.h"
#include "FrameConf2.h"
#include "FrameConf3.h"
#include "FrameConf4.h"
#include "FrameConf5.h"
#include "FrameConf6.h"
#include "protocol_core.h"

#include <array>
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdint>

namespace hwp = esphome::hwp;
namespace protocol = esphome::hwp::protocol;

using Packet = std::array<uint8_t, protocol::FRAME_DATA_LENGTH>;
using ShortPacket = std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT>;

void assert_float_eq(float actual, float expected) {
    assert(std::fabs(actual - expected) < 0.01f);
}

hwp::BaseFrame make_frame(const Packet& packet, hwp::frame_source_t source) {
    hwp::BaseFrame frame;
    std::memcpy(frame.packet.data, packet.data(), packet.size());
    frame.packet.data_len = packet.size();
    frame.set_source(source);
    assert(frame.packet.is_checksum_valid());
    return frame;
}

hwp::BaseFrame make_frame(const ShortPacket& packet, hwp::frame_source_t source) {
    hwp::BaseFrame frame;
    std::memcpy(frame.packet.data, packet.data(), packet.size());
    frame.packet.data_len = packet.size();
    frame.set_source(source);
    assert(frame.packet.is_checksum_valid());
    return frame;
}

template <typename FrameType>
FrameType stage_frame(const Packet& packet, hwp::frame_source_t source) {
    auto base = make_frame(packet, source);
    FrameType frame;
    frame.stage(base);
    return frame;
}

void test_frame_matching_contracts() {
    const Packet conf1 = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x37, 0xA3};
    const Packet conf2 = {
        0x82, 0xB1, 0x46, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xDF};
    const Packet conf4 = {
        0x84, 0xB1, 0x8F, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x12};
    const Packet conf5 = {
        0x85, 0xB1, 0x08, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x4D};

    hwp::FrameConf1 frame1;
    hwp::FrameConf2 frame2;
    hwp::FrameConf4 frame4;
    hwp::FrameConf5 frame5;

    auto base1 = make_frame(conf1, hwp::SOURCE_CONTROLLER);
    auto base2 = make_frame(conf2, hwp::SOURCE_CONTROLLER);
    auto base4 = make_frame(conf4, hwp::SOURCE_CONTROLLER);
    auto base5 = make_frame(conf5, hwp::SOURCE_CONTROLLER);

    assert(hwp::FrameConf1::matches(frame1, base1));
    assert(hwp::FrameConf2::matches(frame2, base2));
    assert(hwp::FrameConf4::matches(frame4, base4));
    assert(hwp::FrameConf5::matches(frame5, base5));

    assert(!hwp::FrameConf1::matches(frame1, base2));
    assert(!hwp::FrameConf2::matches(frame2, base4));
    assert(!hwp::FrameConf4::matches(frame4, base5));
    assert(!hwp::FrameConf5::matches(frame5, base1));
}

void test_passive_frame_matching_contracts() {
    const Packet conf3 = {
        0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x4C, 0x82, 0x46, 0x8C, 0x8D};
    const Packet conf6 = {
        0x86, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x37};
    const Packet cond1 = {
        0xD1, 0xB1, 0x05, 0x00, 0x00, 0x00, 0x00, 0x78, 0x5E, 0x77, 0x1B, 0xEF};
    const Packet cond1b = {
        0xD1, 0xB1, 0x00, 0x02, 0x0F, 0x00, 0x00, 0x78, 0x5E, 0x77, 0x1B, 0xFB};
    const Packet cond2 = {
        0xD2, 0xB1, 0x11, 0x5E, 0x77, 0x6E, 0x78, 0x00, 0x64, 0x00, 0x00, 0xB3};
    const ShortPacket cond2b = {0xD2, 0x1B, 0x1D, 0x28, 0x15, 0x0D, 0xA0, 0xEA, 0x0C};
    const ShortPacket condd = {0xDD, 0x1D, 0x1D, 0x19, 0x11, 0x1E, 0x00, 0x00, 0x82};
    const Packet clock = {
        0xCF, 0xB1, 0x00, 0x00, 0x15, 0x03, 0x05, 0x11, 0x06, 0x00, 0x00, 0xB4};

    hwp::FrameConf3 frame_conf3;
    hwp::FrameConf6 frame_conf6;
    hwp::FrameConditions1 frame_cond1;
    hwp::FrameConditions1B frame_cond1b;
    hwp::FrameConditions2 frame_cond2;
    hwp::FrameConditions2B frame_cond2b;
    hwp::FrameConditionsD frame_condd;
    hwp::FrameClock frame_clock;

    auto base_conf3 = make_frame(conf3, hwp::SOURCE_HEATER);
    auto base_conf6 = make_frame(conf6, hwp::SOURCE_HEATER);
    auto base_cond1 = make_frame(cond1, hwp::SOURCE_HEATER);
    auto base_cond1b = make_frame(cond1b, hwp::SOURCE_HEATER);
    auto base_cond2 = make_frame(cond2, hwp::SOURCE_HEATER);
    auto base_cond2b = make_frame(cond2b, hwp::SOURCE_HEATER);
    auto base_condd = make_frame(condd, hwp::SOURCE_HEATER);
    auto base_clock = make_frame(clock, hwp::SOURCE_CONTROLLER);

    assert(hwp::FrameConf3::matches(frame_conf3, base_conf3));
    assert(hwp::FrameConf6::matches(frame_conf6, base_conf6));
    assert(hwp::FrameConditions1::matches(frame_cond1, base_cond1));
    assert(hwp::FrameConditions1B::matches(frame_cond1b, base_cond1b));
    assert(hwp::FrameConditions2::matches(frame_cond2, base_cond2));
    assert(hwp::FrameConditions2B::matches(frame_cond2b, base_cond2b));
    assert(hwp::FrameConditionsD::matches(frame_condd, base_condd));
    assert(hwp::FrameClock::matches(frame_clock, base_clock));

    assert(!hwp::FrameConf3::matches(frame_conf3, base_conf6));
    assert(!hwp::FrameConf6::matches(frame_conf6, base_conf3));
    assert(!hwp::FrameConditions1::matches(frame_cond1, base_cond1b));
    assert(!hwp::FrameConditions1B::matches(frame_cond1b, base_cond1));
    assert(!hwp::FrameConditions2::matches(frame_cond2, base_cond2b));
    assert(!hwp::FrameConditions2B::matches(frame_cond2b, base_cond2));
    assert(!hwp::FrameConditionsD::matches(frame_condd, base_cond2b));
    assert(!hwp::FrameClock::matches(frame_clock, base_conf3));
}

void test_conf2_parse_matches_protocol_core() {
    const Packet f01 = {
        0x82, 0xB1, 0x46, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xDF};
    const Packet f10 = {
        0x82, 0xB1, 0x3E, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xD7};
    const Packet f13 = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x32, 0x9D};

    {
        auto frame = stage_frame<hwp::FrameConf2>(f01, hwp::SOURCE_CONTROLLER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.fan_mode.has_value());
        assert(data.fan_mode->to_raw() ==
               protocol::read_conf2_f01_fan_mode(f01.data(), f01.size()).value());
    }

    {
        auto frame = stage_frame<hwp::FrameConf2>(f10, hwp::SOURCE_CONTROLLER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.f10_fan_speed_control_temp.has_value());
        assert(data.f10_fan_speed_control_temp->encode() ==
               protocol::read_conf2_f10_fan_speed_control_temp(f10.data(), f10.size()).value());
    }

    {
        auto frame = stage_frame<hwp::FrameConf2>(f13, hwp::SOURCE_CONTROLLER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.f13_max_fan_voltage_pct.has_value());
        assert_float_eq(
            data.f13_max_fan_voltage_pct.value(),
            protocol::read_conf2_f13_max_fan_voltage_pct(f13.data(), f13.size()).value());
    }
}

void test_conf4_parse_matches_protocol_core() {
    const Packet packets[] = {
        {0x84, 0xB1, 0x8F, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x12},
        {0x84, 0xB1, 0x8C, 0x64, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x19},
        {0x84, 0xB1, 0x8C, 0x5A, 0x51, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x51, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x65, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x7B, 0x00, 0x00, 0x78, 0x12},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x17, 0x00, 0x78, 0x26},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x10, 0x78, 0x1F},
    };

    for (uint8_t field = 2; field <= 9; ++field) {
        auto frame = stage_frame<hwp::FrameConf4>(packets[field - 2], hwp::SOURCE_CONTROLLER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        const float expected =
            protocol::read_conf4_fan_parameter(
                packets[field - 2].data(), packets[field - 2].size(), field)
                .value();
        switch (field) {
        case 2:
            assert_float_eq(data.f02_fan_high_speed_cool_setpoint.value(), expected);
            break;
        case 3:
            assert_float_eq(data.f03_fan_low_speed_temp_in_cooling_set_point.value(), expected);
            break;
        case 4:
            assert_float_eq(data.f04_fan_stop_temp_in_cooling_set_point.value(), expected);
            break;
        case 5:
            assert_float_eq(data.f05_fan_high_speed_temp_in_heating_set_point.value(), expected);
            break;
        case 6:
            assert_float_eq(data.f06_fan_low_speed_temp_in_heating_set_point.value(), expected);
            break;
        case 7:
            assert_float_eq(data.f07_fan_stop_temp_in_heating_set_point.value(), expected);
            break;
        case 8:
            assert_float_eq(data.f08_fan_low_speed_running_time.value(), expected);
            break;
        case 9:
            assert_float_eq(data.f09_fan_stop_low_speed_running_time.value(), expected);
            break;
        }
    }
}

void test_conf5_parse_matches_protocol_core() {
    const Packet f11 = {
        0x85, 0xB1, 0x08, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x4D};
    auto frame = stage_frame<hwp::FrameConf5>(f11, hwp::SOURCE_CONTROLLER);
    hwp::heat_pump_data_t data;
    frame.parse(data);
    assert(data.f11_speed_control_module.has_value());
    assert(data.f11_speed_control_module->encode() ==
           protocol::read_conf5_f11_speed_control_module(f11.data(), f11.size()).value());
}

void test_conf1_source_gated_parse_matches_protocol_core() {
    const Packet f12 = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x37, 0xA3};

    auto controller_frame = stage_frame<hwp::FrameConf1>(f12, hwp::SOURCE_CONTROLLER);
    hwp::heat_pump_data_t controller_data;
    controller_frame.parse(controller_data);
    assert(!controller_data.f12_min_fan_voltage_pct.has_value());

    auto heater_frame = stage_frame<hwp::FrameConf1>(f12, hwp::SOURCE_HEATER);
    hwp::heat_pump_data_t heater_data;
    heater_frame.parse(heater_data);
    assert(heater_data.f12_min_fan_voltage_pct.has_value());
    assert_float_eq(heater_data.f12_min_fan_voltage_pct.value(),
                    protocol::read_conf1_f12_min_fan_voltage_pct(f12.data(), f12.size()).value());
}

void test_conf1_extended_setpoint_runtime_contract() {
    const Packet r02_35_0 = {
        0x81, 0xB1, 0x26, 0x6E, 0x82, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xD2};

    auto frame = stage_frame<hwp::FrameConf1>(r02_35_0, hwp::SOURCE_CONTROLLER);
    assert_float_eq(frame.data().r02_setpoint_heating.decode(), 35.0f);
    assert_float_eq(
        frame.data().r02_setpoint_heating.decode(),
        protocol::read_conf1_temperature_parameter(r02_35_0.data(), r02_35_0.size(), 2).value());

    frame.set_target_cooling(34.0f);
    assert(frame.data().r01_setpoint_cooling.raw == 0x80);
    frame.set_target_heating(35.0f);
    assert(frame.data().r02_setpoint_heating.raw == 0x82);
    frame.set_target_auto(33.5f);
    assert(frame.data().r03_setpoint_auto.raw == 0x7F);
}

void test_condition_parse_matches_protocol_core() {
    const Packet cond1 = {
        0xD1, 0xB1, 0x05, 0x00, 0x00, 0x00, 0x00, 0x78, 0x5E, 0x77, 0x1B, 0xEF};
    const Packet cond1b = {
        0xD1, 0xB1, 0x00, 0x02, 0x0F, 0x00, 0x00, 0x78, 0x5E, 0x77, 0x1B, 0xFB};
    const Packet cond2 = {
        0xD2, 0xB1, 0x11, 0x5E, 0x77, 0x6E, 0x78, 0x00, 0x64, 0x00, 0x00, 0xB3};

    {
        auto frame = stage_frame<hwp::FrameConditions1>(cond1, hwp::SOURCE_HEATER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.t02_temperature_inlet.has_value());
        assert_float_eq(data.t02_temperature_inlet.value(),
                        protocol::read_cond1_inlet_temperature(cond1.data(), cond1.size()).value());
    }

    {
        auto frame = stage_frame<hwp::FrameConditions1B>(cond1b, hwp::SOURCE_HEATER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.t02_temperature_inlet.has_value());
        assert(data.S02_water_flow.has_value());
        assert_float_eq(data.t02_temperature_inlet.value(),
                        protocol::read_cond1_inlet_temperature(cond1b.data(), cond1b.size()).value());
        assert(static_cast<bool>(data.S02_water_flow.value()) ==
               (protocol::read_cond1b_water_flow(cond1b.data(), cond1b.size()).value() != 0));
    }

    {
        auto frame = stage_frame<hwp::FrameConditions2>(cond2, hwp::SOURCE_HEATER);
        hwp::heat_pump_data_t data;
        frame.parse(data);
        assert(data.t03_temperature_outlet.has_value());
        assert(data.t04_temperature_coil.has_value());
        assert(data.t06_temperature_exhaust.has_value());
        assert_float_eq(data.t03_temperature_outlet.value(),
                        protocol::read_cond2_temperature(cond2.data(), cond2.size(), 3).value());
        assert_float_eq(data.t04_temperature_coil.value(),
                        protocol::read_cond2_temperature(cond2.data(), cond2.size(), 4).value());
        assert_float_eq(data.t06_temperature_exhaust.value(),
                        protocol::read_cond2_temperature(cond2.data(), cond2.size(), 6).value());
        assert(protocol::read_cond2_temperature(cond2.data(), cond2.size(), 8).has_value());
    }
}

void test_conf3_parse_matches_protocol_core() {
    const Packet conf3 = {
        0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x4C, 0x82, 0x46, 0x8C, 0x8D};
    auto frame = stage_frame<hwp::FrameConf3>(conf3, hwp::SOURCE_HEATER);
    hwp::heat_pump_data_t data;
    frame.parse(data);
    assert(data.r08_min_cool_setpoint.has_value());
    assert(data.r09_max_cooling_setpoint.has_value());
    assert(data.r10_min_heating_setpoint.has_value());
    assert(data.r11_max_heating_setpoint.has_value());
    assert_float_eq(data.r08_min_cool_setpoint.value(),
                    protocol::read_conf3_setpoint_limit(conf3.data(), conf3.size(), 8).value());
    assert_float_eq(data.r09_max_cooling_setpoint.value(),
                    protocol::read_conf3_setpoint_limit(conf3.data(), conf3.size(), 9).value());
    assert_float_eq(data.r10_min_heating_setpoint.value(),
                    protocol::read_conf3_setpoint_limit(conf3.data(), conf3.size(), 10).value());
    assert_float_eq(data.r11_max_heating_setpoint.value(),
                    protocol::read_conf3_setpoint_limit(conf3.data(), conf3.size(), 11).value());
}

void test_passive_shape_contracts() {
    const ShortPacket cond2b = {0xD2, 0x1B, 0x1D, 0x28, 0x15, 0x0D, 0xA0, 0xEA, 0x0C};
    const ShortPacket condd = {0xDD, 0x1D, 0x1D, 0x19, 0x11, 0x1E, 0x00, 0x00, 0x82};
    const Packet conf6 = {
        0x86, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x37};
    const Packet clock = {
        0xCF, 0xB1, 0x00, 0x00, 0x15, 0x03, 0x05, 0x11, 0x06, 0x00, 0x00, 0xB4};

    assert(make_frame(cond2b, hwp::SOURCE_HEATER).is_short_frame());
    assert(make_frame(condd, hwp::SOURCE_HEATER).is_short_frame());
    assert(make_frame(conf6, hwp::SOURCE_HEATER).is_long_frame());
    assert(make_frame(clock, hwp::SOURCE_CONTROLLER).is_long_frame());

    auto clock_frame = stage_frame<hwp::FrameClock>(clock, hwp::SOURCE_CONTROLLER);
    hwp::heat_pump_data_t clock_data;
    clock_frame.parse(clock_data);
    assert(clock_data.time.has_value());

    auto conf6_frame = stage_frame<hwp::FrameConf6>(conf6, hwp::SOURCE_HEATER);
    hwp::heat_pump_data_t conf6_data;
    conf6_frame.parse(conf6_data);
}

int main() {
    test_frame_matching_contracts();
    test_passive_frame_matching_contracts();
    test_conf2_parse_matches_protocol_core();
    test_conf4_parse_matches_protocol_core();
    test_conf5_parse_matches_protocol_core();
    test_conf1_source_gated_parse_matches_protocol_core();
    test_conf1_extended_setpoint_runtime_contract();
    test_condition_parse_matches_protocol_core();
    test_conf3_parse_matches_protocol_core();
    test_passive_shape_contracts();
}
