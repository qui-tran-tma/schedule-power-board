#include "relay.h"

#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_attr.h>

#include <array>

#include "pins.h"
#include "power.h"

#ifndef RELAY_ACTIVE_HIGH
#define RELAY_ACTIVE_HIGH 0
#endif

namespace relay {
namespace {

constexpr uint8_t kCoilOn = RELAY_ACTIVE_HIGH ? HIGH : LOW;
constexpr uint8_t kCoilOff = RELAY_ACTIVE_HIGH ? LOW : HIGH;

// RTC memory: survives deep sleep so a wake does not flip loads back on.
RTC_DATA_ATTR std::array<bool, kChannelCount> g_powerOn{};

bool valid(uint8_t channel) { return channel >= 1 && channel <= kChannelCount; }

}  // namespace

void begin() {
  const bool restore = power::wokeFromSleep();
  for (size_t i = 0; i < kChannelCount; ++i) {
    if (!restore) g_powerOn[i] = true;
    const uint8_t level = g_powerOn[i] ? kCoilOff : kCoilOn;
    // Set the output level before enabling the driver / releasing the hold so the coil
    // never pulses at boot.
    digitalWrite(pins::kRelays[i], level);
    pinMode(pins::kRelays[i], OUTPUT);
    digitalWrite(pins::kRelays[i], level);
    gpio_hold_dis(static_cast<gpio_num_t>(pins::kRelays[i]));
  }
}

void prepareSleep() {
  for (size_t i = 0; i < kChannelCount; ++i) {
    gpio_hold_en(static_cast<gpio_num_t>(pins::kRelays[i]));
  }
}

bool setPower(uint8_t channel, bool powerOn) {
  if (!valid(channel)) return false;
  const size_t i = channel - 1;
  digitalWrite(pins::kRelays[i], powerOn ? kCoilOff : kCoilOn);
  g_powerOn[i] = powerOn;
  log_i("relay ch%u -> %s", channel, powerOn ? "ON (COM-NC closed)" : "OFF (COM-NC open)");
  return true;
}

bool isPowerOn(uint8_t channel) { return valid(channel) && g_powerOn[channel - 1]; }

}  // namespace relay
