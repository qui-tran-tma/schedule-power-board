#pragma once

#include <stdint.h>

#include <array>

#include "config.h"

// ESP32-C3 Super Mini pin map, per profile.
namespace pins {

// Relay inputs, index 0 = CH1. Loads wired COM -> NC.
#if DEVICE_PROFILE == PROFILE_POWER_BOARD
constexpr std::array<uint8_t, config::kRelayCount> kRelays = {1, 3, 4};
#else
constexpr std::array<uint8_t, config::kRelayCount> kRelays = {};
#endif

// Servo button pushers (SG90 signal, servo on 5V), index 0 = button_id 1.
#if DEVICE_PROFILE == PROFILE_POWER_BOARD
constexpr std::array<uint8_t, config::kButtonCount> kButtonServos = {};
#else
constexpr std::array<uint8_t, config::kButtonCount> kButtonServos = {0};
#endif

constexpr uint8_t kStatusLed = 8;  // onboard blue LED, active-LOW (also a strapping pin)

}  // namespace pins
