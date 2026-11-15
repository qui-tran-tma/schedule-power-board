#pragma once

#include <stddef.h>
#include <stdint.h>

// Servo button pushers (rack-and-pinion SG90). Non-blocking: call tick() from loop().
// button_id is 1-based (1..count()).
namespace button {

enum class Result : uint8_t { kOk, kBadButton, kBadArgs, kBusy };

// Press limits. Shared with the app through power_board.proto comments.
constexpr uint32_t kMaxPressCount = 10;
constexpr uint32_t kMinHoldMs = 50;
constexpr uint32_t kMaxHoldMs = 30000;
constexpr uint32_t kMinGapMs = 100;
constexpr uint32_t kMaxGapMs = 10000;
constexpr uint32_t kDefaultGapMs = 250;

void begin();
size_t count();
// Stop PWM and latch servo signal LOW for deep sleep (servo idles, no torque).
void prepareSleep();

// Start a press sequence. pressCount 0 -> 1, gapMs 0 -> kDefaultGapMs.
Result press(uint32_t buttonId, uint32_t pressCount, uint32_t holdMs, uint32_t gapMs);
// Check press arguments without starting anything (used by schedules).
Result validate(uint32_t buttonId, uint32_t pressCount, uint32_t holdMs, uint32_t gapMs);
// Abort a running sequence and release. kOk even if idle.
Result stop(uint32_t buttonId);
bool isPressing(uint32_t buttonId);

// Drive servos and sequences. Returns true when any sequence finished this tick.
bool tick();

}  // namespace button
