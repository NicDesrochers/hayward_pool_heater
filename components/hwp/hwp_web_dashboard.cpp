/**
 * @file hwp_web_dashboard.cpp
 * @brief Firmware-served HWP diagnostic dashboard support.
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
 * copies or substantial portions of the Software.
 */

#include "hwp_web_dashboard.h"

#include "hwp_time_adapter.h"
#include "hwp_version.h"

#include <algorithm>
#include <cstdio>
#include <map>
#include <utility>

#ifndef HWP_NATIVE_TEST
#include "esphome/core/hal.h"
#endif

namespace esphome {
namespace hwp {

namespace {

const char HWP_WEB_INDEX[] =
    "<!doctype html><html><head><meta charset=utf-8><meta name=viewport "
    "content='width=device-width,initial-scale=1'><title>HWP</title><style>"
    "body{margin:0 0 76px;font:14px system-ui;background:#f5f7fa;color:#17202a}"
    "header{padding:12px 16px;background:#17324d;color:white;display:flex;gap:12px;align-items:center}"
    "button{border:0;background:#dce6f1;padding:8px 10px;margin:0 4px 0 0;border-radius:4px}"
    "input{padding:8px;border:1px solid #c5d0dc;border-radius:4px;min-width:220px}"
    "button.active{background:#1d6fb8;color:white}.view{display:none;padding:10px}.view.active{display:block}"
    "table{border-collapse:collapse;width:100%;background:white}th,td{padding:6px 8px;border-bottom:1px solid #e1e5ea;text-align:left}"
    "tr.changed,span.changed{background:#fff2a8}.bad{color:#a40000;font-weight:700}.packet{font-family:ui-monospace,monospace;margin:6px 0;padding:8px;background:white;border-left:4px solid #8aa4bd;overflow:auto}"
    ".annotate{position:fixed;left:0;right:0;bottom:0;z-index:20;padding:10px;background:#edf3f8;border-top:1px solid #c6d4e1;box-shadow:0 -2px 8px #0002}"
    ".meta{font-size:12px;color:#52616f}.chart{background:white;border:1px solid #d8dee6;margin:10px 0;padding:8px}.chart h3{margin:0 0 4px;font-size:15px;color:#17324d}.chart p{margin:0 0 6px}.chart canvas{display:block;width:100%;height:260px}"
    "</style></head><body><header><strong>HWP</strong><span id=meta></span></header>"
    "<nav style='padding:8px;background:#e9eef4'><button data-tab=values class=active>Values</button><button data-tab=frames>Frames</button><button data-tab=packets>Packets</button><button data-tab=graphs>Graphs</button></nav>"
    "<section id=values class='view active'><table><thead><tr><th>Field</th><th>Value</th><th>Age</th><th>Source</th><th>Frame</th><th>Raw</th></tr></thead><tbody id=valueRows></tbody></table></section>"
    "<section id=frames class=view><div class=meta>Latest packet seen for each frame/source/length, including unknown frames.</div><div id=frameRows></div></section>"
    "<section id=packets class=view><div id=packetRows></div></section>"
    "<section id=graphs class=view><div class=meta>Recent graph history is retained on the device and sent with state.json, so the chart starts with the latest sliding window.</div>"
    "<div class=chart><h3>Temperatures</h3><p class=meta id=g1m></p><canvas id=g1></canvas></div>"
    "<div class=chart><h3>Setpoints And Limits</h3><p class=meta id=g2m></p><canvas id=g2></canvas></div>"
    "<div class=chart><h3>Differentials And Timers</h3><p class=meta id=g3m></p><canvas id=g3></canvas></div>"
    "<div class=chart><h3>Fan Values</h3><p class=meta id=g4m></p><canvas id=g4></canvas></div></section>"
    "<section class=annotate><strong>Annotate</strong> <input id=annNote placeholder='label or note'><button id=annStart>Start</button><button id=annEvent>Mark Event</button><button id=annEnd>End</button><button id=annExport>Export JSON</button><button id=annClear>Clear</button><span id=annCount class=meta></span></section>"
    "<script>"
    "const ANN_KEY='hwp.web.annotations.v1';let state={fields:[],frames:[],packets:[],graphs:{},meta:{}};let changed={};let tab='values';"
    "function anns(){try{return JSON.parse(localStorage.getItem(ANN_KEY)||'[]')}catch(e){return[]}}"
    "function saveAnns(a){localStorage.setItem(ANN_KEY,JSON.stringify(a));annCount.textContent=a.length+' annotations'}"
    "function latestPacket(){return state.packets.length?state.packets[state.packets.length-1]:null}"
    "function compact(){let p=latestPacket();return{local_time:new Date().toISOString(),uptime_ms:state.meta.uptime_ms||0,note:annNote.value,tab:tab,packet:p?{sequence:p.sequence,kind:p.kind,frame:p.frame,label:p.label}:null,changed_fields:state.fields.filter(f=>f.changed).map(f=>f.id),snapshot:{meta:state.meta,fields:state.fields,packets:state.packets.slice(-5)}}}"
    "function addAnn(type){let a=anns();a.push(Object.assign({type:type},compact()));saveAnns(a)}"
    "document.querySelectorAll('button[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('button[data-tab]').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.view').forEach(x=>x.classList.remove('active'));b.classList.add('active');tab=b.dataset.tab;document.getElementById(tab).classList.add('active');render()});"
    "annStart.onclick=()=>addAnn('start');annEvent.onclick=()=>addAnn('event');annEnd.onclick=()=>addAnn('end');annClear.onclick=()=>{if(confirm('Clear local HWP annotations?'))saveAnns([])};"
    "annExport.onclick=()=>{let data=JSON.stringify({schema:'hwp-web-annotations-v1',exported_at:new Date().toISOString(),annotations:anns()},null,2);let u=URL.createObjectURL(new Blob([data],{type:'application/json'}));let a=document.createElement('a');a.href=u;a.download='hwp-web-annotations.json';a.click();URL.revokeObjectURL(u)};"
    "function age(ms){if(!ms)return'';let base=state.meta.uptime_ms||0;let s=Math.max(0,Math.floor((base-ms)/1000));return s<60?s+'s':Math.floor(s/60)+'m '+String(s%60).padStart(2,'0')+'s'}"
    "function packetHtml(p){return`<div class=packet><div class=meta>#${p.sequence} ${age(p.seen_ms)} ${p.kind} ${p.frame} ${p.label} ${p.source} ${p.length}b ${p.checksum_valid?'ok':'<span class=bad>bad checksum</span>'}</div>[${p.bytes.map((b,i)=>`<span class='${p.changed_bytes[i]?'changed':''}'>${b.toString(16).padStart(2,'0').toUpperCase()}</span>`).join(' ')}]</div>`}"
    "function render(){document.getElementById('meta').textContent=`${state.meta.status||''} ${state.meta.bus_mode||''} ${state.meta.revision||''}`;let now=Date.now();valueRows.innerHTML=state.fields.map(f=>`<tr class='${changed[f.id]>now?'changed':''}'><td>${f.label}</td><td>${f.value} ${f.unit||''}</td><td>${age(f.seen_ms)}</td><td>${f.source}</td><td>${f.frame}</td><td>${f.raw}</td></tr>`).join('');frameRows.innerHTML=(state.frames||[]).slice().reverse().map(packetHtml).join('');packetRows.innerHTML=state.packets.slice().reverse().map(packetHtml).join('');drawGraphs()}"
    "function fmeta(){let m={};state.fields.forEach(f=>m[f.id]=f);return m}"
    "function resizeCanvas(c){let r=c.getBoundingClientRect(),d=window.devicePixelRatio||1,w=Math.max(320,Math.floor(r.width)),h=Math.max(220,Math.floor(r.height));if(c.width!==Math.floor(w*d)||c.height!==Math.floor(h*d)){c.width=Math.floor(w*d);c.height=Math.floor(h*d)}let x=c.getContext('2d');x.setTransform(d,0,0,d,0,0);return{x,w,h}}"
    "function drawOne(id,names){let c=document.getElementById(id),{x,w,h}=resizeCanvas(c),m=fmeta();x.clearRect(0,0,w,h);let series=names.map(n=>({id:n,label:(m[n]&&m[n].label)||n,unit:(m[n]&&m[n].unit)||'',p:state.graphs[n]||[]})).filter(s=>s.p.length);let note=document.getElementById(id+'m');if(!series.length){note.textContent='Waiting for retained samples from the device.';return}let vals=series.flatMap(s=>s.p.map(p=>p.value));let times=series.flatMap(s=>s.p.map(p=>p.t||p.sequence||0));let lo=Math.min(...vals),hi=Math.max(...vals),t0=Math.min(...times),t1=Math.max(...times);if(lo===hi){lo-=1;hi+=1}let pad=(hi-lo)*0.08;lo-=pad;hi+=pad;if(t0===t1)t0-=1;let l=48,r=Math.max(120,Math.min(260,w*0.32)),top=18,b=h-34,gw=w-l-r,gh=b-top;let colors=['#1d6fb8','#c45f1a','#2e7d32','#7b1fa2','#a00030','#00838f','#6d4c41','#455a64'];x.strokeStyle='#dce3eb';x.lineWidth=1;x.fillStyle='#5b6773';x.font='12px system-ui';for(let i=0;i<=4;i++){let y=top+gh*i/4;x.beginPath();x.moveTo(l,y);x.lineTo(l+gw,y);x.stroke();let v=hi-(hi-lo)*i/4;x.fillText(v.toFixed(1),6,y+4)}x.strokeStyle='#93a4b5';x.strokeRect(l,top,gw,gh);series.forEach((s,si)=>{x.strokeStyle=colors[si%colors.length];x.lineWidth=2;x.beginPath();s.p.forEach((p,i)=>{let tt=p.t||p.sequence||0,px=l+(tt-t0)*gw/(t1-t0),py=top+gh-(p.value-lo)*gh/(hi-lo);if(i)x.lineTo(px,py);else x.moveTo(px,py)});x.stroke();let last=s.p[s.p.length-1];let y=24+si*18;x.fillStyle=x.strokeStyle;x.fillRect(w-r+8,y-8,9,9);x.fillText(`${s.label}: ${last.value.toFixed(1)}${s.unit?' '+s.unit:''}`,w-r+22,y)});let span=Math.max(0,Math.round((t1-t0)/1000));note.textContent=`${series.length} series, ${span}s retained window, ${Math.max(...series.map(s=>s.p.length))} samples max`}"
    "function drawGraphs(){drawOne('g1',['t02_inlet','t03_outlet','t04_coil','t06_exhaust','t_aux_cond2']);drawOne('g2',['r01_setpoint_cooling','r02_setpoint_heating','r03_setpoint_auto','r08_min_cool_setpoint','r09_max_cooling_setpoint','r10_min_heating_setpoint','r11_max_heating_setpoint']);drawOne('g3',['r04_return_diff_cooling','r05_shutdown_temp_diff_when_cooling','r06_return_diff_heating','r07_shutdown_diff_heating','d03_defrosting_cycle_time_minutes','d04_max_defrost_time_minutes','d05_min_economy_defrost_time_minutes']);drawOne('g4',['f02_fan_high_speed_cool_setpoint','f03_fan_low_speed_temp_in_cooling_set_point','f04_fan_stop_temp_in_cooling_set_point','f05_fan_high_speed_temp_in_heating_set_point','f06_fan_low_speed_temp_in_heating_set_point','f07_fan_stop_temp_in_heating_set_point','f08_fan_low_speed_running_time','f09_fan_stop_low_speed_running_time','f12_min_fan_voltage_pct','f13_max_fan_voltage_pct'])}"
    "let base=location.pathname.replace(/\\/$/,'');"
    "async function load(){state=await fetch(base+'/state.json').then(r=>r.json());render()}"
    "saveAnns(anns());load();setInterval(render,1000);addEventListener('resize',drawGraphs);let es=new EventSource(base+'/events');es.addEventListener('state',e=>{let next=JSON.parse(e.data);if(!Object.keys(next.graphs||{}).length)next.graphs=state.graphs;state=next;state.fields.forEach(f=>{if(f.changed)changed[f.id]=Date.now()+4000});render()});"
    "</script></body></html>";

void append_json_pair(std::ostringstream& out, const char* key, const std::string& value, bool comma = true) {
    out << "\"" << key << "\":\"" << HWPWebDashboard::escape_json(value) << "\"";
    if (comma) out << ",";
}

} // namespace

#ifndef HWP_NATIVE_TEST
#ifdef USE_WEBSERVER
class HWPWebHandler : public AsyncWebHandler {
  public:
    HWPWebHandler(HWPWebDashboard* dashboard, std::string path)
        : dashboard_(dashboard), path_(std::move(path)) {}
    bool canHandle(AsyncWebServerRequest* request) const override {
        if (request->method() != HTTP_GET) return false;
        char url_buf[AsyncWebServerRequest::URL_BUF_SIZE];
        auto url = request->url_to(url_buf);
        return url == path_ || url == path_ + "/" || url == path_ + "/state.json";
    }
    void handleRequest(AsyncWebServerRequest* request) override {
        char url_buf[AsyncWebServerRequest::URL_BUF_SIZE];
        auto url = request->url_to(url_buf);
        if (url == path_ + "/state.json") {
            auto payload = dashboard_->state_json();
            request->send(200, "application/json", payload.c_str());
            return;
        }
        request->send(200, "text/html", HWPWebDashboard::index_html());
    }

