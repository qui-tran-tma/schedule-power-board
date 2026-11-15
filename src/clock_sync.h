#pragma once

#include <stdint.h>
#include <time.h>

// Wall clock set by the app (SetTime). No RTC battery or Wi-Fi: unset after every boot
// until the app connects. Survives deep sleep (RTC timer), but drifts on the internal RC
// oscillator, so each app connect resyncs it. UTC offset is persisted in NVS.
namespace clock_sync {

void begin();

// Returns false if unixS is implausible (before 2024).
bool set(uint64_t unixS, int32_t utcOffsetMin);
bool isSet();
uint64_t unixNow();  // UTC seconds, 0 if not set
int32_t utcOffsetMin();

// Local broken-down time. False if clock not set.
bool localNow(struct tm& out, int64_t& localMinuteKey);

}  // namespace clock_sync
