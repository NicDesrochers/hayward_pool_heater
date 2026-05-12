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

#include "FrameConf4.h"
#include "CS.h"
#include "Schema.h"
namespace esphome {
namespace hwp {
CLASS_ID_DECLARATION(esphome::hwp::FrameConf4);
static constexpr char TAG[] = "hwp";
std::shared_ptr<BaseFrame> FrameConf4::create() {
    return std::make_shared<FrameConf4>(); // Create a FrameTemperature if type matches
}
const char* FrameConf4::type_string() const { return "CONFIG_4  "; }
bool FrameConf4::matches(BaseFrame& secialized, BaseFrame& base) {
    return base.packet.get_type() == FRAME_ID_CONF_4;
}
std::string FrameConf4::format(bool no_diff) const {
    if (!this->data_.has_value()) return "N/A";
    return this->format(*data_, (no_diff ? *data_ : prev_data_.value_or(*data_)));
}

std::string FrameConf4::format_prev() const {
    if (!this->prev_data_.has_value()) return "N/A";
    return this->format(this->prev_data_.value(), this->prev_data_.value());
}
void FrameConf4::traits(climate::ClimateTraits& traits, heat_pump_data_t& hp_data) {
    // N/A
}

std::string FrameConf4::format(const conf_4_t& val, const conf_4_t& ref) const {
    CS oss;
    bool changed = (val != ref);
    oss.set_changed_base_color(changed);

    oss << "F02 high cool " << val.f02_fan_high_speed_cool_setpoint.diff(
                                     ref.f02_fan_high_speed_cool_setpoint, ", ")
        << "F03 low cool "
        << val.f03_fan_low_speed_temp_in_cooling_set_point.diff(
               ref.f03_fan_low_speed_temp_in_cooling_set_point, ", ")
        << "F04 stop cool "
        << val.f04_fan_stop_temp_in_cooling_set_point.diff(
               ref.f04_fan_stop_temp_in_cooling_set_point, ", ")
        << "F05 high heat "
        << val.f05_fan_high_speed_temp_in_heating_set_point.diff(
               ref.f05_fan_high_speed_temp_in_heating_set_point, ", ")
        << "F06 low heat "
        << val.f06_fan_low_speed_temp_in_heating_set_point.diff(
               ref.f06_fan_low_speed_temp_in_heating_set_point, ", ")
        << "F07 stop heat "
        << val.f07_fan_stop_temp_in_heating_set_point.diff(
               ref.f07_fan_stop_temp_in_heating_set_point, ", ")
        << "F08 low run " << val.f08_fan_low_speed_running_time.diff(
                                  ref.f08_fan_low_speed_running_time, ", ")
        << "F09 stop low run "
        << val.f09_fan_stop_low_speed_running_time.diff(
               ref.f09_fan_stop_low_speed_running_time, ", unknown ")
        << val.unknown.diff(ref.unknown);
    return oss.str();
}
/**
 * @brief Parses the frame data and places it into the canonical
 *        heat_pump_data_t structure.
 *
 * The heat_pump_data_t is a canonical representation between the heat pump bus
 * data and the esphome heat pump component.
 * 
 * @param hp_data The heat_pump_data_t structure to fill
 * @see heat_pump_data_t
 * @note identifies fan speed temperature and timing parameters F02-F09
 */
void FrameConf4::parse(heat_pump_data_t& hp_data) {
    hp_data.f02_fan_high_speed_cool_setpoint =
        data_->f02_fan_high_speed_cool_setpoint.decode();
    hp_data.f03_fan_low_speed_temp_in_cooling_set_point =
        data_->f03_fan_low_speed_temp_in_cooling_set_point.decode();
    hp_data.f04_fan_stop_temp_in_cooling_set_point =
        data_->f04_fan_stop_temp_in_cooling_set_point.decode();
    hp_data.f05_fan_high_speed_temp_in_heating_set_point =
        data_->f05_fan_high_speed_temp_in_heating_set_point.decode();
    hp_data.f06_fan_low_speed_temp_in_heating_set_point =
        data_->f06_fan_low_speed_temp_in_heating_set_point.decode();
    hp_data.f07_fan_stop_temp_in_heating_set_point =
        data_->f07_fan_stop_temp_in_heating_set_point.decode();
    hp_data.f08_fan_low_speed_running_time = data_->f08_fan_low_speed_running_time.decode();
    hp_data.f09_fan_stop_low_speed_running_time =
        data_->f09_fan_stop_low_speed_running_time.decode();
}
optional<std::shared_ptr<BaseFrame>> FrameConf4::control(const HWPCall& call) {
    FrameConf4 fan_speed_control_frame(*this);
    bool has_data = this->data_.has_value();

    if (call.f02_fan_high_speed_cool_setpoint.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan high speed cool setpoint %.1f",
            *call.f02_fan_high_speed_cool_setpoint);
        fan_speed_control_frame.data().f02_fan_high_speed_cool_setpoint =
            *call.f02_fan_high_speed_cool_setpoint;
    }
    if (call.f03_fan_low_speed_temp_in_cooling_set_point.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan low speed cooling temp %.1f",
            *call.f03_fan_low_speed_temp_in_cooling_set_point);
        fan_speed_control_frame.data().f03_fan_low_speed_temp_in_cooling_set_point =
            *call.f03_fan_low_speed_temp_in_cooling_set_point;
    }
    if (call.f04_fan_stop_temp_in_cooling_set_point.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan stop cooling temp %.1f",
            *call.f04_fan_stop_temp_in_cooling_set_point);
        fan_speed_control_frame.data().f04_fan_stop_temp_in_cooling_set_point =
            *call.f04_fan_stop_temp_in_cooling_set_point;
    }
    if (call.f05_fan_high_speed_temp_in_heating_set_point.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan high speed heating temp %.1f",
            *call.f05_fan_high_speed_temp_in_heating_set_point);
        fan_speed_control_frame.data().f05_fan_high_speed_temp_in_heating_set_point =
            *call.f05_fan_high_speed_temp_in_heating_set_point;
    }
    if (call.f06_fan_low_speed_temp_in_heating_set_point.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan low speed heating temp %.1f",
            *call.f06_fan_low_speed_temp_in_heating_set_point);
        fan_speed_control_frame.data().f06_fan_low_speed_temp_in_heating_set_point =
            *call.f06_fan_low_speed_temp_in_heating_set_point;
    }
    if (call.f07_fan_stop_temp_in_heating_set_point.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan stop heating temp %.1f",
            *call.f07_fan_stop_temp_in_heating_set_point);
        fan_speed_control_frame.data().f07_fan_stop_temp_in_heating_set_point =
            *call.f07_fan_stop_temp_in_heating_set_point;
    }
    if (call.f08_fan_low_speed_running_time.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan low speed running time %.1f",
            *call.f08_fan_low_speed_running_time);
        fan_speed_control_frame.data().f08_fan_low_speed_running_time =
            *call.f08_fan_low_speed_running_time;
    }
    if (call.f09_fan_stop_low_speed_running_time.has_value()) {
        ESP_LOGI(TAG, "FrameConf4 control: request for fan stop low speed running time %.1f",
            *call.f09_fan_stop_low_speed_running_time);
        fan_speed_control_frame.data().f09_fan_stop_low_speed_running_time =
            *call.f09_fan_stop_low_speed_running_time;
    }
    if (!fan_speed_control_frame.is_changed() && has_data) {
        ESP_LOGV(TAG, "control: no changes to fan speed control");
        return nullopt;
    }
    if (!has_data) {
        ESP_LOGW(TAG, "Cannot control yet. Waiting for first FrameConf4 packet");
        call.component.status_momentary_warning("Waiting for first FrameConf4 packet", 5000);
        return nullopt;
    }
    fan_speed_control_frame.finalize();
    fan_speed_control_frame.print("TXQ", TAG, ESPHOME_LOG_LEVEL_VERBOSE, __LINE__);
    return optional<std::shared_ptr<FrameConf4>>{
        std::make_shared<FrameConf4>(fan_speed_control_frame)};
}
} // namespace hwp
} // namespace esphome
REGISTER_FRAME_ID_DEFAULT(esphome::hwp::FrameConf4);
