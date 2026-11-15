#pragma once

#include <stddef.h>
#include <stdint.h>

#include "config.h"

// Relay driver. Loads are wired COM -> NC, so "power on" means the coil is
// de-energised. Boot state is all coils de-energised (all loads powered).
namespace relay {

constexpr size_t kChannelCount = config::kRelayCount;  // 0 on button profiles

// Cold boot: all coils de-energised. Deep-sleep wake: restore the pre-sleep states.
void begin();
// Latch relay outputs so they keep their state through deep sleep.
void prepareSleep();

// channel is 1-based (1..kChannelCount). Returns false on bad channel.
bool setPower(uint8_t channel, bool powerOn);
bool isPowerOn(uint8_t channel);

}  // namespace relay
