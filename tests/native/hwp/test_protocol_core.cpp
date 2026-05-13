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
#include "protocol_core.h"

#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <string>

namespace protocol = esphome::hwp::protocol;

template <size_t N>
void assert_packet_eq(const std::array<uint8_t, N>& actual, const std::array<uint8_t, N>& expected) {
    for (size_t i = 0; i < N; ++i) {
        assert(actual[i] == expected[i]);
    }
}

void assert_float_eq(float actual, float expected) {
    assert(std::fabs(actual - expected) < 0.01f);
}

void test_invert_bytes() {
    std::array<uint8_t, 3> data = {0x00, 0xAA, 0x55};

    protocol::invert_bytes(data.data(), data.size(), 2);

    assert(data[0] == 0xFF);
    assert(data[1] == 0x55);
    assert(data[2] == 0x55);
}

void test_short_checksum() {
    std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT> data = {
        0x81, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x00};

    const uint8_t expected = 0x1C;
    assert(protocol::calculate_short_checksum(data.data(), data.size()) == expected);

    data[protocol::packet_checksum_position(data.size())] = expected;
    assert(protocol::is_packet_checksum_valid(data.data(), data.size()));
}

void test_long_checksum() {
    std::array<uint8_t, protocol::FRAME_DATA_LENGTH> data = {
        0x82, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x00};

    const uint8_t expected = 0xB9;
    assert(protocol::calculate_long_checksum(data.data(), data.size()) == expected);

    data[protocol::packet_checksum_position(data.size())] = expected;
    assert(protocol::is_packet_checksum_valid(data.data(), data.size()));
}

void test_invalid_checksum_lengths() {
    std::array<uint8_t, 8> data = {0x81, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00};

    assert(!protocol::is_supported_packet_length(data.size()));
    assert(!protocol::is_packet_checksum_valid(data.data(), data.size()));
    assert(!protocol::is_packet_checksum_valid(nullptr, protocol::FRAME_DATA_LENGTH));
    assert(protocol::packet_checksum_position(0) == 0);
    assert(protocol::calculate_short_checksum(data.data(), 0) == 0);
    assert(protocol::calculate_long_checksum(data.data(), 1) == 0);
}

void test_defrost_eco_conversion() {
    assert(protocol::defrost_eco_raw_from_string("Eco") == protocol::DEFROST_ECO);
    assert(protocol::defrost_eco_raw_from_string("Normal") == protocol::DEFROST_NORMAL);
    assert(protocol::defrost_eco_raw_from_string("unexpected") == protocol::DEFROST_NORMAL);
    assert(std::string(protocol::defrost_eco_to_string(protocol::DEFROST_ECO)) == "Eco");
    assert(std::string(protocol::defrost_eco_to_string(protocol::DEFROST_NORMAL)) == "Normal");
    assert(protocol::defrost_eco_raw_from_bool(true) == protocol::DEFROST_ECO);
    assert(protocol::defrost_eco_raw_from_bool(false) == protocol::DEFROST_NORMAL);
}

void test_flow_meter_conversion() {
    assert(protocol::flow_meter_raw_from_string("Enabled") == protocol::FLOW_METER_ENABLED);
    assert(protocol::flow_meter_raw_from_string("Disabled") == protocol::FLOW_METER_DISABLED);
    assert(protocol::flow_meter_raw_from_string("unexpected") == protocol::FLOW_METER_DISABLED);
    assert(std::string(protocol::flow_meter_to_string(protocol::FLOW_METER_ENABLED)) == "Enabled");
    assert(std::string(protocol::flow_meter_to_string(protocol::FLOW_METER_DISABLED)) == "Disabled");
    assert(protocol::flow_meter_raw_from_bool(true) == protocol::FLOW_METER_ENABLED);
    assert(protocol::flow_meter_raw_from_bool(false) == protocol::FLOW_METER_DISABLED);
}

void test_fan_speed_control_temp_conversion() {
    assert(protocol::fan_speed_control_temp_raw_from_string("Coil Temperature") ==
           protocol::FAN_SPEED_CONTROL_COIL);
    assert(protocol::fan_speed_control_temp_raw_from_string("Ambient Temperature") ==
           protocol::FAN_SPEED_CONTROL_AMBIENT);
    assert(protocol::fan_speed_control_temp_raw_from_string("unexpected") ==
           protocol::FAN_SPEED_CONTROL_COIL);
    assert(std::string(protocol::fan_speed_control_temp_to_string(
               protocol::FAN_SPEED_CONTROL_COIL)) == "Coil Temperature");
    assert(std::string(protocol::fan_speed_control_temp_to_string(
               protocol::FAN_SPEED_CONTROL_AMBIENT)) == "Ambient Temperature");
    assert(protocol::fan_speed_control_temp_raw_from_bool(false) ==
           protocol::FAN_SPEED_CONTROL_COIL);
    assert(protocol::fan_speed_control_temp_raw_from_bool(true) ==
           protocol::FAN_SPEED_CONTROL_AMBIENT);
}

