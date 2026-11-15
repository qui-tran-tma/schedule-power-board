#include "ble_service.h"

#include <Arduino.h>
#include <NimBLEDevice.h>

#include "config.h"
#include "power.h"
#include "protocol.h"

#include <atomic>

namespace ble_service {
namespace {

constexpr const char* kServiceUuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e";
constexpr const char* kRxUuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e";
constexpr const char* kTxUuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";

NimBLECharacteristic* g_tx = nullptr;
std::atomic<uint32_t> g_lastActivityMs{0};  // connect or request, NimBLE task

class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer*, NimBLEConnInfo& info) override {
    g_lastActivityMs = millis();
    log_i("connected: %s", info.getAddress().toString().c_str());
  }
  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int reason) override {
    log_i("disconnected (reason %d), advertising", reason);
    power::stayAwakeFor(config::kDisconnectGraceMs);
    NimBLEDevice::startAdvertising();
  }
};

class RxCallbacks : public NimBLECharacteristicCallbacks {
  void onWrite(NimBLECharacteristic* c, NimBLEConnInfo&) override {
    g_lastActivityMs = millis();
    const NimBLEAttValue& v = c->getValue();
    uint8_t out[protocol::kMaxFrame];
    const size_t n = protocol::handle(v.data(), v.length(), out, sizeof(out));
    if (n > 0) {
      g_tx->setValue(out, n);
      g_tx->notify();
    }
  }
};

ServerCallbacks g_serverCb;
RxCallbacks g_rxCb;

}  // namespace

void begin() {
  NimBLEDevice::init(BLE_DEVICE_NAME);
  NimBLEDevice::setMTU(185);

  NimBLEServer* server = NimBLEDevice::createServer();
  server->setCallbacks(&g_serverCb, false);

  NimBLEService* svc = server->createService(kServiceUuid);
  NimBLECharacteristic* rx =
      svc->createCharacteristic(kRxUuid, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR);
  rx->setCallbacks(&g_rxCb);
  g_tx = svc->createCharacteristic(kTxUuid, NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::READ);

  NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
  adv->setName(BLE_DEVICE_NAME);
  adv->addServiceUUID(kServiceUuid);
  adv->enableScanResponse(true);
  if (config::kLowPower) {
    // Short wake windows: advertise fast so a scanning phone sees the board quickly.
    adv->setMinInterval(0x50);  // 50 ms (units of 0.625 ms)
    adv->setMaxInterval(0x60);  // 60 ms
  }
  adv->start();
  log_i("BLE advertising as %s (profile %u)", BLE_DEVICE_NAME, config::kProfile);
}

bool isConnected() { return NimBLEDevice::getServer()->getConnectedCount() > 0; }

void tick() {
  if (!config::kLowPower || config::kIdleDisconnectS == 0 || !isConnected()) return;
  if (millis() - g_lastActivityMs < config::kIdleDisconnectS * 1000UL) return;
  log_i("connection idle %u s, disconnecting to save battery",
        static_cast<unsigned>(config::kIdleDisconnectS));
  g_lastActivityMs = millis();  // one attempt per idle period
  NimBLEServer* server = NimBLEDevice::getServer();
  for (uint16_t handle : server->getPeerDevices()) server->disconnect(handle);
}

void notifyStatus() {
  if (!g_tx || !isConnected()) return;
  uint8_t out[protocol::kMaxFrame];
  const size_t n = protocol::encodeStatus(out, sizeof(out));
  if (n > 0) {
    g_tx->setValue(out, n);
    g_tx->notify();
  }
}

}  // namespace ble_service
