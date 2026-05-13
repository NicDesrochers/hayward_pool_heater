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

#include "CS.h"
#include "Schema.h"
#include "base_frame.h"
namespace esphome {
namespace hwp {
/**
 * @brief Fan configuration menu packet.
 *
 * Maps technical-menu options F02-F09 onto CONFIG_4 payload bytes.
 */
typedef struct conf_4 {
    uint8_t id;                                      ///< ID byte
    temperature_extended_t f02_fan_high_speed_cool_setpoint; // F02
    temperature_extended_t f03_fan_low_speed_temp_in_cooling_set_point; // F03
    temperature_extended_t f04_fan_stop_temp_in_cooling_set_point; // F04
    temperature_extended_t f05_fan_high_speed_temp_in_heating_set_point; // F05
    temperature_extended_t f06_fan_low_speed_temp_in_heating_set_point; // F06
    temperature_extended_t f07_fan_stop_temp_in_heating_set_point; // F07
    small_integer_t f08_fan_low_speed_running_time; // F08
    small_integer_t f09_fan_stop_low_speed_running_time; // F09
    bits_details_t unknown;
    
    bool operator==(const optional<struct conf_4>& other) const {
        return other.has_value() && *this == *other;
    }
    bool operator==(const struct conf_4& other) const {
        return id == other.id &&
               f02_fan_high_speed_cool_setpoint == other.f02_fan_high_speed_cool_setpoint &&
               f03_fan_low_speed_temp_in_cooling_set_point ==
                   other.f03_fan_low_speed_temp_in_cooling_set_point &&
               f04_fan_stop_temp_in_cooling_set_point ==
                   other.f04_fan_stop_temp_in_cooling_set_point &&
               f05_fan_high_speed_temp_in_heating_set_point ==
                   other.f05_fan_high_speed_temp_in_heating_set_point &&
               f06_fan_low_speed_temp_in_heating_set_point ==
                   other.f06_fan_low_speed_temp_in_heating_set_point &&
               f07_fan_stop_temp_in_heating_set_point ==
                   other.f07_fan_stop_temp_in_heating_set_point &&
               f08_fan_low_speed_running_time == other.f08_fan_low_speed_running_time &&
               f09_fan_stop_low_speed_running_time == other.f09_fan_stop_low_speed_running_time &&
               unknown == other.unknown;
    }

    bool operator!=(const struct conf_4& other) const { return !(*this == other); }
    bool operator!=(const optional<struct conf_4>& other) const {
        return !(*this == other);
    }
} __attribute__((packed)) conf_4_t;
static_assert(sizeof(conf_4_t) == frame_data_length - 2, "frame structure has wrong size");

class FrameConf4 : public BaseFrame {
  public:
    CLASS_DEFAULT_IMPL(FrameConf4, conf_4_t);
    static constexpr uint8_t FRAME_ID_CONF_4 = 0x84;
    void traits(climate::ClimateTraits& traits, heat_pump_data_t& hp_data) override;
};

} // namespace hwp
} // namespace esphome
