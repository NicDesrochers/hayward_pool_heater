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

#include "FrameConditionsD.h"
#include "CS.h"
#include "Schema.h"
namespace esphome {
namespace hwp {
CLASS_ID_DECLARATION(esphome::hwp::FrameConditionsD);
static constexpr char TAG[] = "hwp";
std::shared_ptr<BaseFrame> FrameConditionsD::create() {
    return std::make_shared<FrameConditionsD>(); // Create a FrameTemperature if type matches
}
const char* FrameConditionsD::type_string() const { return "COND_D    "; }
bool FrameConditionsD::matches(BaseFrame& secialized, BaseFrame& base) {
    return base.packet.get_type() == FRAME_ID_COND_D;
}
std::string FrameConditionsD::format(bool no_diff) const {
    if (!this->data_.has_value()) return "N/A";
    return this->format(*data_, (no_diff ? *data_ : prev_data_.value_or(*data_)));
}

std::string FrameConditionsD::format_prev() const {
    if (!this->prev_data_.has_value()) return "N/A";
    return this->format(this->prev_data_.value(), this->prev_data_.value());
}
void FrameConditionsD::traits(climate::ClimateTraits& traits, heat_pump_data_t& hp_data) {
    // N/A
}

std::string FrameConditionsD::format(const cond_d_t& val, const cond_d_t& ref) const {
    CS oss;
    bool changed = (val != ref);
    oss.set_changed_base_color(changed);

    oss << "[" << val.unknown_1.diff(ref.unknown_1, ", ")
        << val.unknown_2.diff(ref.unknown_2, ", ")
        << val.unknown_3.diff(ref.unknown_3, ", ")
        << val.unknown_4.diff(ref.unknown_4, ", ")
        << val.unknown_5.diff(ref.unknown_5, ", ") << val.unknown_6.diff(ref.unknown_6, ", ")
        << val.unknown_7.diff(ref.unknown_7, ", ") << val.unknown_8.diff(ref.unknown_8, ", ")
        << val.unknown_9.diff(ref.unknown_9, "]");
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
 * @note no current elements identified in this frame
 */
void FrameConditionsD::parse(heat_pump_data_t& hp_data) {
    // N/A
}
optional<std::shared_ptr<BaseFrame>> FrameConditionsD::control(const HWPCall& call) {
    // Not supported yet.
    return nullopt;
}
} // namespace hwp
} // namespace esphome
REGISTER_FRAME_ID_DEFAULT(esphome::hwp::FrameConditionsD);
