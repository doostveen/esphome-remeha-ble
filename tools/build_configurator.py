#!/usr/bin/env python3
"""Bouw de configurator-pagina voor de ESP (configurator_page.h) en de start-YAML.

Bronnen:
  data/Remeha_parametercodeboek.xlsx    objecten, namen, datatypes, keuzeteksten
  presets/*.yaml                        groepen voor de knoppen in de configurator
  tools/configurator_template.html      de pagina (met /*__DATA__*/ als plek voor de data)
  data/translations.json                korte Engelse/Duitse namen (uit de Remeha-vertalingen)

Uitvoer:
  components/remeha_ble/configurator_page.h   de pagina, gzip, voor /remeha op de ESP
  remeha-start.yaml                               eerste flash (ingebouwde Bluetooth en GTW-IoT)

Gebruik (vanuit de hoofdmap):  python3 tools/build_configurator.py
"""
import gzip
import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# YAML-kop per taal. {DEVICE_NAME} {FRIENDLY_NAME} {BLE_MAC} {REF} {EXPECTED}
# worden door de configurator (of hieronder voor de start-YAML's) ingevuld;
# {T:...} zijn de vertaalbare teksten uit TEXT.
# ---------------------------------------------------------------------------
HEAD = """# =====================================================================
#  {T:title}
#  {T:made}
# ---------------------------------------------------------------------
#  {T:secrets}
#     wifi_ssid / wifi_password
#     remeha_bt_key : {T:key}
#  {T:github}
#  {T:risk1}
#  {T:risk2}
# =====================================================================

substitutions:
  device_name: {DEVICE_NAME}
  friendly_name: "{FRIENDLY_NAME}"
  # {T:mac1}
  # {T:mac2}
  ble_mac: "{BLE_MAC}"

esphome:
  name: ${device_name}
  friendly_name: ${friendly_name}

esp32:
  board: esp32dev          # {T:board}
  framework:
    type: esp-idf

logger:
  level: INFO

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

api:
ota:
  - platform: esphome
web_server:
  version: 3
  port: 80

external_components:
  - source: github://mcc-tweakers/esphome-remeha-ble@{REF}
    components: [remeha_ble]
    refresh: 1d

button:
  - platform: restart
    name: "{T:restart}"
    icon: mdi:restart

switch:
  - platform: template
    name: "{T:active}"
    icon: mdi:bluetooth
    optimistic: true
    restore_mode: RESTORE_DEFAULT_ON
    turn_on_action:
      - lambda: 'id(remeha).set_active(true);'
    turn_off_action:
      - lambda: 'id(remeha).set_active(false);'

esp32_ble:
  io_capability: keyboard_only   # {T:io}

esp32_ble_tracker:

ble_client:
  - mac_address: ${ble_mac}
    id: remeha_client

remeha_ble:
  id: remeha
  ble_client_id: remeha_client
  update_interval: 30s
  service_uuid: "f8fc98e4-5919-4a5c-852e-dfe04ad383c0"
  write_uuid:   "496b1b03-cebc-4d59-9c32-14ea88c266f9"
  notify_uuid:  "ab9af948-fb86-492d-820d-bdea2dcb7ecf"
  # {T:pk1}
  # {T:pk2}
  passkey: !secret remeha_bt_key
{EXPECTED}  write_result:
    name: "{T:wres}"
  reconnect_reason:
    name: "{T:rreason}"
  reconnect_count:
    name: "{T:rcount}"
  appliance:
    name: "{T:appliance}"
  # {T:cfg1}
  # {T:cfg2}
  configurator: true
"""

