#include "configurator_web.h"
#if defined(USE_ESP32) && defined(USE_REMEHA_CONFIGURATOR)
#include "esphome/core/log.h"
#include "configurator_page.h"
#include <cstring>
#include <cstdlib>

namespace esphome {
namespace remeha_ble {

static const char *const TAG = "remeha_ble.web";

void RemehaConfigurator::setup() {
  base_->init();
  base_->add_handler(this);
  ESP_LOGI(TAG, "configurator op /remeha (%u bytes)", (unsigned) sizeof(REMEHA_CONFIGURATOR_GZ));
}

bool RemehaConfigurator::canHandle(AsyncWebServerRequest *request) const {
  if (request->method() != HTTP_GET) return false;
  char buf[AsyncWebServerRequest::URL_BUF_SIZE];
  StringRef url = request->url_to(buf);
  return url == "/remeha" || url == "/remeha/" || url == "/remeha/scan" || url == "/remeha/data.json" ||
         url == "/remeha/current.json" || url == "/remeha/read";
}

void RemehaConfigurator::handleRequest(AsyncWebServerRequest *request) {
  char buf[AsyncWebServerRequest::URL_BUF_SIZE];
  StringRef url = request->url_to(buf);
  if (url == "/remeha" || url == "/remeha/") {
    AsyncWebServerResponse *res =
        request->beginResponse(200, "text/html; charset=utf-8", REMEHA_CONFIGURATOR_GZ, sizeof(REMEHA_CONFIGURATOR_GZ));
    res->addHeader("Content-Encoding", "gzip");
    request->send(res);
    return;
  }
  if (url == "/remeha/current.json") {
    std::string j = hub_->current_json();
    AsyncWebServerResponse *res = request->beginResponse(
        200, "application/json; charset=utf-8", reinterpret_cast<const uint8_t *>(j.data()), j.size());
    res->addHeader("Cache-Control", "no-store");
    request->send(res);
    return;
  }
  if (url == "/remeha/read") {
    // ?n=1&i=13313&s=1 starts a read; without parameters: the result so far
    auto *pi = request->getParam("i");
    std::string j;
    if (pi != nullptr) {
      auto *pn = request->getParam("n");
      auto *ps = request->getParam("s");
      j = hub_->probe_request(pn != nullptr ? (uint8_t) strtoul(pn->value().c_str(), nullptr, 10) : 1,
                              (uint16_t) strtoul(pi->value().c_str(), nullptr, 0),
                              ps != nullptr ? (uint8_t) strtoul(ps->value().c_str(), nullptr, 10) : 0);
    } else {
      j = hub_->probe_poll();
    }
    AsyncWebServerResponse *res = request->beginResponse(
        200, "application/json; charset=utf-8", reinterpret_cast<const uint8_t *>(j.data()), j.size());
    res->addHeader("Cache-Control", "no-store");
    request->send(res);
    return;
  }
  if (url == "/remeha/scan") hub_->request_scan();
  // ?gen=G&from=N: the page already has chunks < N of run G, the hub frees them
  int gen = -1;
  uint16_t from = 0;
  auto *g = request->getParam("gen");
  if (g != nullptr) gen = (int) strtol(g->value().c_str(), nullptr, 10);
  auto *f = request->getParam("from");
  if (f != nullptr) from = (uint16_t) strtoul(f->value().c_str(), nullptr, 10);
  std::string j = hub_->scan_poll(gen, from);
  AsyncWebServerResponse *res = request->beginResponse(
      200, "application/json; charset=utf-8", reinterpret_cast<const uint8_t *>(j.data()), j.size());
  res->addHeader("Cache-Control", "no-store");
  request->send(res);  // synchronous, j stays valid
}

}  // namespace remeha_ble
}  // namespace esphome
#endif
