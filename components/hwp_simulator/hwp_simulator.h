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

#include "hwp_simulator_engine.h"

#include "esphome/components/button/button.h"
#include "esphome/components/number/number.h"
#include "esphome/components/select/select.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/text/text.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/core/component.h"
#include "esphome/core/gpio.h"
#include "esphome/core/helpers.h"

#ifndef HWP_NATIVE_TEST
#include <driver/rmt_common.h>
#include <driver/rmt_encoder.h>
#include <driver/rmt_rx.h>
#include <driver/rmt_tx.h>
#include <freertos/ringbuf.h>
#endif

#include <array>
#include <string>

namespace esphome {
namespace hwp_simulator {

class HWPSimulator : public Component {
  public:
    explicit HWPSimulator(InternalGPIOPin* pin) : pin_(pin) {}

    void setup() override;
    void loop() override;
    void dump_config() override;

    void set_startup_playbook(const std::string& playbook);
    void set_packet_buffer_size(size_t size) { packet_buffer_size_ = size; }
    void set_active_on_boot(bool active) { active_on_boot_ = active; }

    void set_playbook_select(select::Select* entity) { playbook_select_ = entity; }
    void set_active_switch(switch_::Switch* entity) { active_switch_ = entity; }
    void set_interval_scale_number(number::Number* entity) { interval_scale_number_ = entity; }
    void set_command_text(text::Text* entity) { command_text_ = entity; }
    void set_current_playbook_sensor(text_sensor::TextSensor* entity) { current_playbook_sensor_ = entity; }
    void set_last_frame_sensor(text_sensor::TextSensor* entity) { last_frame_sensor_ = entity; }
    void set_last_rx_frame_sensor(text_sensor::TextSensor* entity) { last_rx_frame_sensor_ = entity; }
    void set_last_echo_sensor(text_sensor::TextSensor* entity) { last_echo_sensor_ = entity; }
    void set_status_sensor(text_sensor::TextSensor* entity) { status_sensor_ = entity; }
    void set_step_sensor(sensor::Sensor* entity) { step_sensor_ = entity; }
    void set_packet_count_sensor(sensor::Sensor* entity) { packet_count_sensor_ = entity; }
    void set_error_count_sensor(sensor::Sensor* entity) { error_count_sensor_ = entity; }

    void set_playbook(const std::string& value);
    void set_active(bool active);
    void set_interval_scale(float value);
    void start();
    void pause();
    void step_once();
    void reset_state();
    void inject_next_event();
    void handle_command(const std::string& command);

  protected:
    bool setup_rmt_();
    void publish_status_();
    void publish_step_(const SimulatorStep& step);
    void publish_rx_packet_(const Packet& packet, const char* status);
    void process_rx_();
    bool process_rx_symbols_(const esphome::hwp::wire::PulseSymbol* symbols, size_t symbol_count);
    bool emit_packet_(const SimulatorStep& step);
    void wiggle_pin_();
    std::string format_packet_(const SimulatorStep& step) const;
    std::string format_packet_(const Packet& packet, const char* event, const char* packet_id) const;

    InternalGPIOPin* pin_{nullptr};
    SimulatorEngine engine_;
    std::string startup_playbook_{"normal_idle"};
    size_t packet_buffer_size_{120};
    bool active_on_boot_{false};
    uint32_t next_step_ms_{0};

#ifndef HWP_NATIVE_TEST
    rmt_channel_handle_t rmt_rx_channel_{nullptr};
    rmt_channel_handle_t rmt_tx_channel_{nullptr};
    rmt_encoder_handle_t rmt_copy_encoder_{nullptr};
    rmt_receive_config_t rmt_receive_config_{};
    rmt_transmit_config_t rmt_transmit_config_{};
    std::array<rmt_symbol_word_t, 128> rmt_rx_symbols_{};
    RingbufHandle_t rb_{nullptr};
    bool rmt_rx_enabled_{false};
    bool rmt_rx_armed_{false};
    bool arm_receive_();
    void stop_receive_();
    void resume_receive_();
    static bool rmt_rx_done_callback(
        rmt_channel_handle_t channel, const rmt_rx_done_event_data_t* event_data, void* user_data);
#endif

    select::Select* playbook_select_{nullptr};
    switch_::Switch* active_switch_{nullptr};
    number::Number* interval_scale_number_{nullptr};
    text::Text* command_text_{nullptr};
    text_sensor::TextSensor* current_playbook_sensor_{nullptr};
    text_sensor::TextSensor* last_frame_sensor_{nullptr};
    text_sensor::TextSensor* last_rx_frame_sensor_{nullptr};
    text_sensor::TextSensor* last_echo_sensor_{nullptr};
    text_sensor::TextSensor* status_sensor_{nullptr};
    sensor::Sensor* step_sensor_{nullptr};
    sensor::Sensor* packet_count_sensor_{nullptr};
    sensor::Sensor* error_count_sensor_{nullptr};
};

class HWPSimulatorPlaybookSelect : public select::Select, public Parented<HWPSimulator> {
  protected:
    void control(const std::string& value) override;
};

class HWPSimulatorActiveSwitch : public switch_::Switch, public Parented<HWPSimulator>, public Component {
  protected:
    void write_state(bool state) override;
};

class HWPSimulatorIntervalScaleNumber : public number::Number, public Parented<HWPSimulator> {
  protected:
    void control(float value) override;
};

class HWPSimulatorStartButton : public button::Button, public Parented<HWPSimulator>, public Component {
  protected:
    void press_action() override;
};

class HWPSimulatorPauseButton : public button::Button, public Parented<HWPSimulator>, public Component {
  protected:
    void press_action() override;
};

class HWPSimulatorStepButton : public button::Button, public Parented<HWPSimulator>, public Component {
  protected:
    void press_action() override;
};

class HWPSimulatorResetButton : public button::Button, public Parented<HWPSimulator>, public Component {
  protected:
    void press_action() override;
};

class HWPSimulatorInjectButton : public button::Button, public Parented<HWPSimulator>, public Component {
  protected:
    void press_action() override;
};

class HWPSimulatorCommandText : public text::Text, public Parented<HWPSimulator> {
  protected:
    void control(const std::string& value) override;
};

} // namespace hwp_simulator
} // namespace esphome