TEXT = {
    "nl": dict(
        title="Remeha via Bluetooth (ingebouwde Bluetooth of GTW-IoT home-hub)",
        made="Gemaakt met de configurator van esphome-remeha-ble.",
        secrets="Vul in de secrets.yaml van je ESPHome in:",
        key='het 6-cijferige nummer van de BLE-sticker, tussen aanhalingstekens ("012345").',
        github="De component wordt bij het compileren uit GitHub gehaald (geen token nodig).",
        risk1="Gebruik op eigen risico. Een BLE-verbinding tegelijk: wil je met de app",
        risk2='verbinden, zet dan de schakelaar "Remeha uitlezing" uit.',
        mac1="00:00:00:00:00:00 = automatisch zoeken (naam EHC-... of GTW-IOT...). Heb je",
        mac2='meerdere toestellen, vul dan het MAC in (staat in de log: "BLE gezien: ...").',
        board="pas aan als je een ander ESP32-board hebt",
        restart="Remeha ESP herstart", active="Remeha uitlezing",
        io="nodig voor koppelen met het stickernummer",
        pk1="Ingebouwde Bluetooth: koppelt met het stickernummer. GTW-IoT: koppelt niet, de",
        pk2="component herkent dat zelf aan de naam (vul dan 000000 in bij remeha_bt_key).",
        wres="Remeha laatste schrijfresultaat", rreason="Remeha laatste herverbind-reden",
        rcount="Remeha herverbindingen", appliance="Remeha toestel",
        cfg1="Configurator-pagina op de ESP zelf: open http://<ip-van-de-esp>/remeha,",
        cfg2='druk op "Scan toestel" en kies wat je wilt zien. Zet op false om flash te sparen.',
        start1="START-YAML: eerste flash. Open daarna http://<ip-van-de-esp>/remeha, druk op",
        start2='"Scan toestel", kies wat je wilt zien en flash de YAML die je daar krijgt.',
        basis="Basisset (preset 'basis'); vervang dit later door de uitvoer van de configurator",
    ),
    "en": dict(
        title="Remeha via Bluetooth (built-in Bluetooth or GTW-IoT home hub)",
        made="Made with the esphome-remeha-ble configurator.",
        secrets="Put these in the secrets.yaml of your ESPHome:",
        key='the 6-digit number on the BLE sticker, in quotes ("012345").',
        github="The component is fetched from GitHub when compiling (no token needed).",
        risk1="Use at your own risk. Only one BLE connection at a time: to connect with the app,",
        risk2='switch off "Remeha reading" first.',
        mac1="00:00:00:00:00:00 = find the appliance automatically (name EHC-... or GTW-IOT...).",
        mac2='With several appliances, fill in the MAC (it is in the log: "BLE gezien: ...").',
        board="change this if you use another ESP32 board",
        restart="Remeha ESP restart", active="Remeha reading",
        io="needed to pair with the sticker number",
        pk1="Built-in Bluetooth: pairs with the sticker number. GTW-IoT: no pairing, the",
        pk2="component detects that from the name (then put 000000 in remeha_bt_key).",
        wres="Remeha last write result", rreason="Remeha last reconnect reason",
        rcount="Remeha reconnects", appliance="Remeha appliance",
        cfg1="Configurator page on the ESP itself: open http://<esp-ip>/remeha,",
        cfg2='press "Scan appliance" and pick what you want. Set to false to save flash.',
        start1="START YAML: first flash. Then open http://<esp-ip>/remeha, press",
        start2='"Scan appliance", pick what you want and flash the YAML you get there.',
        basis="Basic set (preset 'basis'); replace this later with the configurator output",
    ),
    "de": dict(
        title="Remeha über Bluetooth (eingebautes Bluetooth oder GTW-IoT Home-Hub)",
        made="Erstellt mit dem Konfigurator von esphome-remeha-ble.",
        secrets="In die secrets.yaml deines ESPHome eintragen:",
        key='die 6-stellige Nummer auf dem BLE-Aufkleber, in Anführungszeichen ("012345").',
        github="Die Komponente wird beim Kompilieren von GitHub geladen (kein Token nötig).",
        risk1="Nutzung auf eigene Gefahr. Nur eine BLE-Verbindung gleichzeitig: um dich mit der App",
        risk2='zu verbinden, schalte zuerst "Remeha Auslesen" aus.',
        mac1="00:00:00:00:00:00 = Gerät automatisch finden (Name EHC-... oder GTW-IOT...). Bei",
        mac2='mehreren Geräten die MAC eintragen (steht im Log: "BLE gezien: ...").',
        board="anpassen, wenn du ein anderes ESP32-Board nutzt",
        restart="Remeha ESP Neustart", active="Remeha Auslesen",
        io="nötig zum Koppeln mit der Aufklebernummer",
        pk1="Eingebautes Bluetooth: koppelt mit der Aufklebernummer. GTW-IoT: koppelt nicht, die",
        pk2="Komponente erkennt das am Namen (dann 000000 bei remeha_bt_key eintragen).",
        wres="Remeha letztes Schreibergebnis", rreason="Remeha letzter Grund für Neuverbindung",
        rcount="Remeha Neuverbindungen", appliance="Remeha Gerät",
        cfg1="Konfigurator-Seite auf dem ESP selbst: http://<esp-ip>/remeha öffnen,",
        cfg2='"Gerät scannen" drücken und auswählen. Auf false setzen, um Flash zu sparen.',
        start1="START-YAML: erstes Flashen. Danach http://<esp-ip>/remeha öffnen,",
        start2='"Gerät scannen" drücken, auswählen und die dort erzeugte YAML flashen.',
        basis="Grundauswahl (Preset 'basis'); später durch die Ausgabe des Konfigurators ersetzen",
    ),
}
LANGS = list(TEXT)


def head_template(lang="nl"):
    t = HEAD
    for k, v in TEXT[lang].items():
        t = t.replace("{T:" + k + "}", v)
    return t


def parse_choices(txt):
    out = []
    for part in str(txt or "").split(" | "):
        m = re.match(r"\s*(-?\d+)=(.*)$", part)
        if m:
            out.append([int(m.group(1)), m.group(2).strip()])
    return out


def load_translations():
    """Short English/German names (data/translations.json, from the Remeha OBD translations)."""
    p = ROOT / "data" / "translations.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"names": {}, "enums": {}}


