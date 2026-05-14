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
#include "hwp_simulator.h"

#include "esphome/core/hal.h"
#include "esphome/core/log.h"

#ifndef HWP_NATIVE_TEST
#include <freertos/FreeRTOS.h>
#endif

#include <algorithm>
#include <cstdio>
#include <vector>

namespace esphome {
namespace hwp_simulator {

static constexpr const char* TAG = "hwp_sim";
static constexpr uint32_t HWP_SIM_RMT_RESOLUTION_HZ = 312500;
static constexpr uint32_t HWP_SIM_RMT_MAX_SYMBOL_TICKS = 0x7FFF;

static uint32_t hwp_sim_us_to_rmt_ticks(uint32_t duration_us) {
    uint64_t ticks =
        (static_cast<uint64_t>(duration_us) * HWP_SIM_RMT_RESOLUTION_HZ + 1000000ULL - 1) /
        1000000ULL;
    if (ticks == 0) {
        return 1;
    }
    if (ticks > HWP_SIM_RMT_MAX_SYMBOL_TICKS) {
        return HWP_SIM_RMT_MAX_SYMBOL_TICKS;
    }
    return static_cast<uint32_t>(ticks);
}

static constexpr uint32_t hwp_sim_rmt_ticks_to_us(uint32_t ticks) {
    return static_cast<uint32_t>(
        (static_cast<uint64_t>(ticks) * 1000000ULL + HWP_SIM_RMT_RESOLUTION_HZ / 2) /
        HWP_SIM_RMT_RESOLUTION_HZ);
}

static constexpr uint32_t HWP_SIM_RMT_MAX_SYMBOL_US =
    hwp_sim_rmt_ticks_to_us(HWP_SIM_RMT_MAX_SYMBOL_TICKS);

void HWPSimulator::setup() {
    if (pin_ != nullptr) {
        pin_->setup();
        pin_->pin_mode(gpio::FLAG_OUTPUT | gpio::FLAG_OPEN_DRAIN);
        pin_->digital_write(true);
    }
    setup_rmt_();
    set_playbook(startup_playbook_);
    set_active(active_on_boot_);
    publish_status_();
}

void HWPSimulator::loop() {
    process_rx_();
    if (!engine_.active()) {
        return;
    }
    const uint32_t now = millis();
    if (next_step_ms_ != 0 && now < next_step_ms_) {
        return;
    }
    const auto step = engine_.step_once();
    publish_step_(step);
    next_step_ms_ = now + step.delay_ms;
}

void HWPSimulator::dump_config() {
    ESP_LOGCONFIG(TAG, "HWP Simulator:");
    LOG_PIN("  Pin: ", pin_);
    ESP_LOGCONFIG(TAG, "  Startup playbook: %s", startup_playbook_.c_str());
    ESP_LOGCONFIG(TAG, "  Active on boot: %s", active_on_boot_ ? "YES" : "NO");
    ESP_LOGCONFIG(TAG, "  Packet buffer size: %u", static_cast<unsigned>(packet_buffer_size_));
}

void HWPSimulator::set_startup_playbook(const std::string& playbook) {
    startup_playbook_ = playbook;
    if (auto parsed = playbook_from_string(playbook)) {
        engine_.set_playbook(*parsed);
    }
}

void HWPSimulator::set_playbook(const std::string& value) {
    auto parsed = playbook_from_string(value);
    if (!parsed.has_value()) {
        ESP_LOGW(TAG, "Unknown simulator playbook: %s", value.c_str());
        return;
    }
    engine_.set_playbook(*parsed);
    if (playbook_select_ != nullptr) {
        playbook_select_->publish_state(value);
    }
    publish_status_();
}

void HWPSimulator::set_active(bool active) {
    engine_.set_active(active);
    if (active_switch_ != nullptr) {
        active_switch_->publish_state(active);
    }
    next_step_ms_ = 0;
    publish_status_();
}

void HWPSimulator::set_interval_scale(float value) {
    engine_.set_interval_scale(value);
    if (interval_scale_number_ != nullptr) {
        interval_scale_number_->publish_state(engine_.interval_scale());
    }
}

void HWPSimulator::start() { set_active(true); }

void HWPSimulator::pause() { set_active(false); }

void HWPSimulator::step_once() {
    const bool was_active = engine_.active();
    engine_.set_active(true);
    const auto step = engine_.step_once();
    publish_step_(step);
    engine_.set_active(was_active);
    publish_status_();
}

void HWPSimulator::reset_state() {
    engine_.reset();
    next_step_ms_ = 0;
    publish_status_();
}

void HWPSimulator::inject_next_event() { step_once(); }

void HWPSimulator::handle_command(const std::string& command) {
    if (command.rfind("playbook ", 0) == 0) {
        set_playbook(command.substr(9));
    } else if (command == "start") {
        start();
    } else if (command == "pause") {
        pause();
    } else if (command == "step") {
        step_once();
    } else if (command == "reset") {
        reset_state();
    } else if (command.rfind("inject frame=", 0) == 0) {
        const auto* packet = find_catalog_packet(command.substr(13));
        if (packet == nullptr) {
            ESP_LOGW(TAG, "Unknown fixture packet for injection: %s", command.c_str());
            return;
        }
        SimulatorStep step;
        step.has_packet = true;
        step.packet = packet->packet;
        step.packet_id = packet->id;
        step.label = packet->label;
        step.event = "manual_inject";
        publish_step_(step);
    } else {
        ESP_LOGW(TAG, "Unknown simulator command: %s", command.c_str());
    }
    if (command_text_ != nullptr) {
        command_text_->publish_state(command);
    }
}

bool HWPSimulator::setup_rmt_() {
#ifdef HWP_NATIVE_TEST
    return false;
#else
    if (pin_ == nullptr) {
        return false;
    }

    if (rb_ == nullptr) {
        const size_t ring_symbols = std::max<size_t>(packet_buffer_size_, 128);
        rb_ = xRingbufferCreate(ring_symbols * sizeof(rmt_symbol_word_t), RINGBUF_TYPE_BYTEBUF);
        if (rb_ == nullptr) {
            ESP_LOGE(TAG, "Failed to create simulator RMT RX ring buffer");
            return false;
        }
    }

    rmt_receive_config_ = {};
    rmt_receive_config_.signal_range_min_ns = 1000;
    rmt_receive_config_.signal_range_max_ns = HWP_SIM_RMT_MAX_SYMBOL_US * 1000;
    rmt_transmit_config_ = {};
    rmt_transmit_config_.loop_count = 0;
    rmt_transmit_config_.flags.eot_level = 1;

    if (rmt_rx_channel_ == nullptr) {
        rmt_rx_channel_config_t rx_config = {};
        rx_config.gpio_num = static_cast<gpio_num_t>(pin_->get_pin());
        rx_config.clk_src = RMT_CLK_SRC_DEFAULT;
        rx_config.resolution_hz = HWP_SIM_RMT_RESOLUTION_HZ;
        rx_config.mem_block_symbols = 128;
        rx_config.intr_priority = 0;

        esp_err_t err = rmt_new_rx_channel(&rx_config, &rmt_rx_channel_);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to create simulator RMT RX channel: %d", err);
            rmt_rx_channel_ = nullptr;
            return false;
        }

        rmt_rx_event_callbacks_t callbacks = {};
        callbacks.on_recv_done = &HWPSimulator::rmt_rx_done_callback;
        err = rmt_rx_register_event_callbacks(rmt_rx_channel_, &callbacks, this);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to register simulator RMT RX callback: %d", err);
            return false;
        }
    }