void test_speed_control_module_conversion() {
    assert(protocol::speed_control_module_raw_from_string("Enabled") ==
           protocol::SPEED_CONTROL_MODULE_ENABLED);
    assert(protocol::speed_control_module_raw_from_string("Disabled") ==
           protocol::SPEED_CONTROL_MODULE_DISABLED);
    assert(protocol::speed_control_module_raw_from_string("unexpected") ==
           protocol::SPEED_CONTROL_MODULE_ENABLED);
    assert(std::string(protocol::speed_control_module_to_string(
               protocol::SPEED_CONTROL_MODULE_ENABLED)) == "Enabled");
    assert(std::string(protocol::speed_control_module_to_string(
               protocol::SPEED_CONTROL_MODULE_DISABLED)) == "Disabled");
    assert(protocol::speed_control_module_raw_from_bool(true) ==
           protocol::SPEED_CONTROL_MODULE_ENABLED);
    assert(protocol::speed_control_module_raw_from_bool(false) ==
           protocol::SPEED_CONTROL_MODULE_DISABLED);
}

void test_heat_pump_restrict_conversion() {
    assert(protocol::heat_pump_restrict_raw_from_string("Cooling Only") ==
           protocol::HEAT_PUMP_COOLING_ONLY);
    assert(protocol::heat_pump_restrict_raw_from_string("Any Mode") ==
           protocol::HEAT_PUMP_ANY_MODE);
    assert(protocol::heat_pump_restrict_raw_from_string("Heating Only") ==
           protocol::HEAT_PUMP_HEATING_ONLY);
    assert(protocol::heat_pump_restrict_raw_from_string("unexpected") ==
           protocol::HEAT_PUMP_ANY_MODE);
    assert(std::string(protocol::heat_pump_restrict_to_string(
               protocol::HEAT_PUMP_COOLING_ONLY)) == "Cooling Only");
    assert(std::string(protocol::heat_pump_restrict_to_string(protocol::HEAT_PUMP_ANY_MODE)) ==
           "Any Mode");
    assert(std::string(protocol::heat_pump_restrict_to_string(
               protocol::HEAT_PUMP_HEATING_ONLY)) == "Heating Only");
}

void test_fan_mode_raw_conversion() {
    assert(protocol::normalize_fan_mode_raw(0x00) == protocol::FAN_MODE_LOW_SPEED);
    assert(protocol::normalize_fan_mode_raw(0x01) == protocol::FAN_MODE_HIGH_SPEED);
    assert(protocol::normalize_fan_mode_raw(0x02) == protocol::FAN_MODE_AMBIENT);
    assert(protocol::normalize_fan_mode_raw(0x03) == protocol::FAN_MODE_SCHEDULED);
    assert(protocol::normalize_fan_mode_raw(0x04) == protocol::FAN_MODE_AMBIENT_SCHEDULED);
    assert(protocol::normalize_fan_mode_raw(0x05) == protocol::FAN_MODE_LOW_SPEED);
    assert(protocol::normalize_fan_mode_raw(protocol::FAN_MODE_UNKNOWN) ==
           protocol::FAN_MODE_LOW_SPEED);
}

void test_fan_mode_strings() {
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_LOW_SPEED)) ==
           "Low Speed");
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_HIGH_SPEED)) ==
           "High Speed");
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_AMBIENT)) ==
           "Ambient");
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_SCHEDULED)) ==
           "Scheduled");
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_AMBIENT_SCHEDULED)) ==
           "Scheduled Ambient");
    assert(std::string(protocol::fan_mode_to_string(protocol::FAN_MODE_UNKNOWN)) ==
           "Unknown");

    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_LOW_SPEED)) ==
           "LOW   ");
    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_HIGH_SPEED)) ==
           "HIGH  ");
    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_AMBIENT)) ==
           "AMBI  ");
    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_SCHEDULED)) ==
           "TIME  ");
    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_AMBIENT_SCHEDULED)) ==
           "AMBTME");
    assert(std::string(protocol::fan_mode_log_format(protocol::FAN_MODE_UNKNOWN)) == "UNK ");
}

