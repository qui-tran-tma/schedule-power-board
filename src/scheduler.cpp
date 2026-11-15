#include "scheduler.h"

#include <Arduino.h>
#include <Preferences.h>
#include <esp_attr.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#include <array>

#include "button.h"
#include "clock_sync.h"
#include "power.h"
#include "relay.h"

namespace scheduler {
namespace {

constexpr const char* kNamespace = "sched";
constexpr const char* kKey = "v1";  // bump if Slot layout changes

struct Slot {
  bool used;
  Entry entry;
};

std::array<Slot, kMaxSchedules> g_slots{};
// Local minute each slot last fired, so a clock resync inside the same minute never re-fires.
// RTC memory so a deep-sleep wake inside the same minute never re-fires.
RTC_DATA_ATTR std::array<int64_t, kMaxSchedules> g_lastFired{};
RTC_DATA_ATTR int64_t g_lastMinute = -1;

// set/remove/get run on the NimBLE host task, tick() on the loop task.
SemaphoreHandle_t g_lock = nullptr;

struct Guard {
  Guard() { xSemaphoreTake(g_lock, portMAX_DELAY); }
  ~Guard() { xSemaphoreGive(g_lock); }
  Guard(const Guard&) = delete;
  Guard& operator=(const Guard&) = delete;
};

bool validSlot(uint32_t id) { return id >= 1 && id <= kMaxSchedules; }

bool validEntry(const Entry& e) {
  if (e.minuteOfDay >= 24 * 60 || e.weekdays > kAllDays) return false;
  switch (e.action) {
    case ActionType::kRelay:
      return e.channel >= 1 && e.channel <= relay::kChannelCount;
    case ActionType::kPress:
      return button::validate(e.buttonId, e.pressCount, e.holdMs, e.gapMs) == button::Result::kOk;
    case ActionType::kNone:
      break;
  }
  return false;
}

// Caller holds g_lock.
bool save() {
  if (kMaxSchedules == 0) return true;
  Preferences prefs;
  if (!prefs.begin(kNamespace, false)) return false;
  const size_t n = prefs.putBytes(kKey, g_slots.data(), sizeof(g_slots));
  prefs.end();
  return n == sizeof(g_slots);
}

void run(size_t i, const Entry& e) {
  log_i("schedule %u fired", static_cast<unsigned>(i + 1));
  if (e.action == ActionType::kRelay) {
    relay::setPower(e.channel, e.powerOn);
  } else if (e.action == ActionType::kPress) {
    const button::Result r = button::press(e.buttonId, e.pressCount, e.holdMs, e.gapMs);
    if (r != button::Result::kOk) log_w("schedule %u press skipped (%d)", i + 1, static_cast<int>(r));
  }
}

}  // namespace

void begin() {
  g_lock = xSemaphoreCreateMutex();
  if (!power::wokeFromSleep()) {
    g_lastFired.fill(-1);
    g_lastMinute = -1;
  }
  if (kMaxSchedules == 0) return;
  Preferences prefs;
  if (!prefs.begin(kNamespace, true)) return;  // namespace absent on first boot
  if (prefs.getBytesLength(kKey) == sizeof(g_slots)) {
    prefs.getBytes(kKey, g_slots.data(), sizeof(g_slots));
    for (auto& s : g_slots) {
      if (s.used && !validEntry(s.entry)) s = Slot{};  // drop anything corrupt
    }
  }
  prefs.end();
  log_i("schedules loaded, mask 0x%08x", static_cast<unsigned>(usedMask()));
}

Result set(uint32_t id, const Entry& entry) {
  if (kMaxSchedules == 0) return Result::kUnsupported;
  if (!validSlot(id)) return Result::kBadSlot;
  if (!validEntry(entry)) return Result::kBadEntry;
  Guard guard;
  g_slots[id - 1] = Slot{true, entry};
  g_lastFired[id - 1] = -1;
  return save() ? Result::kOk : Result::kStorage;
}

Result remove(uint32_t id) {
  if (kMaxSchedules == 0) return Result::kUnsupported;
  if (!validSlot(id)) return Result::kBadSlot;
  Guard guard;
  if (!g_slots[id - 1].used) return Result::kEmpty;
  g_slots[id - 1] = Slot{};
  return save() ? Result::kOk : Result::kStorage;
}

Result get(uint32_t id, Entry& out) {
  if (kMaxSchedules == 0) return Result::kUnsupported;
  if (!validSlot(id)) return Result::kBadSlot;
  Guard guard;
  if (!g_slots[id - 1].used) return Result::kEmpty;
  out = g_slots[id - 1].entry;
  return Result::kOk;
}

uint32_t usedMask() {
  if (kMaxSchedules == 0) return 0;
  Guard guard;
  uint32_t mask = 0;
  for (size_t i = 0; i < kMaxSchedules; ++i) {
    if (g_slots[i].used) mask |= 1UL << i;
  }
  return mask;
}

bool tick() {
  if (kMaxSchedules == 0) return false;
  struct tm now{};
  int64_t minuteKey = 0;
  if (!clock_sync::localNow(now, minuteKey) || minuteKey == g_lastMinute) return false;
  g_lastMinute = minuteKey;

  const uint16_t minuteOfDay = now.tm_hour * 60 + now.tm_min;
  const uint8_t dayBit = 1U << ((now.tm_wday + 6) % 7);  // tm_wday 0 = Sunday

  bool fired = false;
  bool dirty = false;
  Guard guard;
  for (size_t i = 0; i < kMaxSchedules; ++i) {
    Slot& s = g_slots[i];
    if (!s.used || !s.entry.enabled || s.entry.minuteOfDay != minuteOfDay) continue;
    if (s.entry.weekdays != 0 && !(s.entry.weekdays & dayBit)) continue;
    if (g_lastFired[i] == minuteKey) continue;
    g_lastFired[i] = minuteKey;
    run(i, s.entry);
    fired = true;
    if (s.entry.weekdays == 0) {  // one-shot: done
      s.entry.enabled = false;
      dirty = true;
    }
  }
  if (dirty && !save()) log_e("schedule save failed");
  return fired;
}

int64_t secondsUntilNext() {
  if (kMaxSchedules == 0) return -1;
  struct tm now{};
  int64_t minuteKey = 0;
  if (!clock_sync::localNow(now, minuteKey)) return -1;
  const int64_t nowMinute = now.tm_hour * 60 + now.tm_min;
  const int today = (now.tm_wday + 6) % 7;  // 0 = Monday

  int64_t best = -1;
  Guard guard;
  for (size_t i = 0; i < kMaxSchedules; ++i) {
    const Slot& s = g_slots[i];
    if (!s.used || !s.entry.enabled) continue;
    // Search today .. same weekday next week (d = 7 covers "today, but time already passed").
    for (int d = 0; d <= 7; ++d) {
      const int64_t deltaMin = d * 24 * 60 + s.entry.minuteOfDay - nowMinute;
      if (deltaMin < 0) continue;
      if (deltaMin == 0 && g_lastFired[i] == minuteKey) continue;  // already ran this minute
      const int day = (today + d) % 7;
      if (s.entry.weekdays != 0 && !(s.entry.weekdays & (1U << day))) continue;
      int64_t secs = deltaMin * 60 - now.tm_sec;
      if (secs < 0) secs = 0;
      if (best < 0 || secs < best) best = secs;
      break;
    }
  }
  return best;
}

}  // namespace scheduler
