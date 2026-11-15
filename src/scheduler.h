#pragma once

#include <stddef.h>
#include <stdint.h>

#include "config.h"

// Time-of-day schedules, persisted in NVS, run on the board (phone can be away).
// Slot ids are 1-based (1..kMaxSchedules). Pure C++ types; protocol.cpp maps protobuf.
namespace scheduler {

constexpr size_t kMaxSchedules = config::kMaxSchedules;
constexpr uint8_t kAllDays = 0x7F;  // bit 0 = Monday ... bit 6 = Sunday

enum class ActionType : uint8_t { kNone, kRelay, kPress };

struct Entry {
  bool enabled = false;
  uint16_t minuteOfDay = 0;  // 0..1439 local
  uint8_t weekdays = 0;      // 0 = one-shot
  ActionType action = ActionType::kNone;
  // kRelay
  uint8_t channel = 0;
  bool powerOn = false;
  // kPress
  uint8_t buttonId = 0;
  uint8_t pressCount = 0;
  uint16_t holdMs = 0;
  uint16_t gapMs = 0;
};

enum class Result : uint8_t { kOk, kUnsupported, kBadSlot, kEmpty, kBadEntry, kStorage };

void begin();

Result set(uint32_t id, const Entry& entry);
Result remove(uint32_t id);
Result get(uint32_t id, Entry& out);
uint32_t usedMask();

// Fire due schedules. Call from loop(). Returns true if anything fired.
bool tick();

// Seconds until the next enabled schedule fires (0 = due now), -1 if none or clock unset.
int64_t secondsUntilNext();

}  // namespace scheduler