void test_fan_mode_custom_strings() {
    assert(!protocol::is_custom_fan_mode(protocol::FAN_MODE_LOW_SPEED));
    assert(!protocol::is_custom_fan_mode(protocol::FAN_MODE_HIGH_SPEED));
    assert(protocol::is_custom_fan_mode(protocol::FAN_MODE_AMBIENT));
    assert(protocol::is_custom_fan_mode(protocol::FAN_MODE_SCHEDULED));
    assert(protocol::is_custom_fan_mode(protocol::FAN_MODE_AMBIENT_SCHEDULED));

    assert(protocol::fan_mode_custom_string(protocol::FAN_MODE_LOW_SPEED) == nullptr);
    assert(protocol::fan_mode_custom_string(protocol::FAN_MODE_HIGH_SPEED) == nullptr);
    assert(std::string(protocol::fan_mode_custom_string(protocol::FAN_MODE_AMBIENT)) ==
           "Ambient");
    assert(std::string(protocol::fan_mode_custom_string(protocol::FAN_MODE_SCHEDULED)) ==
           "Scheduled");
    assert(std::string(protocol::fan_mode_custom_string(protocol::FAN_MODE_AMBIENT_SCHEDULED)) ==
           "Scheduled Ambient");

    assert(protocol::fan_mode_raw_from_custom_string("Ambient").value() ==
           protocol::FAN_MODE_AMBIENT);
    assert(protocol::fan_mode_raw_from_custom_string("Scheduled").value() ==
           protocol::FAN_MODE_SCHEDULED);
    assert(protocol::fan_mode_raw_from_custom_string("Scheduled Ambient").value() ==
           protocol::FAN_MODE_AMBIENT_SCHEDULED);
    assert(!protocol::fan_mode_raw_from_custom_string("Low Speed").has_value());
    assert(!protocol::fan_mode_raw_from_custom_string("High Speed").has_value());
    assert(!protocol::fan_mode_raw_from_custom_string("unexpected").has_value());
}

void test_fan_fixture_read_helpers() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f01 = {
        0x82, 0xB1, 0x46, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xDF};
    assert(protocol::read_conf2_f01_fan_mode(f01.data(), f01.size()).value() ==
           protocol::FAN_MODE_AMBIENT_SCHEDULED);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f10 = {
        0x82, 0xB1, 0x3E, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xD7};
    assert(protocol::read_conf2_f10_fan_speed_control_temp(f10.data(), f10.size()).value() ==
           protocol::FAN_SPEED_CONTROL_AMBIENT);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f13 = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x32, 0x9D};
    assert_float_eq(protocol::read_conf2_f13_max_fan_voltage_pct(f13.data(), f13.size()).value(),
                    50.0f);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f02 = {
        0x84, 0xB1, 0x8F, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x12};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f03 = {
        0x84, 0xB1, 0x8C, 0x64, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x19};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f03_edge = {
        0x84, 0xB1, 0x8C, 0x5B, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f04 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x51, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f05 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x51, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f06 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x65, 0x78, 0x00, 0x00, 0x78, 0x10};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f07 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x7B, 0x00, 0x00, 0x78, 0x12};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f08 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x17, 0x00, 0x78, 0x26};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f08_edge = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x01, 0x00, 0x78, 0x10};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f09 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x10, 0x78, 0x1F};
    assert_float_eq(protocol::read_conf4_fan_parameter(f02.data(), f02.size(), 2).value(), 41.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f03.data(), f03.size(), 3).value(), 20.0f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f03_edge.data(), f03_edge.size(), 3).value(), 15.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f04.data(), f04.size(), 4).value(), 10.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f05.data(), f05.size(), 5).value(), 10.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f06.data(), f06.size(), 6).value(), 20.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f07.data(), f07.size(), 7).value(), 31.5f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f08.data(), f08.size(), 8).value(), 23.0f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f08_edge.data(), f08_edge.size(), 8).value(), 1.0f);
    assert_float_eq(protocol::read_conf4_fan_parameter(f09.data(), f09.size(), 9).value(), 16.0f);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f11 = {
        0x85, 0xB1, 0x08, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x4D};
    assert(protocol::read_conf5_f11_speed_control_module(f11.data(), f11.size()).value() ==
           protocol::SPEED_CONTROL_MODULE_DISABLED);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d06_eco = {
        0x85, 0xB1, 0x40, 0x06, 0x4A, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0xB1};
    assert(protocol::read_conf5_d06_defrost_eco_mode(d06_eco.data(), d06_eco.size()).value() ==
           protocol::DEFROST_ECO);
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d06_normal = {
        0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
    assert(protocol::read_conf5_d06_defrost_eco_mode(
               d06_normal.data(), d06_normal.size()).value() == protocol::DEFROST_NORMAL);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f12 = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x37, 0xA3};
    assert_float_eq(protocol::read_conf1_f12_min_fan_voltage_pct(f12.data(), f12.size()).value(),
                    55.0f);
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f12_edge = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0x9E};
    assert_float_eq(protocol::read_conf1_f12_min_fan_voltage_pct(
                        f12_edge.data(), f12_edge.size()).value(), 50.0f);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f10_coil = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xCF};
    assert(protocol::read_conf2_f10_fan_speed_control_temp(
               f10_coil.data(), f10_coil.size()).value() == protocol::FAN_SPEED_CONTROL_COIL);
    assert_float_eq(protocol::read_conf2_f13_max_fan_voltage_pct(
                        f10_coil.data(), f10_coil.size()).value(), 100.0f);
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f13_99 = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x63, 0xCE};
    assert_float_eq(protocol::read_conf2_f13_max_fan_voltage_pct(
                        f13_99.data(), f13_99.size()).value(), 99.0f);

    assert(!protocol::read_conf1_f12_min_fan_voltage_pct(f11.data(), f11.size()).has_value());
    assert(!protocol::read_conf5_d06_defrost_eco_mode(f12.data(), f12.size()).has_value());
    assert(!protocol::read_conf4_fan_parameter(f02.data(), protocol::FRAME_DATA_LENGTH_SHORT, 2)
                .has_value());
    assert(!protocol::read_conf4_fan_parameter(f02.data(), f02.size(), 10).has_value());
}

