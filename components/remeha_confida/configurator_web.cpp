#include "configurator_web.h"
#if defined(USE_ESP32) && defined(USE_REMEHA_CONFIGURATOR)
#include "esphome/core/log.h"
#include "configurator_page.h"
#include <cstring>

namespace esphome {
namespace remeha_confida {

static const char *const TAG = "remeha_confida.web";

void RemehaConfigurator::setup() {
  base_->init();
  base_->add_handler(this);
  ESP_LOGI(TAG, "configurator op /remeha (%u bytes)", (unsigned) sizeof(REMEHA_CONFIGURATOR_GZ));
}

bool RemehaConfigurator::canHandle(AsyncWebServerRequest *request) const {
  if (request->method() != HTTP_GET) return false;
  char buf[AsyncWebServerRequest::URL_BUF_SIZE];
  StringRef url = request->url_to(buf);
  return url == "/remeha" || url == "/remeha/" || url == "/remeha/scan" || url == "/remeha/data.json";
}

void RemehaConfigurator::handleRequest(AsyncWebServerRequest *request) {
  char buf[AsyncWebServerRequest::URL_BUF_SIZE];
  StringRef url = request->url_to(buf);
  if (url == "/remeha" || url == "/remeha/") {
    AsyncWebServerResponse *res =
        request->beginResponse(200, "text/html", REMEHA_CONFIGURATOR_GZ, sizeof(REMEHA_CONFIGURATOR_GZ));
    res->addHeader("Content-Encoding", "gzip");
    request->send(res);
    return;
  }
  if (url == "/remeha/scan") hub_->request_scan();
  // send straight from the hub's JSON buffer (no copy); send() is synchronous
  std::lock_guard<std::mutex> lock(hub_->scan_mutex());
  const std::string &j = hub_->scan_json();
  AsyncWebServerResponse *res = request->beginResponse(
      200, "application/json", reinterpret_cast<const uint8_t *>(j.data()), j.size());
  res->addHeader("Cache-Control", "no-store");
  request->send(res);
}

}  // namespace remeha_confida
}  // namespace esphome
#endif
