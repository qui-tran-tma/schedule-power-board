#include "power.h"

#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_sleep.h>

#include <atomic>

#include "button.h"
#include "config.h"
#include "pins.h"
#include "relay.h"
#include "scheduler.h"

namespace power {
namespace {

// Written from the NimBLE task (stayAwakeFor), read in loop().
std::atomic<uint32_t> g_awakeUntilMs{0};

void deepSleep(uint64_t seconds) {
  log_i("deep sleep %llu s", static_cast<unsigned long long>(seconds));
  Serial.flush();

  relay::prepareSleep();
  button::prepareSleep();
  digitalWrite(pins::kStatusLed, HIGH);  // LED off, latched
  gpio_hold_en(static_cast<gpio_num_t>(pins::kStatusLed));
  gpio_deep_sleep_hold_en();

  esp_sleep_enable_timer_wakeup(seconds * 1000000ULL);
  esp_deep_sleep_start();
}

}  // namespace

bool wokeFromSleep() { return esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_TIMER; }

void begin() {
  gpio_deep_sleep_hold_dis();
  gpio_hold_dis(static_cast<gpio_num_t>(pins::kStatusLed));
  if (!config::kLowPower) return;
  setCpuFrequencyMhz(80);  // lowest clock BLE supports
  g_awakeUntilMs = millis() + (wokeFromSleep() ? config::kAdvWindowMs : config::kColdBootWindowMs);
}

void stayAwakeFor(uint32_t ms) {
  const uint32_t until = millis() + ms;
  uint32_t cur = g_awakeUntilMs;
  while (static_cast<int32_t>(until - cur) > 0 && !g_awakeUntilMs.compare_exchange_weak(cur, until)) {
  }
}

void tick(bool busy) {
  if (!config::kLowPower || busy) return;
  if (static_cast<int32_t>(g_awakeUntilMs - millis()) > 0) return;

  // Next schedule: stay up if it is about to fire, else wake just before it.
  const int64_t untilNext = scheduler::secondsUntilNext();
  if (untilNext >= 0 && untilNext <= static_cast<int64_t>(config::kScheduleLeadS)) return;

  uint64_t sleepS = config::kSleepIntervalS;
  if (untilNext > 0) {
    const int64_t wake = untilNext - config::kScheduleLeadS;
    if (wake < static_cast<int64_t>(sleepS)) sleepS = wake;
  }
  if (sleepS < 1) sleepS = 1;
  deepSleep(sleepS);
}

}  // namespace power