    if (rmt_tx_channel_ != nullptr && rmt_copy_encoder_ != nullptr) {
        resume_receive_();
        return true;
    }

    rmt_tx_channel_config_t tx_config = {};
    tx_config.gpio_num = static_cast<gpio_num_t>(pin_->get_pin());
    tx_config.clk_src = RMT_CLK_SRC_DEFAULT;
    tx_config.resolution_hz = HWP_SIM_RMT_RESOLUTION_HZ;
    tx_config.mem_block_symbols = 128;
    tx_config.trans_queue_depth = 1;
    tx_config.intr_priority = 0;
    tx_config.flags.io_od_mode = 1;
    tx_config.flags.init_level = 1;

    esp_err_t err = rmt_new_tx_channel(&tx_config, &rmt_tx_channel_);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create simulator RMT TX channel: %d", err);
        rmt_tx_channel_ = nullptr;
        return false;
    }

    rmt_copy_encoder_config_t copy_config = {};
    err = rmt_new_copy_encoder(&copy_config, &rmt_copy_encoder_);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create simulator RMT copy encoder: %d", err);
        rmt_copy_encoder_ = nullptr;
        return false;
    }

    err = rmt_enable(rmt_tx_channel_);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable simulator RMT TX channel: %d", err);
        return false;
    }
    resume_receive_();
    return true;
#endif
}