void test_fan_command_byte_helpers() {
    std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf1 = {
        0x81, 0xB1, 0x06, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0x8A};
    assert(protocol::set_conf1_f12_min_fan_voltage_pct(conf1.data(), conf1.size(), 45.0f));
    assert(conf1[10] == 0x2D);
    assert(protocol::is_packet_checksum_valid(conf1.data(), conf1.size()));

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf2 = {
        0x82, 0xB1, 0x16, 0x2E, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xB3};
    assert(protocol::set_conf2_f10_fan_speed_control_temp(
        conf2.data(), conf2.size(), protocol::FAN_SPEED_CONTROL_AMBIENT));
    assert(conf2[2] == 0x1E);
    assert(protocol::is_packet_checksum_valid(conf2.data(), conf2.size()));
    assert(protocol::set_conf2_f13_max_fan_voltage_pct(conf2.data(), conf2.size(), 85.0f));
    assert(conf2[10] == 0x55);
    assert(protocol::is_packet_checksum_valid(conf2.data(), conf2.size()));

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf4 = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x0F};
    assert(protocol::set_conf4_fan_parameter(conf4.data(), conf4.size(), 2, 42.5f));
    assert(conf4[2] == 0x91);
    assert(protocol::set_conf4_fan_parameter(conf4.data(), conf4.size(), 8, 12.0f));
    assert(conf4[8] == 0x0C);
    assert(protocol::is_packet_checksum_valid(conf4.data(), conf4.size()));

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf5 = {
        0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
    assert(protocol::set_conf5_f11_speed_control_module(
        conf5.data(), conf5.size(), protocol::SPEED_CONTROL_MODULE_DISABLED));
    assert(conf5[2] == 0x08);
    assert(protocol::is_packet_checksum_valid(conf5.data(), conf5.size()));
    assert(protocol::set_conf5_d06_defrost_eco_mode(
        conf5.data(), conf5.size(), protocol::DEFROST_ECO));
    assert(conf5[2] == 0x48);
    assert(protocol::is_packet_checksum_valid(conf5.data(), conf5.size()));

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT> short_frame = {
        0x81, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x1C};
    assert(!protocol::set_conf2_f13_max_fan_voltage_pct(
        short_frame.data(), short_frame.size(), 90.0f));
    assert(!protocol::set_conf5_d06_defrost_eco_mode(
        short_frame.data(), short_frame.size(), protocol::DEFROST_NORMAL));
    assert(!protocol::set_conf4_fan_parameter(conf4.data(), conf4.size(), 10, 1.0f));
}

