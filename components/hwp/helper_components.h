
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
#include "PoolHeater.h"
#include "esphome/components/number/number.h"
#include "esphome/components/select/select.h"

#include <string>

namespace esphome {
namespace hwp {

class GenerateCodeButton : public button::Button, public Parented<PoolHeater>, public Component {
  protected:
    void press_action() override;
};
class d01_defrost_start_number : public number::Number, public Parented<PoolHeater> {
  public:
    d01_defrost_start_number() = default;

  protected:
    void control(float value) override;
};

class d02_defrost_end_number : public number::Number, public Parented<PoolHeater> {
  public:
    d02_defrost_end_number() = default;

  protected:
    void control(float value) override;
};
class d03_defrosting_cycle_time_minutes_number : public number::Number,
                                                 public Parented<PoolHeater> {
  public:
    d03_defrosting_cycle_time_minutes_number() = default;

  protected:
    void control(float value) override;
};
class d04_max_defrost_time_minutes_number : public number::Number, public Parented<PoolHeater> {
  public:
    d04_max_defrost_time_minutes_number() = default;

  protected:
    void control(float value) override;
};
class d05_min_economy_defrost_time_minutes_number : public number::Number,
                                                    public Parented<PoolHeater> {
  public:
    d05_min_economy_defrost_time_minutes_number() = default;

  protected:
    void control(float value) override;
};

class r04_return_diff_cooling_number : public number::Number, public Parented<PoolHeater> {
  public:
    r04_return_diff_cooling_number() = default;

  protected:
    void control(float value) override;
};
class r05_shutdown_temp_diff_when_cooling_number : public number::Number,
                                                   public Parented<PoolHeater> {
  public:
    r05_shutdown_temp_diff_when_cooling_number() = default;

  protected:
    void control(float value) override;
};
class r06_return_diff_heating_number : public number::Number, public Parented<PoolHeater> {
  public:
    r06_return_diff_heating_number() = default;

  protected:
    void control(float value) override;
};
class r07_shutdown_diff_heating_number : public number::Number, public Parented<PoolHeater> {
  public:
    r07_shutdown_diff_heating_number() = default;

  protected:
    void control(float value) override;
};

class f02_fan_high_speed_cool_setpoint_number : public number::Number,
                                                 public Parented<PoolHeater> {
  public:
    f02_fan_high_speed_cool_setpoint_number() = default;

  protected:
    void control(float value) override;
};
class f03_fan_low_speed_temp_in_cooling_set_point_number : public number::Number,
                                                           public Parented<PoolHeater> {
  public:
    f03_fan_low_speed_temp_in_cooling_set_point_number() = default;

  protected:
    void control(float value) override;
};
class f04_fan_stop_temp_in_cooling_set_point_number : public number::Number,
                                                      public Parented<PoolHeater> {
  public:
    f04_fan_stop_temp_in_cooling_set_point_number() = default;

  protected:
    void control(float value) override;
};
class f05_fan_high_speed_temp_in_heating_set_point_number : public number::Number,
                                                            public Parented<PoolHeater> {
  public:
    f05_fan_high_speed_temp_in_heating_set_point_number() = default;

  protected:
    void control(float value) override;
};
class f06_fan_low_speed_temp_in_heating_set_point_number : public number::Number,
                                                           public Parented<PoolHeater> {
  public:
    f06_fan_low_speed_temp_in_heating_set_point_number() = default;

  protected:
    void control(float value) override;
};
class f07_fan_stop_temp_in_heating_set_point_number : public number::Number,
                                                      public Parented<PoolHeater> {
  public:
    f07_fan_stop_temp_in_heating_set_point_number() = default;

  protected:
    void control(float value) override;
};
class f08_fan_low_speed_running_time_number : public number::Number,
                                              public Parented<PoolHeater> {
  public:
    f08_fan_low_speed_running_time_number() = default;

  protected:
    void control(float value) override;
};
class f09_fan_stop_low_speed_running_time_number : public number::Number,
                                                   public Parented<PoolHeater> {
  public:
    f09_fan_stop_low_speed_running_time_number() = default;

  protected:
    void control(float value) override;
};
class f12_min_fan_voltage_pct_number : public number::Number, public Parented<PoolHeater> {
  public:
    f12_min_fan_voltage_pct_number() = default;

  protected:
    void control(float value) override;
};
class f13_max_fan_voltage_pct_number : public number::Number, public Parented<PoolHeater> {
  public:
    f13_max_fan_voltage_pct_number() = default;

  protected:
    void control(float value) override;
};

class u01_flow_meter_number : public number::Number, public Parented<PoolHeater> {
  public:
    u01_flow_meter_number() = default;

  protected:
    void control(float value) override;
};
class u02_pulses_per_liter_number : public number::Number, public Parented<PoolHeater> {
  public:
    u02_pulses_per_liter_number() = default;

  protected:
    void control(float value) override;
};
class d06_defrost_eco_mode_select : public select::Select, public Parented<PoolHeater> {
  public:
    d06_defrost_eco_mode_select() = default;

  protected:
    void control(const std::string& value) override;
};
class u01_flow_meter_select : public select::Select, public Parented<PoolHeater> {
  public:
    u01_flow_meter_select() = default;

  protected:
    void control(const std::string& value) override;
};

class h02_mode_restrictions_select : public select::Select, public Parented<PoolHeater> {
  public:
    h02_mode_restrictions_select() = default;

  protected:
    void control(const std::string& value) override;
};

class f10_fan_speed_control_temp_select : public select::Select, public Parented<PoolHeater> {
  public:
    f10_fan_speed_control_temp_select() = default;

  protected:
    void control(const std::string& value) override;
};

class f11_speed_control_module_select : public select::Select, public Parented<PoolHeater> {
  public:
    f11_speed_control_module_select() = default;

  protected:
    void control(const std::string& value) override;
};


} // namespace hwp
} // namespace esphome
