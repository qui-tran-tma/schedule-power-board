#pragma once

#include <stddef.h>
#include <stdint.h>

// Device profile, chosen per PlatformIO env with -DDEVICE_PROFILE=<n>.
// Values match powerboard.Profile in proto/power_board.proto.
#define PROFILE_POWER_BOARD 1       // 3 relays + relay schedules
#define PROFILE_BUTTON_TESTER 2     // 1 servo button, manual press tests
#define PROFILE_SCHEDULED_BUTTON 3  // 1 servo button + press schedules

#ifndef DEVICE_PROFILE
#define DEVICE_PROFILE PROFILE_POWER_BOARD
#endif

#ifndef FW_VERSION
#define FW_VERSION "0.2.0"
#endif

namespace config {

constexpr uint8_t kProfile = DEVICE_PROFILE;

#if DEVICE_PROFILE == PROFILE_POWER_BOARD
constexpr size_t kRelayCount = 3;
constexpr size_t kButtonCount = 0;
constexpr size_t kMaxSchedules = 16;
constexpr const char* kDefaultName = "PowerBoard";
#elif DEVICE_PROFILE == PROFILE_BUTTON_TESTER
constexpr size_t kRelayCount = 0;
constexpr size_t kButtonCount = 1;
constexpr size_t kMaxSchedules = 0;
constexpr const char* kDefaultName = "ButtonTester";
#elif DEVICE_PROFILE == PROFILE_SCHEDULED_BUTTON
constexpr size_t kRelayCount = 0;
constexpr size_t kButtonCount = 1;
constexpr size_t kMaxSchedules = 8;
constexpr const char* kDefaultName = "RiceButton";
#else
#error "Unknown DEVICE_PROFILE"
#endif

// ---- Battery mode (deep sleep between short advertising windows) ----
// Default: on for servo button devices (battery), off for the relay board (mains, coils
// draw ~70 mA each so battery is not viable anyway). Override with -DLOW_POWER=0/1.
#ifndef LOW_POWER
#define LOW_POWER (DEVICE_PROFILE != PROFILE_POWER_BOARD)
#endif
#ifndef SLEEP_INTERVAL_S
#define SLEEP_INTERVAL_S 60  // max deep sleep between advertising windows
#endif
#ifndef ADV_WINDOW_MS
#define ADV_WINDOW_MS 2000  // advertise this long after each timer wake
#endif
#ifndef COLD_BOOT_WINDOW_MS
#define COLD_BOOT_WINDOW_MS 120000  // after battery insert / flash / reset: time to set up
#endif
#ifndef DISCONNECT_GRACE_MS
#define DISCONNECT_GRACE_MS 5000  // stay advertising after disconnect, for quick reconnect
#endif
#ifndef IDLE_DISCONNECT_S
#define IDLE_DISCONNECT_S 180  // drop a connection with no request for this long
#endif
#ifndef SCHEDULE_LEAD_S
#define SCHEDULE_LEAD_S 3  // wake this early for a schedule (boot + drift margin)
#endif

constexpr bool kLowPower = LOW_POWER;
constexpr uint32_t kSleepIntervalS = SLEEP_INTERVAL_S;
constexpr uint32_t kAdvWindowMs = ADV_WINDOW_MS;
constexpr uint32_t kColdBootWindowMs = COLD_BOOT_WINDOW_MS;
constexpr uint32_t kDisconnectGraceMs = DISCONNECT_GRACE_MS;
constexpr uint32_t kIdleDisconnectS = IDLE_DISCONNECT_S;
constexpr uint32_t kScheduleLeadS = SCHEDULE_LEAD_S;

static_assert(kSleepIntervalS > kScheduleLeadS, "sleep interval must exceed schedule lead");

static_assert(kMaxSchedules <= 32, "Status.schedule_mask is 32 bits");

}  // namespace config

#ifndef BLE_DEVICE_NAME
#define BLE_DEVICE_NAME config::kDefaultName
#endif