void test_config1_config3_demo_read_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> h02 = {
        0x81, 0xB1, 0x26, 0x6D, 0x58, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xA7};
    assert(protocol::read_conf1_h02_mode_restriction(h02.data(), h02.size()).value() ==
           protocol::HEAT_PUMP_ANY_MODE);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r01 = {
        0x81, 0xB1, 0x26, 0x71, 0x58, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xAB};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r02 = {
        0x81, 0xB1, 0x26, 0x6E, 0x56, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xA6};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r03 = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xAD};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r04 = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3F, 0x3D, 0x3D, 0x3D, 0x32, 0xAF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r05 = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x43, 0x3D, 0x3D, 0x32, 0xB3};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r06 = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x45, 0x3D, 0x32, 0xB5};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r07 = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x3D, 0x41, 0x32, 0xB1};

    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r01.data(), r01.size(), 1).value(), 26.5f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r02.data(), r02.size(), 2).value(), 13.0f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r03.data(), r03.size(), 3).value(), 22.0f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r04.data(), r04.size(), 4).value(), 1.5f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r05.data(), r05.size(), 5).value(), 3.5f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r06.data(), r06.size(), 6).value(), 4.5f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r07.data(), r07.size(), 7).value(), 2.5f);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r09 = {
        0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x3C, 0x84, 0x46, 0x8C, 0x7F};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r10 = {
        0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x3C, 0x82, 0x4B, 0x8C, 0x82};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r11 = {
        0x83, 0xB1, 0x46, 0x23, 0x0A, 0x23, 0x23, 0x3C, 0x82, 0x46, 0x89, 0x7A};
    assert_float_eq(protocol::read_conf3_setpoint_limit(r09.data(), r09.size(), 9).value(), 36.0f);
    assert_float_eq(protocol::read_conf3_setpoint_limit(r10.data(), r10.size(), 10).value(), 7.5f);
    assert_float_eq(protocol::read_conf3_setpoint_limit(r11.data(), r11.size(), 11).value(), 38.5f);

    assert(!protocol::read_conf1_temperature_parameter(r09.data(), r09.size(), 1).has_value());
    assert(!protocol::read_conf1_temperature_parameter(r01.data(), r01.size(), 8).has_value());
    assert(!protocol::read_conf3_setpoint_limit(r01.data(), r01.size(), 9).has_value());
}

void test_cond2_demo_temperature_read_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> temp_out_1 = {
        0xD2, 0xB1, 0x11, 0x5E, 0x52, 0x4C, 0x4E, 0x00, 0x64, 0x00, 0x00, 0x42};

    assert_float_eq(
        protocol::read_cond2_temperature(temp_out_1.data(), temp_out_1.size(), 3).value(),
        11.0f);
    assert_float_eq(
        protocol::read_cond2_temperature(temp_out_1.data(), temp_out_1.size(), 4).value(),
        9.0f);
    assert_float_eq(
        protocol::read_cond2_temperature(temp_out_1.data(), temp_out_1.size(), 6).value(),
        8.0f);
    assert_float_eq(
        protocol::read_cond2_temperature(temp_out_1.data(), temp_out_1.size(), 8).value(),
        20.0f);
    assert(protocol::is_packet_checksum_valid(temp_out_1.data(), temp_out_1.size()));
    assert(!protocol::read_cond2_temperature(temp_out_1.data(), temp_out_1.size(), 7)
                .has_value());

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT> short_frame = {
        0xD2, 0x1B, 0x06, 0x28, 0x07, 0x0D, 0xA0, 0x8C, 0x89};
    assert(!protocol::read_cond2_temperature(short_frame.data(), short_frame.size(), 3)
                .has_value());
}

void test_config1_extended_setpoint_regression_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r02_33_5 = {
        0x81, 0xB1, 0x26, 0x6E, 0x7F, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xCF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r02_34_0 = {
        0x81, 0xB1, 0x26, 0x6E, 0x80, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xD0};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r02_35_0 = {
        0x81, 0xB1, 0x26, 0x6E, 0x82, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xD2};

    assert(protocol::encode_temperature_extended(33.5f) == 0x7F);
    assert(protocol::encode_temperature_extended(34.0f) == 0x80);
    assert(protocol::encode_temperature_extended(35.0f) == 0x82);
    assert(protocol::encode_temperature(35.0f) != 0x82);

    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r02_33_5.data(), r02_33_5.size(), 2).value(),
        33.5f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r02_34_0.data(), r02_34_0.size(), 2).value(),
        34.0f);
    assert_float_eq(
        protocol::read_conf1_temperature_parameter(r02_35_0.data(), r02_35_0.size(), 2).value(),
        35.0f);

    auto conf1 = r02_33_5;
    assert(protocol::set_conf1_temperature_parameter(conf1.data(), conf1.size(), 2, 34.0f));
    assert_packet_eq(conf1, r02_34_0);
    assert(protocol::is_packet_checksum_valid(conf1.data(), conf1.size()));

    assert(protocol::set_conf1_temperature_parameter(conf1.data(), conf1.size(), 2, 35.0f));
    assert_packet_eq(conf1, r02_35_0);
    assert(protocol::is_packet_checksum_valid(conf1.data(), conf1.size()));
    assert(conf1[4] != 0x42);
}

