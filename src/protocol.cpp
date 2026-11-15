#include "protocol.h"

#include <Arduino.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include <string.h>

#include "button.h"
#include "clock_sync.h"
#include "config.h"
#include "power_board.pb.h"
#include "relay.h"
#include "scheduler.h"

namespace protocol {
namespace {

static_assert(powerboard_Response_size <= kMaxFrame, "Response can outgrow kMaxFrame");
static_assert(powerboard_Request_size <= kMaxFrame, "Request can outgrow kMaxFrame");
static_assert(config::kRelayCount <= 3, "Status.relays max_count is 3 in power_board.options");
static_assert(config::kProfile == powerboard_Profile_PROFILE_POWER_BOARD ||
                  config::kProfile == powerboard_Profile_PROFILE_BUTTON_TESTER ||
                  config::kProfile == powerboard_Profile_PROFILE_SCHEDULED_BUTTON,
              "config.h profile ids must match powerboard.Profile");

void fillStatus(powerboard_Status& s) {
  s.relays_count = relay::kChannelCount;
  for (size_t i = 0; i < relay::kChannelCount; ++i) {
    const uint8_t ch = i + 1;
    s.relays[i].channel = static_cast<powerboard_Channel>(ch);
    s.relays[i].power_on = relay::isPowerOn(ch);
  }
  s.uptime_s = millis() / 1000;
  s.buttons_count = button::count();
  for (size_t i = 0; i < button::count(); ++i) {
    s.buttons[i].button_id = i + 1;
    s.buttons[i].pressing = button::isPressing(i + 1);
  }
  s.unix_s = clock_sync::unixNow();
  s.schedule_mask = scheduler::usedMask();
  s.utc_offset_min = clock_sync::utcOffsetMin();
}

void fillInfo(powerboard_DeviceInfo& info) {
  info.profile = static_cast<powerboard_Profile>(config::kProfile);
  strncpy(info.fw_version, FW_VERSION, sizeof(info.fw_version) - 1);
  info.relay_count = config::kRelayCount;
  info.button_count = config::kButtonCount;
  info.max_schedules = config::kMaxSchedules;
  if (config::kLowPower) {
    info.sleep_interval_s = config::kSleepIntervalS;
    info.awake_window_ms = config::kAdvWindowMs;
    info.idle_disconnect_s = config::kIdleDisconnectS;
  }
}

powerboard_ErrorCode toError(button::Result r) {
  switch (r) {
    case button::Result::kOk:
      return powerboard_ErrorCode_ERROR_NONE;
    case button::Result::kBadButton:
      return button::count() == 0 ? powerboard_ErrorCode_ERROR_UNSUPPORTED
                                  : powerboard_ErrorCode_ERROR_BAD_BUTTON;
    case button::Result::kBadArgs:
      return powerboard_ErrorCode_ERROR_BAD_ARGS;
    case button::Result::kBusy:
      return powerboard_ErrorCode_ERROR_BUSY;
  }
  return powerboard_ErrorCode_ERROR_UNKNOWN_REQUEST;
}

powerboard_ErrorCode toError(scheduler::Result r) {
  switch (r) {
    case scheduler::Result::kOk:
      return powerboard_ErrorCode_ERROR_NONE;
    case scheduler::Result::kUnsupported:
      return powerboard_ErrorCode_ERROR_UNSUPPORTED;
    case scheduler::Result::kBadSlot:
    case scheduler::Result::kEmpty:
    case scheduler::Result::kBadEntry:
      return powerboard_ErrorCode_ERROR_BAD_SCHEDULE;
    case scheduler::Result::kStorage:
      return powerboard_ErrorCode_ERROR_STORAGE;
  }
  return powerboard_ErrorCode_ERROR_UNKNOWN_REQUEST;
}

// protobuf -> scheduler entry. False if the action is missing or fields overflow.
bool toEntry(const powerboard_Schedule& in, scheduler::Entry& out) {
  if (in.minute_of_day > 0xFFFF || in.weekdays > 0xFF) return false;
  out.enabled = in.enabled;
  out.minuteOfDay = in.minute_of_day;
  out.weekdays = in.weekdays;
  switch (in.which_action) {
    case powerboard_Schedule_relay_tag:
      out.action = scheduler::ActionType::kRelay;
      out.channel = in.action.relay.channel;
      out.powerOn = in.action.relay.power_on;
      return true;
    case powerboard_Schedule_press_tag: {
      const powerboard_PressButton& p = in.action.press;
      if (p.button_id > 0xFF || p.press_count > 0xFF || p.hold_ms > 0xFFFF || p.gap_ms > 0xFFFF) {
        return false;
      }
      out.action = scheduler::ActionType::kPress;
      out.buttonId = p.button_id;
      out.pressCount = p.press_count;
      out.holdMs = p.hold_ms;
      out.gapMs = p.gap_ms;
      return true;
    }
    default:
      return false;
  }
}

void fromEntry(uint32_t id, const scheduler::Entry& in, powerboard_Schedule& out) {
  out.id = id;
  out.enabled = in.enabled;
  out.minute_of_day = in.minuteOfDay;
  out.weekdays = in.weekdays;
  if (in.action == scheduler::ActionType::kRelay) {
    out.which_action = powerboard_Schedule_relay_tag;
    out.action.relay.channel = static_cast<powerboard_Channel>(in.channel);
    out.action.relay.power_on = in.powerOn;
  } else if (in.action == scheduler::ActionType::kPress) {
    out.which_action = powerboard_Schedule_press_tag;
    out.action.press.button_id = in.buttonId;
    out.action.press.press_count = in.pressCount;
    out.action.press.hold_ms = in.holdMs;
    out.action.press.gap_ms = in.gapMs;
  }
}

// Fills resp.payload for one decoded request; leaves which_payload 0 for "send status".
void dispatch(const powerboard_Request& req, powerboard_Response& resp) {
  switch (req.which_payload) {
    case powerboard_Request_get_info_tag:
      resp.which_payload = powerboard_Response_info_tag;
      fillInfo(resp.payload.info);
      break;

    case powerboard_Request_get_status_tag:
      break;

    case powerboard_Request_set_relay_tag:
      if (relay::kChannelCount == 0) {
        resp.error = powerboard_ErrorCode_ERROR_UNSUPPORTED;
      } else if (!relay::setPower(req.payload.set_relay.channel, req.payload.set_relay.power_on)) {
        resp.error = powerboard_ErrorCode_ERROR_BAD_CHANNEL;
      }
      break;

    case powerboard_Request_press_button_tag: {
      const powerboard_PressButton& p = req.payload.press_button;
      resp.error = toError(button::press(p.button_id, p.press_count, p.hold_ms, p.gap_ms));
      break;
    }

    case powerboard_Request_stop_button_tag:
      resp.error = toError(button::stop(req.payload.stop_button.button_id));
      break;

    case powerboard_Request_set_time_tag:
      if (!clock_sync::set(req.payload.set_time.unix_s, req.payload.set_time.utc_offset_min)) {
        resp.error = powerboard_ErrorCode_ERROR_BAD_ARGS;
      }
      break;

    case powerboard_Request_set_schedule_tag: {
      const powerboard_SetSchedule& s = req.payload.set_schedule;
      scheduler::Entry entry;
      if (config::kMaxSchedules == 0) {
        resp.error = powerboard_ErrorCode_ERROR_UNSUPPORTED;
      } else if (!s.has_schedule || !toEntry(s.schedule, entry)) {
        resp.error = powerboard_ErrorCode_ERROR_BAD_SCHEDULE;
      } else {
        resp.error = toError(scheduler::set(s.schedule.id, entry));
      }
      break;
    }

    case powerboard_Request_delete_schedule_tag:
      resp.error = toError(scheduler::remove(req.payload.delete_schedule.id));
      break;

    case powerboard_Request_get_schedule_tag: {
      const uint32_t id = req.payload.get_schedule.id;
      scheduler::Entry entry;
      resp.error = toError(scheduler::get(id, entry));
      if (resp.error == powerboard_ErrorCode_ERROR_NONE) {
        resp.which_payload = powerboard_Response_schedule_tag;
        fromEntry(id, entry, resp.payload.schedule);
      }
      break;
    }

    default:
      resp.error = powerboard_ErrorCode_ERROR_UNKNOWN_REQUEST;
      break;
  }
}

size_t encode(powerboard_Response& resp, uint8_t* out, size_t outCap) {
  if (resp.which_payload == 0) {
    // Default payload: current status so the app stays in sync.
    resp.which_payload = powerboard_Response_status_tag;
    fillStatus(resp.payload.status);
  }
  pb_ostream_t os = pb_ostream_from_buffer(out, outCap);
  if (!pb_encode(&os, powerboard_Response_fields, &resp)) {
    log_e("encode failed: %s", PB_GET_ERROR(&os));
    return 0;
  }
  return os.bytes_written;
}

}  // namespace

size_t handle(const uint8_t* in, size_t inLen, uint8_t* out, size_t outCap) {
  powerboard_Request req = powerboard_Request_init_zero;
  powerboard_Response resp = powerboard_Response_init_zero;

  pb_istream_t is = pb_istream_from_buffer(in, inLen);
  if (!pb_decode(&is, powerboard_Request_fields, &req)) {
    log_w("decode failed: %s", PB_GET_ERROR(&is));
    resp.error = powerboard_ErrorCode_ERROR_DECODE;
  } else {
    resp.seq = req.seq;
    dispatch(req, resp);
  }
  return encode(resp, out, outCap);
}

size_t encodeStatus(uint8_t* out, size_t outCap) {
  powerboard_Response resp = powerboard_Response_init_zero;
  return encode(resp, out, outCap);
}

}  // namespace protocol