bool HWPSimulator::arm_receive_() {
#ifdef HWP_NATIVE_TEST
    return false;
#else
    if (rmt_rx_channel_ == nullptr || !rmt_rx_enabled_) {
        return false;
    }
    if (rmt_rx_armed_) {
        return false;
    }
    esp_err_t err = rmt_receive(rmt_rx_channel_, rmt_rx_symbols_.data(),
        rmt_rx_symbols_.size() * sizeof(rmt_symbol_word_t), &rmt_receive_config_);
    if (err != ESP_OK) {
        if (err == ESP_ERR_INVALID_STATE) {
            rmt_rx_armed_ = true;
            return true;
        }
        ESP_LOGW(TAG, "Failed to arm simulator RMT RX: %d", err);
        return false;
    }
    rmt_rx_armed_ = true;
    return true;
#endif
}

void HWPSimulator::stop_receive_() {
#ifndef HWP_NATIVE_TEST
    if (rmt_rx_channel_ != nullptr && rmt_rx_enabled_) {
        rmt_disable(rmt_rx_channel_);
        rmt_rx_enabled_ = false;
        rmt_rx_armed_ = false;
    }
#endif
}

void HWPSimulator::resume_receive_() {
#ifndef HWP_NATIVE_TEST
    if (rmt_rx_channel_ == nullptr) {
        return;
    }
    if (!rmt_rx_enabled_) {
        esp_err_t err = rmt_enable(rmt_rx_channel_);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to enable simulator RMT RX channel: %d", err);
            return;
        }
        rmt_rx_enabled_ = true;
    }
    arm_receive_();
#endif
}

bool HWPSimulator::rmt_rx_done_callback(
    rmt_channel_handle_t channel, const rmt_rx_done_event_data_t* event_data, void* user_data) {
#ifdef HWP_NATIVE_TEST
    return false;
#else
    auto* instance = static_cast<HWPSimulator*>(user_data);
    if (instance == nullptr || event_data == nullptr || event_data->received_symbols == nullptr ||
        instance->rb_ == nullptr) {
        return false;
    }
    instance->rmt_rx_armed_ = false;
    const size_t symbols_size = event_data->num_symbols * sizeof(rmt_symbol_word_t);
    if (symbols_size == 0) {
        return false;
    }

    BaseType_t high_task_wakeup = pdFALSE;
    if (xRingbufferSendFromISR(instance->rb_, event_data->received_symbols, symbols_size,
            &high_task_wakeup) != pdTRUE) {
        instance->engine_.record_error();
    }
    return high_task_wakeup == pdTRUE;
#endif
}

void HWPSimulator::publish_status_() {
    const auto& stats = engine_.stats();
    if (current_playbook_sensor_ != nullptr) {
        current_playbook_sensor_->publish_state(playbook_to_string(engine_.playbook()));
    }
    if (status_sensor_ != nullptr) {
        status_sensor_->publish_state(engine_.active() ? "active" : "paused");
    }
    if (step_sensor_ != nullptr) {
        step_sensor_->publish_state(stats.step);
    }
    if (packet_count_sensor_ != nullptr) {
        packet_count_sensor_->publish_state(stats.packet_count);
    }
    if (error_count_sensor_ != nullptr) {
        error_count_sensor_->publish_state(stats.error_count);
    }
}

void HWPSimulator::publish_step_(const SimulatorStep& step) {
    if (step.has_packet) {
        emit_packet_(step);
        if (last_frame_sensor_ != nullptr) {
            last_frame_sensor_->publish_state(format_packet_(step));
        }
    }
    publish_status_();
}

void HWPSimulator::publish_rx_packet_(const Packet& packet, const char* status) {
    if (last_rx_frame_sensor_ != nullptr) {
        last_rx_frame_sensor_->publish_state(format_packet_(packet, status, "rx"));
    }
}

void HWPSimulator::process_rx_() {
#ifndef HWP_NATIVE_TEST
    if (rb_ == nullptr) {
        return;
    }
    size_t item_size = 0;
    while (auto* item = static_cast<rmt_symbol_word_t*>(xRingbufferReceive(rb_, &item_size, 0))) {
        const size_t symbol_count = item_size / sizeof(rmt_symbol_word_t);
        std::vector<esphome::hwp::wire::PulseSymbol> symbols;
        symbols.reserve(symbol_count);
        for (size_t index = 0; index < symbol_count; ++index) {
            symbols.push_back(esphome::hwp::wire::PulseSymbol{
                hwp_sim_rmt_ticks_to_us(item[index].duration0),
                static_cast<uint32_t>(item[index].level0),
                hwp_sim_rmt_ticks_to_us(item[index].duration1),
                static_cast<uint32_t>(item[index].level1),
            });
        }
        vRingbufferReturnItem(rb_, item);
        process_rx_symbols_(symbols.data(), symbols.size());
    }
    if (rmt_rx_enabled_ && !rmt_rx_armed_) {
        arm_receive_();
    }
#endif
}