void test_config1_demo_write_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r01_base = {
        0x81, 0xB1, 0x26, 0x6E, 0x58, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xA8};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r01_expected = {
        0x81, 0xB1, 0x26, 0x71, 0x58, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xAB};
    auto conf1 = r01_base;
    assert(protocol::set_conf1_temperature_parameter(conf1.data(), conf1.size(), 1, 26.5f));
    assert_packet_eq(conf1, r01_expected);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r02_expected = {
        0x81, 0xB1, 0x26, 0x6E, 0x56, 0x64, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xA6};
    conf1 = r01_base;
    assert(protocol::set_conf1_temperature_parameter(conf1.data(), conf1.size(), 2, 13.0f));
    assert_packet_eq(conf1, r02_expected);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> common_base = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0xAD};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r04_expected = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3F, 0x3D, 0x3D, 0x3D, 0x32, 0xAF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r05_expected = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x43, 0x3D, 0x3D, 0x32, 0xB3};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r06_expected = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x45, 0x3D, 0x32, 0xB5};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> r07_expected = {
        0x81, 0xB1, 0x26, 0x6E, 0x59, 0x68, 0x3D, 0x3D, 0x3D, 0x41, 0x32, 0xB1};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> expected[] = {
        r04_expected, r05_expected, r06_expected, r07_expected};
    const float values[] = {1.5f, 3.5f, 4.5f, 2.5f};
    for (uint8_t field = 4; field <= 7; ++field) {
        conf1 = common_base;
        assert(protocol::set_conf1_temperature_parameter(
            conf1.data(), conf1.size(), field, values[field - 4]));
        assert_packet_eq(conf1, expected[field - 4]);
        assert(protocol::is_packet_checksum_valid(conf1.data(), conf1.size()));
    }

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT> short_frame = {
        0x81, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x1C};
    assert(!protocol::set_conf1_temperature_parameter(
        short_frame.data(), short_frame.size(), 1, 26.5f));
    assert(!protocol::set_conf1_temperature_parameter(conf1.data(), conf1.size(), 8, 1.0f));
}

