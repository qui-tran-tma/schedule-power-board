#include "clock_sync.h"

#include <Arduino.h>
#include <Preferences.h>
#include <esp_attr.h>
#include <sys/time.h>

#include <atomic>

#include "power.h"

namespace clock_sync {
namespace {

constexpr uint64_t kMinValidUnix = 1704067200;  // 2024-01-01
constexpr int32_t kMaxOffsetMin = 14 * 60;
constexpr const char* kNamespace = "clock";
constexpr const char* kOffsetKey = "utc_off";

// RTC memory: the system clock keeps running through deep sleep, so a set clock stays
// valid after a timer wake. Any other reset clears it.
RTC_DATA_ATTR volatile bool g_set = false;
std::atomic<int32_t> g_offsetMin{0};

}  // namespace

void begin() {
  if (!power::wokeFromSleep()) g_set = false;
  Preferences prefs;
  if (prefs.begin(kNamespace, true)) {
    g_offsetMin = prefs.getInt(kOffsetKey, 0);
    prefs.end();
  }
}

bool set(uint64_t unixS, int32_t utcOffsetMin) {
  if (unixS < kMinValidUnix || utcOffsetMin < -kMaxOffsetMin || utcOffsetMin > kMaxOffsetMin) {
    return false;
  }
  timeval tv{static_cast<time_t>(unixS), 0};
  settimeofday(&tv, nullptr);
  if (g_offsetMin.exchange(utcOffsetMin) != utcOffsetMin) {
    Preferences prefs;
    if (prefs.begin(kNamespace, false)) {
      prefs.putInt(kOffsetKey, utcOffsetMin);
      prefs.end();
    }
  }
  g_set = true;
  log_i("clock set: unix %llu, offset %d min", static_cast<unsigned long long>(unixS),
        static_cast<int>(utcOffsetMin));
  return true;
}

bool isSet() { return g_set; }

uint64_t unixNow() {
  if (!g_set) return 0;
  timeval tv{};
  gettimeofday(&tv, nullptr);
  return static_cast<uint64_t>(tv.tv_sec);
}

int32_t utcOffsetMin() { return g_offsetMin; }

bool localNow(struct tm& out, int64_t& localMinuteKey) {
  if (!g_set) return false;
  const int64_t local = static_cast<int64_t>(unixNow()) + static_cast<int64_t>(g_offsetMin) * 60;
  const time_t t = static_cast<time_t>(local);
  gmtime_r(&t, &out);  // offset already applied; avoids TZ env handling
  localMinuteKey = local / 60;
  return true;
}

}  // namespace clock_sync