bool HWPSimulator::process_rx_symbols_(
    const esphome::hwp::wire::PulseSymbol* symbols, size_t symbol_count) {
    Packet packet;
    const bool decoded =
        esphome::hwp::wire::decode_packet_symbols(
            symbols, symbol_count, esphome::hwp::wire::PacketSource::CONTROLLER, packet);
    if (!decoded) {
        engine_.record_error();
        if (status_sensor_ != nullptr) {
            status_sensor_->publish_state("invalid controller packet");
        }
        publish_status_();
        return false;
    }

    const auto result = engine_.receive_controller_packet(packet);
    publish_rx_packet_(packet, result.status);
    if (status_sensor_ != nullptr) {
        status_sensor_->publish_state(result.status);
    }
    if (result.has_echo) {
        emit_packet_(result.echo);
        if (last_echo_sensor_ != nullptr) {
            last_echo_sensor_->publish_state(format_packet_(result.echo));
        }
        if (last_frame_sensor_ != nullptr) {
            last_frame_sensor_->publish_state(format_packet_(result.echo));
        }
    }
    publish_status_();
    return result.accepted;
}

bool HWPSimulator::emit_packet_(const SimulatorStep& step) {
    if (!step.has_packet) {
        return false;
    }
    auto pulse_symbols = esphome::hwp::wire::encode_packet_symbols(
        step.packet.data.data(), step.packet.length, step.packet.source, true);
    ESP_LOGI(TAG, "SIM %s %s len=%u symbols=%u", step.event, step.packet_id,
        static_cast<unsigned>(step.packet.length), static_cast<unsigned>(pulse_symbols.size()));
#ifdef HWP_NATIVE_TEST
    return !pulse_symbols.empty();
#else
    if (pulse_symbols.empty()) {
        return false;
    }
    if (!setup_rmt_()) {
        return false;
    }

    std::vector<rmt_symbol_word_t> symbols;
    symbols.reserve(pulse_symbols.size());
    for (const auto& pulse : pulse_symbols) {
        rmt_symbol_word_t symbol{};
        symbol.level0 = pulse.level0;
        symbol.duration0 = hwp_sim_us_to_rmt_ticks(pulse.duration0);
        symbol.level1 = pulse.level1;
        symbol.duration1 = hwp_sim_us_to_rmt_ticks(pulse.duration1);
        symbols.push_back(symbol);
    }

    stop_receive_();
    esp_err_t err = rmt_transmit(rmt_tx_channel_, rmt_copy_encoder_, symbols.data(),
        symbols.size() * sizeof(rmt_symbol_word_t), &rmt_transmit_config_);
    if (err == ESP_OK) {
        err = rmt_tx_wait_all_done(rmt_tx_channel_, 2500);
    }
    resume_receive_();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Simulator RMT transmit failed: %d", err);
        return false;
    }
    return true;
#endif
}

std::string HWPSimulator::format_packet_(const SimulatorStep& step) const {
    return format_packet_(step.packet, step.event, step.packet_id);
}

std::string HWPSimulator::format_packet_(
    const Packet& packet, const char* event, const char* packet_id) const {
    char buffer[96];
    std::snprintf(buffer, sizeof(buffer), "%s %s 0x%02X len=%u", event, packet_id,
        packet.length > 0 ? packet.data[0] : 0, static_cast<unsigned>(packet.length));
    return buffer;
}

void HWPSimulatorPlaybookSelect::control(const std::string& value) {
    this->get_parent()->set_playbook(value);
}

void HWPSimulatorActiveSwitch::write_state(bool state) {
    this->get_parent()->set_active(state);
}

void HWPSimulatorIntervalScaleNumber::control(float value) {
    this->get_parent()->set_interval_scale(value);
}

void HWPSimulatorStartButton::press_action() {
    this->get_parent()->start();
}

void HWPSimulatorPauseButton::press_action() {
    this->get_parent()->pause();
}

void HWPSimulatorStepButton::press_action() {
    this->get_parent()->step_once();
}

void HWPSimulatorResetButton::press_action() {
    this->get_parent()->reset_state();
}

void HWPSimulatorInjectButton::press_action() {
    this->get_parent()->inject_next_event();
}

void HWPSimulatorCommandText::control(const std::string& value) {
    this->get_parent()->handle_command(value);
}

} // namespace hwp_simulator
} // namespace esphome