void test_fan_fixture_write_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf1_base = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0x9E};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f12_expected = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x37, 0xA3};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f12_50_expected = {
        0x81, 0xB1, 0x1A, 0x72, 0x48, 0x72, 0x3D, 0x3D, 0x3D, 0x3D, 0x32, 0x9E};
    auto conf1 = conf1_base;
    assert(protocol::set_conf1_f12_min_fan_voltage_pct(conf1.data(), conf1.size(), 55.0f));
    assert_packet_eq(conf1, f12_expected);
    assert(protocol::is_packet_checksum_valid(conf1.data(), conf1.size()));
    assert(protocol::set_conf1_f12_min_fan_voltage_pct(conf1.data(), conf1.size(), 50.0f));
    assert_packet_eq(conf1, f12_50_expected);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf2_base = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xCF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f01_expected = {
        0x82, 0xB1, 0x46, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xDF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f10_expected = {
        0x82, 0xB1, 0x3E, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xD7};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f10_coil_expected = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xCF};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f13_expected = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x32, 0x9D};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f13_99_expected = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x63, 0xCE};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f13_100_expected = {
        0x82, 0xB1, 0x36, 0x2A, 0x56, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xCF};
    auto conf2 = conf2_base;
    assert(protocol::set_conf2_f01_fan_mode(
        conf2.data(), conf2.size(), protocol::FAN_MODE_AMBIENT_SCHEDULED));
    assert_packet_eq(conf2, f01_expected);
    conf2 = conf2_base;
    assert(protocol::set_conf2_f10_fan_speed_control_temp(
        conf2.data(), conf2.size(), protocol::FAN_SPEED_CONTROL_AMBIENT));
    assert_packet_eq(conf2, f10_expected);
    assert(protocol::set_conf2_f10_fan_speed_control_temp(
        conf2.data(), conf2.size(), protocol::FAN_SPEED_CONTROL_COIL));
    assert_packet_eq(conf2, f10_coil_expected);
    conf2 = conf2_base;
    assert(protocol::set_conf2_f13_max_fan_voltage_pct(conf2.data(), conf2.size(), 50.0f));
    assert_packet_eq(conf2, f13_expected);
    assert(protocol::set_conf2_f13_max_fan_voltage_pct(conf2.data(), conf2.size(), 99.0f));
    assert_packet_eq(conf2, f13_99_expected);
    assert(protocol::set_conf2_f13_max_fan_voltage_pct(conf2.data(), conf2.size(), 100.0f));
    assert_packet_eq(conf2, f13_100_expected);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf4_base = {
        0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x0F};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf4_expected[] = {
        {0x84, 0xB1, 0x8F, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x12},
        {0x84, 0xB1, 0x8C, 0x64, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x19},
        {0x84, 0xB1, 0x8C, 0x5A, 0x51, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x51, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x65, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x7B, 0x00, 0x00, 0x78, 0x12},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x17, 0x00, 0x78, 0x26},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x10, 0x78, 0x1F},
    };
    const float conf4_values[] = {41.5f, 20.0f, 10.5f, 10.5f, 20.5f, 31.5f, 23.0f, 16.0f};
    for (uint8_t field = 2; field <= 9; ++field) {
        auto conf4 = conf4_base;
        assert(protocol::set_conf4_fan_parameter(
            conf4.data(), conf4.size(), field, conf4_values[field - 2]));
        assert_packet_eq(conf4, conf4_expected[field - 2]);
        assert(protocol::is_packet_checksum_valid(conf4.data(), conf4.size()));
    }

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf4_edge_expected[] = {
        {0x84, 0xB1, 0x8E, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x11},
        {0x84, 0xB1, 0x8C, 0x5B, 0x50, 0x50, 0x64, 0x78, 0x00, 0x00, 0x78, 0x10},
        {0x84, 0xB1, 0x8C, 0x5A, 0x50, 0x50, 0x64, 0x78, 0x01, 0x00, 0x78, 0x10},
    };
    const uint8_t conf4_edge_fields[] = {2, 3, 8};
    const float conf4_edge_values[] = {41.0f, 15.5f, 1.0f};
    for (size_t i = 0; i < 3; ++i) {
        auto conf4 = conf4_base;
        assert(protocol::set_conf4_fan_parameter(
            conf4.data(), conf4.size(), conf4_edge_fields[i], conf4_edge_values[i]));
        assert_packet_eq(conf4, conf4_edge_expected[i]);
    }

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> conf5_base = {
        0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> f11_expected = {
        0x85, 0xB1, 0x08, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x4D};
    auto conf5 = conf5_base;
    assert(protocol::set_conf5_f11_speed_control_module(
        conf5.data(), conf5.size(), protocol::SPEED_CONTROL_MODULE_DISABLED));
    assert_packet_eq(conf5, f11_expected);
    assert(protocol::is_packet_checksum_valid(conf5.data(), conf5.size()));
}

void test_config5_defrost_active_tx_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> normal_echo = {
        0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> eco_command = {
        0x85, 0xB1, 0x40, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x85};
    auto conf5 = normal_echo;
    assert(protocol::set_conf5_d06_defrost_eco_mode(
        conf5.data(), conf5.size(), protocol::DEFROST_ECO));
    assert_packet_eq(conf5, eco_command);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> eco_echo = {
        0x85, 0xB1, 0x40, 0x06, 0x4A, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0xB1};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> normal_command = {
        0x85, 0xB1, 0x00, 0x06, 0x4A, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x71};
    conf5 = eco_echo;
    assert(protocol::set_conf5_d06_defrost_eco_mode(
        conf5.data(), conf5.size(), protocol::DEFROST_NORMAL));
    assert_packet_eq(conf5, normal_command);

    assert(protocol::read_conf5_d06_defrost_eco_mode(
               eco_echo.data(), eco_echo.size()).value() == protocol::DEFROST_ECO);
    assert(protocol::read_conf5_d06_defrost_eco_mode(
               normal_echo.data(), normal_echo.size()).value() == protocol::DEFROST_NORMAL);
    assert(protocol::is_packet_checksum_valid(eco_command.data(), eco_command.size()));
    assert(protocol::is_packet_checksum_valid(normal_command.data(), normal_command.size()));
}

