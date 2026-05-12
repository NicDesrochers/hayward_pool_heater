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
#include "helper_components.h"
#include "Schema.h"
#include "base_frame.h"
namespace esphome {

namespace hwp {
void GenerateCodeButton::press_action() {
    auto parent = this->get_parent();
    parent->generate_code();
}
void d01_defrost_start_number::control(float value) {
    auto parent=this->get_parent();
    HWPCall call_data = parent->instantiate_call();
    call_data.d01_defrost_start = value;
    this->get_parent()->control(call_data);
}
void d02_defrost_end_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.d02_defrost_end = value;
    this->get_parent()->control(call_data);
}
void d03_defrosting_cycle_time_minutes_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.d03_defrosting_cycle_time_minutes = value;
    this->get_parent()->control(call_data);
}
void d04_max_defrost_time_minutes_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.d04_max_defrost_time_minutes = value;
    this->get_parent()->control(call_data);
}
void d05_min_economy_defrost_time_minutes_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.d05_min_economy_defrost_time_minutes = value;
    this->get_parent()->control(call_data);
}

void r04_return_diff_cooling_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.r04_return_diff_cooling = value;
    this->get_parent()->control(call_data);
}
void r05_shutdown_temp_diff_when_cooling_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.r05_shutdown_temp_diff_when_cooling = value;
    this->get_parent()->control(call_data);
}
void r06_return_diff_heating_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.r06_return_diff_heating = value;
    this->get_parent()->control(call_data);
}
void r07_shutdown_diff_heating_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.r07_shutdown_diff_heating = value;
    this->get_parent()->control(call_data);
}
void f02_fan_high_speed_cool_setpoint_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f02_fan_high_speed_cool_setpoint = value;
    this->get_parent()->control(call_data);
}
void f03_fan_low_speed_temp_in_cooling_set_point_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f03_fan_low_speed_temp_in_cooling_set_point = value;
    this->get_parent()->control(call_data);
}
void f04_fan_stop_temp_in_cooling_set_point_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f04_fan_stop_temp_in_cooling_set_point = value;
    this->get_parent()->control(call_data);
}
void f05_fan_high_speed_temp_in_heating_set_point_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f05_fan_high_speed_temp_in_heating_set_point = value;
    this->get_parent()->control(call_data);
}
void f06_fan_low_speed_temp_in_heating_set_point_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f06_fan_low_speed_temp_in_heating_set_point = value;
    this->get_parent()->control(call_data);
}
void f07_fan_stop_temp_in_heating_set_point_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f07_fan_stop_temp_in_heating_set_point = value;
    this->get_parent()->control(call_data);
}
void f08_fan_low_speed_running_time_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f08_fan_low_speed_running_time = value;
    this->get_parent()->control(call_data);
}
void f09_fan_stop_low_speed_running_time_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f09_fan_stop_low_speed_running_time = value;
    this->get_parent()->control(call_data);
}
void f12_min_fan_voltage_pct_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f12_min_fan_voltage_pct = value;
    this->get_parent()->control(call_data);
}
void f13_max_fan_voltage_pct_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f13_max_fan_voltage_pct = value;
    this->get_parent()->control(call_data);
}
void u02_pulses_per_liter_number::control(float value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.u02_pulses_per_liter = value;
    this->get_parent()->control(call_data);
}

void d06_defrost_eco_mode_select::control(const std::string& value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.d06_defrost_eco_mode = DefrostEcoMode::from_string(value);
    this->get_parent()->control(call_data);
}
void u01_flow_meter_select::control(const std::string& value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.u01_flow_meter = FlowMeterEnable::from_string(value);
    this->get_parent()->control(call_data);
}
void h02_mode_restrictions_select::control(const std::string& value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.h02_mode_restrictions = HeatPumpRestrict::from_string(value);
    this->get_parent()->control(call_data);
}
void f10_fan_speed_control_temp_select::control(const std::string& value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f10_fan_speed_control_temp = FanSpeedControlTempMode::from_string(value);
    this->get_parent()->control(call_data);
}
void f11_speed_control_module_select::control(const std::string& value) {
    HWPCall call_data = this->get_parent()->instantiate_call();
    call_data.f11_speed_control_module = SpeedControlModule::from_string(value);
    this->get_parent()->control(call_data);
}

} // namespace hwp

} // namespace esphome
