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
#include "hwp_climate_adapter.h"
namespace esphome {
namespace hwp {

typedef struct fanmode_details {
    union {
        struct {
            uint8_t unknown_x : 3;        // Bits 0-2: Unknown purpose
            uint8_t f10_speed_source : 1; // F10 bit 3: fan speed control temperature source
            uint8_t mode : 4;             // F01 bits 4-7: fan mode
        };
        bits_details_t raw; // Raw byte representation
    };
    FanMode get_fan_mode() const {
        return FanMode(mode);
    }
    FanSpeedControlTempMode get_fan_speed_control_temp_mode() const {
        return FanSpeedControlTempMode(f10_speed_source);
    }
    bool operator==(const optional<struct fanmode_details>& other) const {
        return other.has_value() && raw == other.value().raw;
    }
    bool operator==(const struct fanmode_details& other) const { return raw == other.raw; }
    bool operator!=(const struct fanmode_details& other) const { return raw != other.raw; }
    bool operator!=(const optional<struct fanmode_details>& other) const {
        return *this != other.value();
    }

   
   

} __attribute__((packed)) fanmode_details_t;
static_assert(sizeof(fanmode_details_t) == 1, "Invalid fanmode_details_t size");

/**
 * @brief Represents the fan state, including defrost settings and unknown bits.
 *
 * - F01/F10: Fan mode and fan speed control temperature source.
 * - D01: Defrost start temperature.
 * - D02: Defrost end temperature.
 * - D03: Time duration for the defrost cycle in minutes.
 * - D04: Maximum defrost time in minutes.
 * - F13: Maximum fan voltage limit percent.
 * - unknown_5 to unknown_8: Reserved or unknown fields.
 */
typedef struct conf_2 {
    uint8_t id;                                         ///< ID byte
    fanmode_details_t fan_mode;                         // F01/F10 fan mode/source byte
    temperature_extended_t d01_defrost_start;           // D01 defrost start temperature
    temperature_t d02_defrost_end;                      // D02 defrost end temperature at data[4]
    decimal_number_t d03_defrosting_cycle_time_minutes; // D03 defrost cycle time in minutes
    decimal_number_t d04_max_defrost_time_minutes;      // D04 maximum defrost time in minutes
    bits_details_t unknown_5;                           // Reserved or unknown field (6th byte)
    bits_details_t unknown_6;                           // Reserved or unknown field (7th byte)
    bits_details_t unknown_7;                           // Reserved or unknown field (8th byte)
    small_integer_t f13_max_fan_voltage_pct;            // F13 maximum fan voltage limit percent
    bool operator==(const optional<struct conf_2>& other) const {
        return other.has_value() && *this == *other;
    }

    bool operator==(const struct conf_2& other) const {
        return this->id == other.id && this->fan_mode == other.fan_mode &&
               this->d01_defrost_start == other.d01_defrost_start &&
               this->d02_defrost_end == other.d02_defrost_end &&
               this->d03_defrosting_cycle_time_minutes == other.d03_defrosting_cycle_time_minutes &&
               this->d04_max_defrost_time_minutes == other.d04_max_defrost_time_minutes &&
               this->unknown_5 == other.unknown_5 && this->unknown_6 == other.unknown_6 &&
               this->unknown_7 == other.unknown_7 &&
               this->f13_max_fan_voltage_pct == other.f13_max_fan_voltage_pct;
    }

    bool operator!=(const optional<struct conf_2>& other) const { return !(*this == other); }

    bool operator!=(const struct conf_2& other) const { return !(*this == other); }

} __attribute__((packed)) conf_2_t;
static_assert(sizeof(conf_2_t) == frame_data_length - 2, "frame structure has wrong size");

class FrameConf2 : public BaseFrame {
  public:
    CLASS_DEFAULT_IMPL(FrameConf2, conf_2_t);
    void set_fan_mode(FanMode mode);
    static constexpr uint8_t FRAME_ID_CONF_2 = 0x82;
    static const char* get_fan_mode_desc(FanMode mode);
    void traits(climate::ClimateTraits& traits, heat_pump_data_t& hp_data) override;
};

} // namespace hwp
} // namespace esphome
