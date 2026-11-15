#include <Arduino.h>

#include "ble_service.h"
#include "button.h"
#include "clock_sync.h"
#include "config.h"
#include "console.h"
#include "pins.h"
#include "power.h"
#include "relay.h"
#include "scheduler.h"

void setup() {
  // Relays first: get coils into a known (de-energised) state before anything else.
  relay::begin();
  button::begin();  // servos to released position

  Serial.begin(115200);
  if (!power::wokeFromSleep()) delay(200);  // give USB CDC a moment; skip on timer wakes
  log_i("schedule-power-board %s boot, profile %u", FW_VERSION, config::kProfile);

  pinMode(pins::kStatusLed, OUTPUT);
  digitalWrite(pins::kStatusLed, HIGH);  // off
  power::begin();  // releases pin holds from deep sleep

  clock_sync::begin();
  scheduler::begin();
  ble_service::begin();
  console::begin();
}

void loop() {
#if defined(RELAY_TEST_ALL)
  // Bench test: walk CH1..CH3, energise each coil (power OFF) then release it.
  static uint32_t lastStep = 0;
  static uint8_t step = 0;  // even = energise, odd = release
  if (millis() - lastStep >= RELAY_TEST_PERIOD_MS) {
    lastStep = millis();
    const uint8_t ch = step / 2 + 1;
    const bool powerOn = step % 2;
    relay::setPower(ch, powerOn);
    Serial.printf("[test] CH%u (GPIO%u) -> %s\n", ch, pins::kRelays[ch - 1],
                  powerOn ? "coil released, NC closed, load ON" : "coil energised, NC open, load OFF");
    step = (step + 1) % 6;
  }
#elif defined(RELAY_TEST_CHANNEL)
  // Bench test: flip the channel every RELAY_TEST_PERIOD_MS.
  static uint32_t lastToggle = 0;
  if (millis() - lastToggle >= RELAY_TEST_PERIOD_MS) {
    lastToggle = millis();
    const bool next = !relay::isPowerOn(RELAY_TEST_CHANNEL);
    relay::setPower(RELAY_TEST_CHANNEL, next);
    Serial.printf("[test] ch%d power %s\n", RELAY_TEST_CHANNEL, next ? "ON" : "OFF");
  }
#endif

  console::tick();

  // Button pushers: drive servos, tell the app when a press sequence ends.
  bool changed = button::tick();
  // Schedules: fire due entries (needs the app to have set the clock since boot).
  changed |= scheduler::tick();
  if (changed) ble_service::notifyStatus();
  ble_service::tick();

  // Status LED: solid when connected; slow blink when advertising (mains only, saves battery).
  static uint32_t last = 0;
  static bool led = false;
  const uint32_t now = millis();
  const bool connected = ble_service::isConnected();
  if (connected) {
    digitalWrite(pins::kStatusLed, LOW);
  } else if (config::kLowPower) {
    digitalWrite(pins::kStatusLed, HIGH);
  } else if (now - last >= 1000) {
    last = now;
    led = !led;
    digitalWrite(pins::kStatusLed, led ? LOW : HIGH);
  }

  // Battery mode: deep sleep when nothing needs the board awake. Does not return if it sleeps.
  bool pressing = false;
  for (size_t id = 1; id <= button::count(); ++id) pressing |= button::isPressing(id);
  power::tick(connected || pressing);

  delay(20);
}