void test_defrost_demo_command_contracts() {
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d01_neg_7_0 = {
        0x82, 0xB1, 0x16, 0x2E, 0x58, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xB5};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d01_neg_7_5 = {
        0x82, 0xB1, 0x16, 0x2D, 0x58, 0x50, 0x10, 0x1E, 0x03, 0x01, 0x64, 0xB4};

    assert_float_eq(
        protocol::read_conf2_d01_defrost_start(d01_neg_7_0.data(), d01_neg_7_0.size()).value(),
        -7.0f);
    assert_float_eq(
        protocol::read_conf2_d01_defrost_start(d01_neg_7_5.data(), d01_neg_7_5.size()).value(),
        -7.5f);
    auto conf2 = d01_neg_7_0;
    assert(protocol::set_conf2_d01_defrost_start(conf2.data(), conf2.size(), -7.5f));
    assert_packet_eq(conf2, d01_neg_7_5);
    assert(protocol::is_packet_checksum_valid(conf2.data(), conf2.size()));

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d05_3_0 = {
        0x85, 0xB1, 0x00, 0x06, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x45};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d05_4_0 = {
        0x85, 0xB1, 0x00, 0x08, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x47};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d05_5_0 = {
        0x85, 0xB1, 0x00, 0x0A, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x49};
    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d05_10_0 = {
        0x85, 0xB1, 0x00, 0x14, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x53};

    assert(protocol::encode_decimal_number(10.0f) == 0x14);
    assert_float_eq(protocol::decode_decimal_number(0x0A), 5.0f);
    assert_float_eq(protocol::read_conf5_d05_min_economy_defrost_time_minutes(
                        d05_3_0.data(), d05_3_0.size()).value(), 3.0f);
    assert_float_eq(protocol::read_conf5_d05_min_economy_defrost_time_minutes(
                        d05_4_0.data(), d05_4_0.size()).value(), 4.0f);
    assert_float_eq(protocol::read_conf5_d05_min_economy_defrost_time_minutes(
                        d05_5_0.data(), d05_5_0.size()).value(), 5.0f);
    assert_float_eq(protocol::read_conf5_d05_min_economy_defrost_time_minutes(
                        d05_10_0.data(), d05_10_0.size()).value(), 10.0f);

    auto conf5 = d05_3_0;
    assert(protocol::set_conf5_d05_min_economy_defrost_time_minutes(
        conf5.data(), conf5.size(), 10.0f));
    assert_packet_eq(conf5, d05_10_0);
    assert(protocol::set_conf5_d05_min_economy_defrost_time_minutes(
        conf5.data(), conf5.size(), 4.0f));
    assert_packet_eq(conf5, d05_4_0);
    assert(protocol::set_conf5_d05_min_economy_defrost_time_minutes(
        conf5.data(), conf5.size(), 5.0f));
    assert_packet_eq(conf5, d05_5_0);

    const std::array<uint8_t, protocol::FRAME_DATA_LENGTH> d05_5_0_d06_eco = {
        0x85, 0xB1, 0x40, 0x0A, 0x1E, 0x16, 0x00, 0x08, 0x00, 0x00, 0xCD, 0x89};
    conf5 = d05_5_0;
    assert(protocol::set_conf5_d06_defrost_eco_mode(
        conf5.data(), conf5.size(), protocol::DEFROST_ECO));
    assert_packet_eq(conf5, d05_5_0_d06_eco);
    assert(protocol::read_conf5_d06_defrost_eco_mode(
               d05_5_0_d06_eco.data(), d05_5_0_d06_eco.size()).value() ==
           protocol::DEFROST_ECO);

    std::array<uint8_t, protocol::FRAME_DATA_LENGTH_SHORT> short_frame = {
        0x82, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x1C};
    assert(!protocol::read_conf2_d01_defrost_start(
                short_frame.data(), short_frame.size()).has_value());
    assert(!protocol::read_conf5_d05_min_economy_defrost_time_minutes(
                short_frame.data(), short_frame.size()).has_value());
    assert(!protocol::set_conf2_d01_defrost_start(
        short_frame.data(), short_frame.size(), -7.5f));
    assert(!protocol::set_conf5_d05_min_economy_defrost_time_minutes(
        short_frame.data(), short_frame.size(), 5.0f));
}

int main() {
    test_invert_bytes();
    test_short_checksum();
    test_long_checksum();
    test_invalid_checksum_lengths();
    test_defrost_eco_conversion();
    test_flow_meter_conversion();
    test_fan_speed_control_temp_conversion();
    test_speed_control_module_conversion();
    test_heat_pump_restrict_conversion();
    test_fan_mode_raw_conversion();
    test_fan_mode_strings();
    test_fan_mode_custom_strings();
    test_fan_fixture_read_helpers();
    test_fan_command_byte_helpers();
    test_config1_config3_demo_read_contracts();
    test_cond2_demo_temperature_read_contracts();
    test_config1_extended_setpoint_regression_contracts();
    test_config1_demo_write_contracts();
    test_fan_fixture_write_contracts();
    test_config5_defrost_active_tx_contracts();
    test_defrost_demo_command_contracts();
}
