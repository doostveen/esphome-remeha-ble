# Changelog

## v1.0.1 (2026-11-20)

- *Use the choice of this ESP* now also takes over the entity names and the device
  name, so existing entities stay the same entities in Home Assistant (before, they got
  new default names in the chosen language).
- Clearer note under the YAML.
- No compiler warning about an empty `else` in `dump_config` with log level INFO.

## v1.0.0 (2026-11-20)

First release under the name **esphome-remeha-ble**: a generic Bluetooth component for
Remeha appliances instead of a fixed configuration for one model.

### Configurator
- **Configurator on the ESP** (`configurator: true`, needs `web_server:`): open
  `http://<esp-ip>/remeha`, press *Scan appliance*, choose what to read and what to be
  able to change, copy the YAML. About 140 kB of flash.
- The scan reads the appliance's own menu description (0x502B) and is streamed to the
  page in small pieces, so the ESP only needs a few kB of memory.
- **Three languages** (English, Dutch, German) for the page, object names, choice texts
  and the generated YAML. The short English and German names come from Remeha's own
  translations (`data/translations.json`).
- Objects with several elements (per zone, activity or producer) on **one row** with a
  button to show the elements; one tick selects them all.
- **Start from your current choice:** take over what the ESP reads now, or read a pasted
  YAML (names you gave yourself are kept). Objects that work but are not in the menu
  description are kept as well.
- Quick select buttons (Basic, Energy, Outdoor unit, Room, Heating curve), search and
  filters, *Read* / *Adjustable* tick boxes.

### Component
- **`code:`**: declare an entity with just the appliance code (for example
  `code: HM001`); index, subindex, data type, scaling, unit, classes and name come from
  the built-in codebook. ESPHome checks that the platform fits the object.
- New platforms: **`binary_sensor`** (on/off values), **`switch`** (adjustable on/off),
  **`select`** (adjustable choice lists with texts); **`text_sensor`** shows choice lists
  as text.
- **Limits from the appliance:** a `number` takes over the real minimum, maximum and step
  (kept in flash) and refuses values outside them; a `select` refuses choices the
  appliance does not allow. Switch off per number with `device_limits: false`.
- **`read: auto`** (default with `code:`): bulk read first, single read when the
  appliance does not return the object in bulk. Objects that do not exist on the
  appliance are reported once and no longer requested.
- **Appliance recognition:** article number and internal name in the log, optional
  `appliance:` entity and `expected_article_number:` warning (also shown in the
  appliance entity).
- **One YAML for both Bluetooth routes:** `connection: auto` (default) recognises the
  built-in Bluetooth (`EHC-...`, paired with the sticker passkey) and the GTW-IoT hub
  (`GTW-IOT...`, no pairing) by the advertised name. `connection: paired` / `plain` force
  a route; the old `requires_pairing:` still works.
- Faster first values after connecting.
- Discovery dump for development: `id(confida).start_discovery_dump()` logs raw
  identification and discovery objects (contains serial numbers, do not share publicly).
  Based on a proposal by Robert Klep (@robertklep) in PR #1.

### Upgrading from an earlier version
- The example YAMLs `remeha-confida.yaml` and `remeha-confida-gtwiot.yaml` and the
  separate GTW-IoT start YAML are gone. Use [`remeha-start.yaml`](remeha-start.yaml)
  and the configurator. If you referenced the old files from GitHub, pin them to commit
  `a651e64` until you have switched.
- The offline configurator page (`configurator/index.html`) is gone; the configurator
  now runs on the ESP.
- Seven values moved from `sensor` to `binary_sensor` in the old example YAML (HM007,
  HM030, HM008, HM009, AM015, 0x502E:1, 0x502E:7). In Home Assistant they get a new
  entity id; update automations and dashboards.
- A `number` now uses the limits of the appliance, which can replace the limits in your
  YAML (for example AP058 becomes 0 to 2.0 bar).
- The repository was renamed to `esphome-remeha-ble`; the old name redirects.
