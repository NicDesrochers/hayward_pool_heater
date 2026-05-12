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
#include "Schema.h"
namespace esphome {
namespace hwp {
const HeatPumpRestrict HeatPumpRestrict::Cooling(0);
const HeatPumpRestrict HeatPumpRestrict::Any(1);
const HeatPumpRestrict HeatPumpRestrict::Heating(2);
const char* HeatPumpRestrict::HeatPumpStrCooling = "Cooling Only";
const char* HeatPumpRestrict::HeatPumpStrAny = "Any Mode";
const char* HeatPumpRestrict::HeatPumpStrHeating = "Heating Only";

// Define the static constants
const DefrostEcoMode DefrostEcoMode::Eco(0);
const DefrostEcoMode DefrostEcoMode::Normal(1);
const char* DefrostEcoMode::DefrostEcoStrEco = "Eco";
const char* DefrostEcoMode::DefrostEcoStrNormal = "Normal";

// Define the static constants
const FlowMeterEnable FlowMeterEnable::Enabled(0);
const FlowMeterEnable FlowMeterEnable::Disabled(1);
const char* FlowMeterEnable::FlowMeterStrEnabled = "Enabled";
const char* FlowMeterEnable::FlowMeterStrDisabled = "Disabled";

const FanSpeedControlTempMode FanSpeedControlTempMode::ControlledByCoilTemperature(
    protocol::FAN_SPEED_CONTROL_COIL);
const FanSpeedControlTempMode FanSpeedControlTempMode::ControlledByAmbientTemperature(
    protocol::FAN_SPEED_CONTROL_AMBIENT);
const char* FanSpeedControlTempMode::ControlledByCoilTemperatureStr =
    protocol::FAN_SPEED_CONTROL_COIL_STRING;
const char* FanSpeedControlTempMode::ControlledByAmbientTemperatureStr =
    protocol::FAN_SPEED_CONTROL_AMBIENT_STRING;

const SpeedControlModule SpeedControlModule::Enabled(protocol::SPEED_CONTROL_MODULE_ENABLED);
const SpeedControlModule SpeedControlModule::Disabled(protocol::SPEED_CONTROL_MODULE_DISABLED);
const char* SpeedControlModule::EnabledStr = protocol::SPEED_CONTROL_MODULE_ENABLED_STRING;
const char* SpeedControlModule::DisabledStr = protocol::SPEED_CONTROL_MODULE_DISABLED_STRING;

const char * FanMode::ambient_desc = protocol::FAN_MODE_AMBIENT_STRING;
const char * FanMode::ambient_scheduled_desc = protocol::FAN_MODE_AMBIENT_SCHEDULED_STRING;
const char * FanMode::scheduled_desc = protocol::FAN_MODE_SCHEDULED_STRING;
const FanMode unknown = FanMode::Value::UNKNOWN;
const FanMode low_speed = FanMode::Value::LOW_SPEED;
const FanMode high_speed = FanMode::Value::HIGH_SPEED;
const FanMode ambient = FanMode::Value::AMBIENT;
const FanMode scheduled = FanMode::Value::SCHEDULED;
const FanMode ambient_scheduled = FanMode::Value::AMBIENT_SCHEDULED;

} // namespace hwp
} // namespace esphome