def load_objects():
    tr = load_translations()
    wb = openpyxl.load_workbook(ROOT / "data" / "Remeha_parametercodeboek.xlsx", read_only=True)
    ws = wb["Parameters"]
    hdr = next(ws.iter_rows(max_row=1, values_only=True))
    col = {h: i for i, h in enumerate(hdr)}
    enums = {}
    we = wb["Enums"]
    eh = next(we.iter_rows(max_row=1, values_only=True))
    ec = {h: i for i, h in enumerate(eh)}
    for r in we.iter_rows(min_row=2, values_only=True):
        if r[ec["Enum"]] is None or r[ec["Waarde"]] is None:
            continue
        enums.setdefault(r[ec["Enum"]], []).append([int(r[ec["Waarde"]]), str(r[ec["Omschrijving (NL)"]] or "").strip()])
    objs, codes = {}, {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        idx = r[col["CANopen index"]].upper().replace("0X", "")
        sub = r[col["Sub"]].upper()
        code = (r[col["App-code"]] or "").strip().upper()
        note = str(r[col["Wetenswaardigheden"]] or "")
        o = {
            "c": code,
            "n": (r[col["Naam (NL)"]] or r[col["Interne naam (OBD)"]] or "").strip(),
            "k": {"Parameter": "P", "Signal": "S", "Counter": "C"}.get(r[col["Soort"]], "S"),
            "t": r[col["Datatype"]],
            "g": float(r[col["Gain"]]) if r[col["Gain"]] not in (None, "") else 1.0,
            "u": r[col["Eenheid"]] or "",
        }
        if note.startswith("ARRAY"):
            o["a"] = 1
        tn = tr["names"].get(r[col["Interne naam (OBD)"]])
        if tn:
            o["N"] = [x or o["n"] for x in tn]  # [en, de]
        if o["t"] == "Enum":
            ch = parse_choices(r[col["Toegestane waarden (NL)"]]) or enums.get(r[col["Enum"]], [])
            te = tr["enums"].get(r[col["Enum"]], {})
            # [raw, nl, en, de]
            o["e"] = [[v, t] + [x or t for x in te.get(str(v), ["", ""])] for v, t in ch]
        if code:
            codes[code] = codes.get(code, 0) + 1
        objs[f"{idx}:{sub}"] = o
    for o in objs.values():  # codes that occur more than once cannot be used via code:
        if o["c"] and codes.get(o["c"], 0) > 1:
            o["d"] = 1
    return objs


def load_presets():
    out = {}
    for p in sorted((ROOT / "presets").glob("*.yaml")):
        txt = p.read_text(encoding="utf-8")
        groups = {}
        cur = None
        for line in txt.splitlines():
            m = re.match(r"^([a-z_]+):\s*$", line)
            if m:
                cur = m.group(1)
            m = re.match(r"^\s+code:\s*([A-Z0-9]+)", line)
            if m and cur:
                groups.setdefault(cur, []).append(m.group(1))
        out[p.stem] = groups
    return out


def preset_entries(groups):
    lines = []
    for plat in ("sensor", "text_sensor", "binary_sensor", "number", "select"):
        if plat not in groups:
            continue
        lines.append(f"\n{plat}:")
        for c in groups[plat]:
            lines.append("  - platform: remeha_ble")
            lines.append(f"    code: {c}")
    return "\n".join(lines) + "\n"


def main():
    data = {
        "objects": load_objects(),
        "presets": load_presets(),
        "heads": {l: head_template(l) for l in LANGS},
        "known": {"7887477": "Remeha Confida 40"},
    }
    tpl = (ROOT / "tools" / "configurator_template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    gz = gzip.compress(html.encode("utf-8"), compresslevel=9, mtime=0)
    hdr = ROOT / "components" / "remeha_ble" / "configurator_page.h"
    lines = ["// Generated by tools/build_configurator.py - do not edit.",
             "// gzip-compressed configurator page, served at /remeha when `configurator: true`.",
             "#pragma once", "#include <cstdint>", "",
             "namespace esphome {", "namespace remeha_ble {", "",
             f"static const uint8_t REMEHA_CONFIGURATOR_GZ[{len(gz)}] = {{"]
    for i in range(0, len(gz), 24):
        lines.append("  " + ",".join(f"0x{b:02x}" for b in gz[i:i + 24]) + ",")
    lines += ["};", "", "}  // namespace remeha_ble", "}  // namespace esphome", ""]
    hdr.write_text("\n".join(lines), encoding="utf-8")
    print(f"{hdr.relative_to(ROOT)}: {len(gz) // 1024} kB gzip, {len(data['objects'])} objecten")

    T = TEXT["en"]  # the repo's start YAML is in English, like README.md
    h = (head_template("en")
         .replace("{DEVICE_NAME}", "remeha-ble")
         .replace("{FRIENDLY_NAME}", "Remeha")
         .replace("{BLE_MAC}", "00:00:00:00:00:00")
         .replace("{REF}", "main")
         .replace("{EXPECTED}", ""))
    h = h.replace(T["made"], T["start1"] + "\n#  " + T["start2"])
    body = "\n# --- " + T["basis"] + " ---" + preset_entries(data["presets"]["basis"])
    (ROOT / "remeha-start.yaml").write_text(h + body, encoding="utf-8")
    print("remeha-start.yaml: geschreven")


if __name__ == "__main__":
    main()