  private:
    HWPWebDashboard* dashboard_;
    std::string path_;
};

void HWPWebDashboard::setup(web_server::WebServer* web_server) {
    if (!this->config_.enabled || this->handlers_registered_) return;
    auto* base = web_server_base::global_web_server_base;
    if (base == nullptr || web_server == nullptr) return;
    this->web_server_ = web_server;
    base->add_handler(new HWPWebHandler(this, this->config_.path));
    this->events_ = new web_server_idf::AsyncEventSource(this->config_.path + "/events", web_server);
    base->add_handler(this->events_);
    this->handlers_registered_ = true;
}

void HWPWebDashboard::loop() {
    if (this->events_ != nullptr) {
        this->events_->loop();
    }
    bool should_send = false;
    {
        std::lock_guard<std::mutex> lock(this->data_mutex_);
        should_send = this->dirty_ && millis() - this->last_event_ms_ >= 250;
    }
    if (this->events_ != nullptr && should_send) {
        auto payload = this->event_json();
        this->events_->try_send_nodefer(payload.c_str(), "state");
        {
            std::lock_guard<std::mutex> lock(this->data_mutex_);
            this->dirty_ = false;
            this->last_event_ms_ = millis();
        }
    }
}
#endif
#ifndef USE_WEBSERVER
void HWPWebDashboard::loop() {}
#endif
#endif

void HWPWebDashboard::record_packet(const BaseFrame& frame, const std::string& kind) {
    if (!this->config_.enabled) return;
    PacketRecord record;
    record.sequence = ++this->packet_sequence_;
    record.seen_ms = millis();
    record.kind = kind;
    record.label = frame.type_string();
    record.source = frame_source_to_string(frame.get_source());
    record.frame = "0x" + std::string(BaseFrame::format_hex(frame.packet.data[0]));
    record.length = frame.packet.data_len;
    record.checksum_valid = frame.packet.is_checksum_valid();
    record.changed = frame.is_changed();
    record.formatted = frame.header_format(kind, false) + frame.format();
    record.bytes.reserve(frame.packet.data_len);
    for (size_t i = 0; i < frame.packet.data_len; i++) {
        record.bytes.push_back(frame.packet.data[i]);
    }
    auto key = bytes_to_key(frame);
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    auto previous = this->previous_packet_bytes_.find(key);
    for (size_t i = 0; i < record.bytes.size(); i++) {
        record.changed_bytes.push_back(previous != this->previous_packet_bytes_.end() &&
                                       (i >= previous->second.size() || previous->second[i] != record.bytes[i]));
    }
    this->previous_packet_bytes_[key] = record.bytes;
    this->packets_.push_back(record);
    this->latest_frames_[key] = record;
    this->trim_packets();
    this->dirty_ = true;
}

const char* HWPWebDashboard::index_html() {
    return HWP_WEB_INDEX;
}

void HWPWebDashboard::update_fields(
    const heat_pump_data_t& data, const std::string& status, bus_mode_t bus_mode) {
    if (!this->config_.enabled) return;
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    if (!status.empty()) {
        this->last_status_ = status;
    }
    this->last_bus_mode_ = bus_mode;
    std::vector<HWPWebField> fields;
    append_field(fields, make_string_field("actual_status", "Actual Status", status, "status", "", "", "local"));
    append_field(fields, make_string_field("bus_mode", "Bus Mode", bus_mode_to_string(bus_mode), "status", "", "", "local"));
    append_field(fields, make_float_field("t02_inlet", "T02 Inlet", data.t02_temperature_inlet, "C", "temperatures", "COND_1B", "D1[9]", "heater"));
    append_field(fields, make_float_field("t03_outlet", "T03 Outlet", data.t03_temperature_outlet, "C", "temperatures", "COND_2", "D2[3]", "heater"));
    append_field(fields, make_float_field("t04_coil", "T04 Coil", data.t04_temperature_coil, "C", "temperatures", "COND_2", "D2[5]", "heater"));
    append_field(fields, make_float_field("t06_exhaust", "T06 Exhaust", data.t06_temperature_exhaust, "C", "temperatures", "COND_2", "D2[4]", "heater"));
    append_field(fields, make_float_field("r01_setpoint_cooling", "R01 Cooling Setpoint", data.r01_setpoint_cooling, "C", "setpoints", "CONFIG_1", "81[3]", "heater"));
    append_field(fields, make_float_field("r02_setpoint_heating", "R02 Heating Setpoint", data.r02_setpoint_heating, "C", "setpoints", "CONFIG_1", "81[4]", "heater"));
    append_field(fields, make_float_field("r03_setpoint_auto", "R03 Auto Setpoint", data.r03_setpoint_auto, "C", "setpoints", "CONFIG_1", "81[5]", "heater"));
    append_field(fields, make_float_field("r04_return_diff_cooling", "R04 Return Diff Cooling", data.r04_return_diff_cooling, "C", "low_range", "CONFIG_1", "81[6]", "heater"));
    append_field(fields, make_float_field("r05_shutdown_temp_diff_when_cooling", "R05 Shutdown Diff Cooling", data.r05_shutdown_temp_diff_when_cooling, "C", "low_range", "CONFIG_1", "81[7]", "heater"));
    append_field(fields, make_float_field("r06_return_diff_heating", "R06 Return Diff Heating", data.r06_return_diff_heating, "C", "low_range", "CONFIG_1", "81[8]", "heater"));
    append_field(fields, make_float_field("r07_shutdown_diff_heating", "R07 Shutdown Diff Heating", data.r07_shutdown_diff_heating, "C", "low_range", "CONFIG_1", "81[9]", "heater"));
    append_field(fields, make_float_field("r08_min_cool_setpoint", "R08 Min Cool Setpoint", data.r08_min_cool_setpoint, "C", "setpoints", "CONFIG_3", "83[7]", "heater"));
    append_field(fields, make_float_field("r09_max_cooling_setpoint", "R09 Max Cool Setpoint", data.r09_max_cooling_setpoint, "C", "setpoints", "CONFIG_3", "83[8]", "heater"));
    append_field(fields, make_float_field("r10_min_heating_setpoint", "R10 Min Heat Setpoint", data.r10_min_heating_setpoint, "C", "setpoints", "CONFIG_3", "83[9]", "heater"));
    append_field(fields, make_float_field("r11_max_heating_setpoint", "R11 Max Heat Setpoint", data.r11_max_heating_setpoint, "C", "setpoints", "CONFIG_3", "83[10]", "heater"));
    append_field(fields, make_float_field("d01_defrost_start", "D01 Defrost Start", data.d01_defrost_start, "C", "low_range", "CONFIG_2", "82[3]", "heater"));
    append_field(fields, make_float_field("d02_defrost_end", "D02 Defrost End", data.d02_defrost_end, "C", "low_range", "CONFIG_2", "82[4]", "heater"));
    append_field(fields, make_float_field("d03_defrosting_cycle_time_minutes", "D03 Defrost Cycle", data.d03_defrosting_cycle_time_minutes, "min", "low_range", "CONFIG_2", "82[5]", "heater"));
    append_field(fields, make_float_field("d04_max_defrost_time_minutes", "D04 Max Defrost", data.d04_max_defrost_time_minutes, "min", "low_range", "CONFIG_2", "82[6]", "heater"));
    append_field(fields, make_float_field("d05_min_economy_defrost_time_minutes", "D05 Min Eco Defrost", data.d05_min_economy_defrost_time_minutes, "min", "low_range", "CONFIG_5", "85[3]", "heater"));
    if (data.d06_defrost_eco_mode.has_value()) append_field(fields, make_string_field("d06_defrost_eco_mode", "D06 Defrost Eco Mode", data.d06_defrost_eco_mode->to_string(), "low_range", "CONFIG_5", "85[2].6", "heater"));
    if (data.S02_water_flow.has_value()) append_field(fields, make_string_field("s02_water_flow", "S02 Water Flow", data.S02_water_flow.value() ? "FLOWING" : "NO FLOW", "status", "COND_1B", "D1[4].1", "heater"));
    if (data.U01_flow_meter.has_value()) append_field(fields, make_string_field("u01_flow_meter", "U01 Flow Meter", data.U01_flow_meter->to_string(), "status", "CONFIG_5", "85[2].5", "heater"));
    append_field(fields, make_float_field("u02_pulses_per_liter", "U02 Pulses/L", data.U02_pulses_per_liter, "", "low_range", "CONFIG_5", "85[10]", "heater"));
    if (data.fan_mode.has_value()) append_field(fields, make_string_field("f01_fan_mode", "F01 Fan Mode", data.fan_mode->to_string(), "fan", "CONFIG_2", "82[2].4-7", "heater"));
    append_field(fields, make_float_field("f02_fan_high_speed_cool_setpoint", "F02 High Cool", data.f02_fan_high_speed_cool_setpoint, "C", "fan", "CONFIG_4", "84[2]", "heater"));
    append_field(fields, make_float_field("f03_fan_low_speed_temp_in_cooling_set_point", "F03 Low Cool", data.f03_fan_low_speed_temp_in_cooling_set_point, "C", "fan", "CONFIG_4", "84[3]", "heater"));
    append_field(fields, make_float_field("f04_fan_stop_temp_in_cooling_set_point", "F04 Stop Cool", data.f04_fan_stop_temp_in_cooling_set_point, "C", "fan", "CONFIG_4", "84[4]", "heater"));
    append_field(fields, make_float_field("f05_fan_high_speed_temp_in_heating_set_point", "F05 High Heat", data.f05_fan_high_speed_temp_in_heating_set_point, "C", "fan", "CONFIG_4", "84[5]", "heater"));
    append_field(fields, make_float_field("f06_fan_low_speed_temp_in_heating_set_point", "F06 Low Heat", data.f06_fan_low_speed_temp_in_heating_set_point, "C", "fan", "CONFIG_4", "84[6]", "heater"));
    append_field(fields, make_float_field("f07_fan_stop_temp_in_heating_set_point", "F07 Stop Heat", data.f07_fan_stop_temp_in_heating_set_point, "C", "fan", "CONFIG_4", "84[7]", "heater"));
    append_field(fields, make_float_field("f08_fan_low_speed_running_time", "F08 Low Run", data.f08_fan_low_speed_running_time, "min", "low_range", "CONFIG_4", "84[8]", "heater"));
    append_field(fields, make_float_field("f09_fan_stop_low_speed_running_time", "F09 Stop Low Run", data.f09_fan_stop_low_speed_running_time, "min", "low_range", "CONFIG_4", "84[9]", "heater"));
    if (data.f10_fan_speed_control_temp.has_value()) append_field(fields, make_string_field("f10_fan_speed_control_temp", "F10 Fan Speed Source", data.f10_fan_speed_control_temp->to_string(), "fan", "CONFIG_2", "82[2].3", "heater"));
    if (data.f11_speed_control_module.has_value()) append_field(fields, make_string_field("f11_speed_control_module", "F11 Speed Control", data.f11_speed_control_module->to_string(), "fan", "CONFIG_5", "85[2].4", "heater"));
    append_field(fields, make_float_field("f12_min_fan_voltage_pct", "F12 Min Fan Voltage", data.f12_min_fan_voltage_pct, "%", "low_range", "CONFIG_1", "81[10]", "heater"));
    append_field(fields, make_float_field("f13_max_fan_voltage_pct", "F13 Max Fan Voltage", data.f13_max_fan_voltage_pct, "%", "low_range", "CONFIG_2", "82[10]", "heater"));

    std::map<std::string, bool> seen_fields;
    for (const auto& field : fields) {
        seen_fields[field.id] = true;
    }
    for (const auto& previous : this->fields_) {
        if (!previous.id.empty() && seen_fields.find(previous.id) == seen_fields.end()) {
            auto retained = previous;
            retained.changed = false;
            fields.push_back(retained);
        }
    }
    this->fields_ = fields;
    this->dirty_ = true;
}

void HWPWebDashboard::append_field(std::vector<HWPWebField>& fields, HWPWebField field) {
    if (field.id.empty()) return;
    auto previous = this->previous_field_values_.find(field.id);
    field.changed = previous != this->previous_field_values_.end() && previous->second != field.value;
    field.seen_ms = millis();
    this->previous_field_values_[field.id] = field.value;
    fields.push_back(field);
    this->append_graph_point(field);
}

std::string HWPWebDashboard::state_json() const {
    return this->state_json_(true);
}

std::string HWPWebDashboard::event_json() const {
    return this->state_json_(false);
}

std::string HWPWebDashboard::state_json_(bool include_graphs) const {
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    std::ostringstream out;
    out << "{";
    out << "\"meta\":" << meta_json(this->last_status_, this->last_bus_mode_) << ",";
    out << "\"fields\":" << fields_json() << ",";
    out << "\"frames\":" << frames_json() << ",";
    out << "\"packets\":" << packets_json();
    if (include_graphs) {
        out << ",\"graphs\":" << graph_json();
    } else {
        out << ",\"graphs\":{}";
    }
    out << "}";
    return out.str();
}

size_t HWPWebDashboard::packet_count() const {
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    return this->packets_.size();
}

size_t HWPWebDashboard::latest_frame_count() const {
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    return this->latest_frames_.size();
}

std::string HWPWebDashboard::fields_json() const {
    std::ostringstream out;
    out << "[";
    for (size_t i = 0; i < this->fields_.size(); i++) {
        const auto& field = this->fields_[i];
        if (i) out << ",";
        out << "{";
        append_json_pair(out, "id", field.id);
        append_json_pair(out, "label", field.label);
        append_json_pair(out, "value", field.value);
        append_json_pair(out, "unit", field.unit);
        append_json_pair(out, "group", field.group);
        append_json_pair(out, "frame", field.frame);
        append_json_pair(out, "raw", field.raw_location);
        append_json_pair(out, "source", field.source);
        out << "\"numeric\":" << bool_json(field.numeric) << ",";
        out << "\"numeric_value\":" << field.numeric_value << ",";
        out << "\"changed\":" << bool_json(field.changed) << ",";
        out << "\"seen_ms\":" << field.seen_ms;
        out << "}";
    }
    out << "]";
    return out.str();
}

std::string HWPWebDashboard::packets_json() const {
    std::ostringstream out;
    out << "[";
    for (size_t i = 0; i < this->packets_.size(); i++) {
        if (i) out << ",";
        append_packet_json(out, this->packets_[i]);
    }
    out << "]";
    return out.str();
}

std::string HWPWebDashboard::frames_json() const {
    std::ostringstream out;
    out << "[";
    size_t index = 0;
    for (const auto& entry : this->latest_frames_) {
        if (index++) out << ",";
        append_packet_json(out, entry.second);
    }
    out << "]";
    return out.str();
}

void HWPWebDashboard::append_packet_json(std::ostringstream& out, const PacketRecord& packet) {
    out << "{";
    out << "\"sequence\":" << packet.sequence << ",";
    out << "\"seen_ms\":" << packet.seen_ms << ",";
    append_json_pair(out, "kind", packet.kind);
    append_json_pair(out, "label", packet.label);
    append_json_pair(out, "source", packet.source);
    append_json_pair(out, "frame", packet.frame);
    out << "\"length\":" << packet.length << ",";
    out << "\"checksum_valid\":" << bool_json(packet.checksum_valid) << ",";
    out << "\"changed\":" << bool_json(packet.changed) << ",";
    out << "\"bytes\":" << bytes_to_json(packet.bytes) << ",";
    out << "\"changed_bytes\":[";
    for (size_t j = 0; j < packet.changed_bytes.size(); j++) {
        if (j) out << ",";
        out << bool_json(packet.changed_bytes[j]);
    }
    out << "]";
    out << "}";
}

std::string HWPWebDashboard::graph_json() const {
    std::ostringstream out;
    out << "{";
    size_t field_index = 0;
    for (const auto& entry : this->graph_history_) {
        if (field_index++) out << ",";
        out << "\"" << escape_json(entry.first) << "\":[";
        for (size_t i = 0; i < entry.second.size(); i++) {
            if (i) out << ",";
            out << "{\"sequence\":" << entry.second[i].sequence << ",\"t\":"
                << entry.second[i].seen_ms << ",\"value\":" << entry.second[i].value << "}";
        }
        out << "]";
    }
    out << "}";
    return out.str();
}

std::string HWPWebDashboard::meta_json(const std::string& status, bus_mode_t bus_mode) const {
    std::ostringstream out;
    out << "{";
    append_json_pair(out, "revision", HWP_COMPONENT_VERSION);
    append_json_pair(out, "status", status);
    append_json_pair(out, "bus_mode", bus_mode_to_string(bus_mode));
    out << "\"uptime_ms\":" << millis();
    out << "}";
    return out.str();
}

void HWPWebDashboard::append_graph_point(const HWPWebField& field) {
    if (!field.numeric) return;
    auto& points = this->graph_history_[field.id];
    points.push_back(GraphPoint{++this->field_sequence_, field.seen_ms, field.numeric_value});
    trim_graph(field.id);
}

void HWPWebDashboard::trim_packets() {
    if (this->packets_.size() > this->config_.packet_buffer_size) {
        this->packets_.erase(this->packets_.begin(),
            this->packets_.begin() + (this->packets_.size() - this->config_.packet_buffer_size));
    }
}

void HWPWebDashboard::trim_graph(const std::string& field_id) {
    auto& points = this->graph_history_[field_id];
    if (points.size() > this->config_.graph_history_size) {
        points.erase(points.begin(), points.begin() + (points.size() - this->config_.graph_history_size));
    }
}

size_t HWPWebDashboard::graph_point_count(const std::string& field_id) const {
    std::lock_guard<std::mutex> lock(this->data_mutex_);
    auto found = this->graph_history_.find(field_id);
    return found == this->graph_history_.end() ? 0 : found->second.size();
}

HWPWebField HWPWebDashboard::make_float_field(const char* id, const char* label,
    optional<float> value, const char* unit, const char* group, const char* frame,
    const char* raw_location, const char* source) {
    if (!value.has_value()) return {};
    char formatted[24];
    snprintf(formatted, sizeof(formatted), "%.1f", value.value());
    return HWPWebField{id, label, formatted, unit, group, frame, raw_location, source, true,
        value.value(), false, 0};
}

HWPWebField HWPWebDashboard::make_string_field(const char* id, const char* label,
    const std::string& value, const char* group, const char* frame, const char* raw_location,
    const char* source) {
    return HWPWebField{id, label, value, "", group, frame, raw_location, source, false, 0.0f,
        false, 0};
}

std::string HWPWebDashboard::escape_json(const std::string& value) {
    std::string escaped;
    for (char ch : value) {
        switch (ch) {
        case '"': escaped += "\\\""; break;
        case '\\': escaped += "\\\\"; break;
        case '\n': escaped += "\\n"; break;
        case '\r': escaped += "\\r"; break;
        case '\t': escaped += "\\t"; break;
        default:
            if (static_cast<unsigned char>(ch) >= 0x20) escaped += ch;
        }
    }
    return escaped;
}

std::string HWPWebDashboard::bus_mode_to_string(bus_mode_t mode) {
    switch (mode) {
    case BUSMODE_TX: return "TX";
    case BUSMODE_RX: return "RX";
    case BUSMODE_ERROR: return "ERROR";
    }
    return "UNKNOWN";
}

std::string HWPWebDashboard::frame_source_to_string(frame_source_t source) {
    switch (source) {
    case SOURCE_HEATER: return "heater";
    case SOURCE_CONTROLLER: return "controller";
    case SOURCE_LOCAL: return "local";
    case SOURCE_UNKNOWN: return "unknown";
    }
    return "unknown";
}

std::string HWPWebDashboard::bytes_to_key(const BaseFrame& frame) {
    std::ostringstream out;
    out << static_cast<int>(frame.packet.data[0]) << ":" << frame_source_to_string(frame.get_source())
        << ":" << frame.packet.data_len;
    return out.str();
}

std::string HWPWebDashboard::bytes_to_json(const std::vector<uint8_t>& bytes) {
    std::ostringstream out;
    out << "[";
    for (size_t i = 0; i < bytes.size(); i++) {
        if (i) out << ",";
        out << static_cast<int>(bytes[i]);
    }
    out << "]";
    return out.str();
}

} // namespace hwp
} // namespace esphome
