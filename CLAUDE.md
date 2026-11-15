# schedule-power-board

Firmware for ESP32-C3 Super Mini home devices. Workspace overview + app contract: `../CLAUDE.md`.

## Envs (`platformio.ini`)
| Env | What |
|---|---|
| `c3_supermini` (default) | `PROFILE_POWER_BOARD`: 3 relays + schedules |
| `c3_button_tester` | `PROFILE_BUTTON_TESTER`: servo button, manual presses |
| `c3_rice_button` | `PROFILE_SCHEDULED_BUTTON`: servo button + press schedules |
| `c3_toggle_test` | Bench: flip CH1 every 5 s |
| `c3_all_test` | Bench: walk CH1..CH3, 2 s each |
| `c3_servo` | Standalone SG90 button pusher (`src/servo/`), serial commands |
| `c3_servo_sweep` | Servo runs full stroke loop |

## Commands
```bash
pio run                         # build default env
pio run -e <env> -t upload      # flash (upload_port pinned in platformio.ini)
pio device monitor              # serial 115200, native USB CDC
pio test -e <env>               # unit tests (test/ empty for now)
```

## Layout
- `include/config.h` — profile → relay/button/schedule counts, BLE name, `FW_VERSION`. Profile ids = `powerboard.Profile`.
- `include/pins.h` — per-profile pin map (`std::array`, size 0 when absent). Relays GPIO1/3/4, servo GPIO0, LED GPIO8 active-LOW (strapping pin).
- `src/relay.*` — relay driver. Polarity via `RELAY_ACTIVE_HIGH` (0 = active-LOW module). Loads COM→NC: power on = coil off.
- `src/protocol.*` — transport-agnostic nanopb decode → act → encode. `kMaxFrame = 128`.
- `src/button.*` — servo button pushers, non-blocking `tick()` from `loop()`. Mutex: `press/stop` run on NimBLE task. Hold/gap exclude ~125 ms servo travel. Tune via `BUTTON_HOME_MM`, `BUTTON_DEPTH_MM`, `SPEED_MM_PER_S`.
- `src/clock_sync.*` — wall clock from app `SetTime`; UTC offset in NVS (`clock` ns).
- `src/scheduler.*` — schedule slots in NVS (`sched` ns, key `v1`: raw struct blob, bump key if `Slot` layout changes). `tick()` from `loop()`, mutex vs BLE task.
- `src/power.*` — battery mode: deep sleep / timer wake / adv window. RTC_DATA_ATTR state (relay states, clock-set flag, last-fired minutes) + `gpio_hold_en` on outputs. `setup()` reruns every wake. Tune via `SLEEP_INTERVAL_S`, `ADV_WINDOW_MS`, `IDLE_DISCONNECT_S`, `SCHEDULE_LEAD_S` in `config.h`.
- `src/ble_service.*` — NimBLE GATT server, NUS-style UUIDs, peripheral only.
- `src/servo/` — standalone serial servo bench app, excluded from main build by `build_src_filter`. Duplicates servo math of `button.cpp`.
- `proto/` — `power_board.proto` + nanopb `.options`. `.pb.c/.pb.h` generated at build, gitignored.
- `docs/cad/`, `docs/3dlockbox/` — build123d CAD sources + STEP/STL/3MF for printed parts. After every `cad model export ... .3mf`, run `python weld_3mf.py <file.3mf>`: the raw export has unwelded vertices and Bambu Studio slices it near-empty.

## Flashing a battery device
Deep sleep drops USB. To flash: hold BOOT, tap RESET, release BOOT, then upload. Or flash during the 2 min cold-boot window.

## Rules
- Relays first in `setup()`: coils must reach safe de-energised state before anything else.
- Proto is the app contract. Add fields only, never renumber. Change app side in same sitting.
- Any new repeated/string field needs max size in `power_board.options`.
- No blocking work in BLE callbacks; keep `loop()` non-blocking.
- C++17, namespaces per module, `constexpr` over `#define` for constants.
