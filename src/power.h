#pragma once

#include <stdint.h>

// Battery mode (config::kLowPower). While no app is connected the board deep-sleeps,
// wakes on a timer, advertises for a short window and sleeps again. It sleeps at most
// config::kSleepIntervalS, less when a schedule is due sooner.
// Deep sleep resets the CPU: setup() runs again on every wake. State that must survive
// lives in RTC memory (RTC_DATA_ATTR) and output pins are latched with gpio hold.
namespace power {

// True when this boot is a timer wake from deep sleep (not power-on / reset / flash).
// Safe to call before begin().
bool wokeFromSleep();

void begin();

// Keep the board awake for at least ms from now (e.g. after a disconnect).
void stayAwakeFor(uint32_t ms);

// Call from loop(). busy = connected or a press is running. Never returns if it sleeps.
void tick(bool busy);

}  // namespace power
