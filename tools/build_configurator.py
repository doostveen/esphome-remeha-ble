#!/usr/bin/env python3
"""Bouw de configurator (configurator/index.html) en de start-YAML's.

Bronnen:
  data/Remeha_parametercodeboek.xlsx    objecten, namen, datatypes, keuzeteksten
  presets/*.yaml                        groepen voor de knoppen in de configurator
  tools/configurator_template.html      de pagina (met /*__DATA__*/ als plek voor de data)
  tools/sample_confida40.json           voorbeeld: menubeschrijving (0x502B) van een Confida 40

Uitvoer:
  configurator/index.html               zelfstandige pagina (alles ingebakken, werkt ook offline)
  remeha-start.yaml                     eerste flash, GTW-22-route (sticker/passkey)
  remeha-start-gtwiot.yaml              eerste flash, GTW-IoT-route (geen passkey)

Gebruik (vanuit de hoofdmap):  python3 tools/build_configurator.py
"""
import gzip
import json
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# YAML-kop per route en taal. {DEVICE_NAME} {FRIENDLY_NAME} {BLE_MAC} {REF} {EXPECTED}
# worden door de configurator (of hieronder voor de start-YAML's) ingevuld;
# {T:...} zijn de vertaalbare teksten uit TEXT.
# ---------------------------------------------------------------------------
HEAD = """# =====================================================================
#  {TITLE}
#  {T:made}
# ---------------------------------------------------------------------
#  {T:secrets}
#     wifi_ssid / wifi_password{SECRET_LINE}
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
    components: [remeha_confida]
    refresh: 1d

button:
  - platform: restart
    name: "{T:restart}"
    icon: mdi:restart
  # {T:dump1}
  # {T:dump2}
  - platform: template
    name: "{T:dump}"
    entity_category: diagnostic
    icon: mdi:magnify-scan
    on_press:
      - lambda: 'id(confida).start_discovery_dump();'

switch:
  - platform: template
    name: "{T:active}"
    icon: mdi:bluetooth
    optimistic: true
    restore_mode: RESTORE_DEFAULT_ON
    turn_on_action:
      - lambda: 'id(confida).set_active(true);'
    turn_off_action:
      - lambda: 'id(confida).set_active(false);'

esp32_ble:
  io_capability: {IO_CAP}

esp32_ble_tracker:

ble_client:
  - mac_address: ${ble_mac}
    id: confida_client

remeha_confida:
  id: confida
  ble_client_id: confida_client
  update_interval: 30s
  service_uuid: "f8fc98e4-5919-4a5c-852e-dfe04ad383c0"
  write_uuid:   "496b1b03-cebc-4d59-9c32-14ea88c266f9"
  notify_uuid:  "ab9af948-fb86-492d-820d-bdea2dcb7ecf"
{AUTH}  device_name_prefix: "{PREFIX}"
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
        made="Gemaakt met de configurator van esphome-remeha-ble.",
        secrets="Vul in de secrets.yaml van je ESPHome in:",
        github="De component wordt bij het compileren uit GitHub gehaald (geen token nodig).",
        risk1="Gebruik op eigen risico. Een BLE-verbinding tegelijk: wil je met de app",
        risk2='verbinden, zet dan de schakelaar "Remeha uitlezing" uit.',
        mac1='00:00:00:00:00:00 = automatisch zoeken op naam ("{PREFIX}..."). Heb je meerdere',
        mac2='toestellen, vul dan het MAC in (staat in de log: "BLE gezien: ...").',
        board="pas aan als je een ander ESP32-board hebt",
        restart="Remeha ESP herstart", dump="Remeha discovery-dump", active="Remeha uitlezing",
        dump1="Leest eenmalig wat het toestel kan (o.a. de menubeschrijving 0x502B) en zet het",
        dump2="als DUMP-regels in de log. Plak die regels in de configurator.",
        wres="Remeha laatste schrijfresultaat", rreason="Remeha laatste herverbind-reden",
        rcount="Remeha herverbindingen", appliance="Remeha toestel",
        cfg1='Configurator-pagina op de ESP zelf: open http://<ip-van-de-esp>/remeha,',
        cfg2='druk op "Scan toestel" en kies wat je wilt zien. Zet op false om flash te sparen.',
        t_gtw22="Remeha met ingebouwde Bluetooth (GTW-22, bv. Confida 40)",
        t_gtwiot="Remeha via de GTW-IoT home-hub (bv. Confida 10)",
        s_gtw22="\n#     remeha_bt_key : het 6-cijferige nummer van de BLE-sticker",
        s_gtwiot="\n#  (geen remeha_bt_key nodig: de GTW-IoT koppelt zonder passkey)",
        io_gtw22="wij leveren de passkey (het stickernummer)",
        a_gtw22="6-cijferig stickernummer", a_gtwiot="GTW-IoT: geen pairing, geen passkey",
    ),
    "en": dict(
        made="Made with the esphome-remeha-ble configurator.",
        secrets="Put these in the secrets.yaml of your ESPHome:",
        github="The component is fetched from GitHub when compiling (no token needed).",
        risk1="Use at your own risk. Only one BLE connection at a time: to connect with the app,",
        risk2='switch off "Remeha reading" first.',
        mac1='00:00:00:00:00:00 = find the appliance by name ("{PREFIX}..."). With several',
        mac2='appliances, fill in the MAC (it is in the log: "BLE gezien: ...").',
        board="change this if you use another ESP32 board",
        restart="Remeha ESP restart", dump="Remeha discovery dump", active="Remeha reading",
        dump1="Reads once what the appliance offers (including the menu description 0x502B) and",
        dump2="writes it to the log as DUMP lines. Paste those lines into the configurator.",
        wres="Remeha last write result", rreason="Remeha last reconnect reason",
        rcount="Remeha reconnects", appliance="Remeha appliance",
        cfg1="Configurator page on the ESP itself: open http://<esp-ip>/remeha,",
        cfg2='press "Scan appliance" and pick what you want. Set to false to save flash.',
        t_gtw22="Remeha with built-in Bluetooth (GTW-22, e.g. Confida 40)",
        t_gtwiot="Remeha via the GTW-IoT home hub (e.g. Confida 10)",
        s_gtw22="\n#     remeha_bt_key : the 6-digit number on the BLE sticker",
        s_gtwiot="\n#  (no remeha_bt_key needed: the GTW-IoT pairs without a passkey)",
        io_gtw22="we supply the passkey (the sticker number)",
        a_gtw22="6-digit sticker number", a_gtwiot="GTW-IoT: no pairing, no passkey",
    ),
    "de": dict(
        made="Erstellt mit dem Konfigurator von esphome-remeha-ble.",
        secrets="In die secrets.yaml deines ESPHome eintragen:",
        github="Die Komponente wird beim Kompilieren von GitHub geladen (kein Token nötig).",
        risk1="Nutzung auf eigene Gefahr. Nur eine BLE-Verbindung gleichzeitig: um dich mit der App",
        risk2='zu verbinden, schalte zuerst "Remeha Auslesen" aus.',
        mac1='00:00:00:00:00:00 = Gerät automatisch über den Namen finden ("{PREFIX}..."). Bei',
        mac2='mehreren Geräten die MAC eintragen (steht im Log: "BLE gezien: ...").',
        board="anpassen, wenn du ein anderes ESP32-Board nutzt",
        restart="Remeha ESP Neustart", dump="Remeha Discovery-Dump", active="Remeha Auslesen",
        dump1="Liest einmalig, was das Gerät kann (u. a. die Menübeschreibung 0x502B), und schreibt",
        dump2="es als DUMP-Zeilen ins Log. Diese Zeilen in den Konfigurator einfügen.",
        wres="Remeha letztes Schreibergebnis", rreason="Remeha letzter Grund für Neuverbindung",
        rcount="Remeha Neuverbindungen", appliance="Remeha Gerät",
        cfg1="Konfigurator-Seite auf dem ESP selbst: http://<esp-ip>/remeha öffnen,",
        cfg2='"Gerät scannen" drücken und auswählen. Auf false setzen, um Flash zu sparen.',
        t_gtw22="Remeha mit eingebautem Bluetooth (GTW-22, z. B. Confida 40)",
        t_gtwiot="Remeha über den GTW-IoT Home-Hub (z. B. Confida 10)",
        s_gtw22="\n#     remeha_bt_key : die 6-stellige Nummer auf dem BLE-Aufkleber",
        s_gtwiot="\n#  (kein remeha_bt_key nötig: der GTW-IoT koppelt ohne Passkey)",
        io_gtw22="wir liefern den Passkey (die Aufklebernummer)",
        a_gtw22="6-stellige Aufklebernummer", a_gtwiot="GTW-IoT: kein Pairing, kein Passkey",
    ),
}
LANGS = list(TEXT)

ROUTES = {
    "gtw22": dict(PREFIX="EHC-", IO="keyboard_only", AUTH="  passkey: !secret remeha_bt_key      # {A}\n"),
    "gtwiot": dict(PREFIX="GTW-IOT", IO="none", AUTH="  requires_pairing: false             # {A}\n"),
}


def head_template(route, lang="nl"):
    T = TEXT[lang]
    r = ROUTES[route]
    io = r["IO"] + ("   # " + T["io_" + route] if "io_" + route in T else "")
    t = (HEAD.replace("{TITLE}", T["t_" + route]).replace("{SECRET_LINE}", T["s_" + route])
         .replace("{IO_CAP}", io).replace("{AUTH}", r["AUTH"].replace("{A}", T["a_" + route])))
    for k, v in T.items():
        t = t.replace("{T:" + k + "}", v)
    return t.replace("{PREFIX}", r["PREFIX"])


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
            lines.append("  - platform: remeha_confida")
            lines.append(f"    code: {c}")
    return "\n".join(lines) + "\n"


def main():
    data = {
        "objects": load_objects(),
        "presets": load_presets(),
        "heads": {r: {l: head_template(r, l) for l in LANGS} for r in ROUTES},
        "sample": json.loads((ROOT / "tools" / "sample_confida40.json").read_text()),
        "known": {"7887477": "Remeha Confida 40"},
    }
    tpl = (ROOT / "tools" / "configurator_template.html").read_text(encoding="utf-8")
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out = ROOT / "configurator" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(tpl.replace("/*__DATA__*/null", js), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size // 1024} kB, {len(data['objects'])} objecten")

    # Same page for the ESP itself (configurator: true): scans via /remeha/scan,
    # no sample data, gzip-compressed into a C array.
    dev = dict(data, onDevice=True, sample=[])
    html = tpl.replace("/*__DATA__*/null", json.dumps(dev, ensure_ascii=False, separators=(",", ":")))
    gz = gzip.compress(html.encode("utf-8"), compresslevel=9, mtime=0)
    hdr = ROOT / "components" / "remeha_confida" / "configurator_page.h"
    lines = ["// Generated by tools/build_configurator.py - do not edit.",
             "// gzip-compressed configurator page, served at /remeha when `configurator: true`.",
             "#pragma once", "#include <cstdint>", "",
             "namespace esphome {", "namespace remeha_confida {", "",
             f"static const uint8_t REMEHA_CONFIGURATOR_GZ[{len(gz)}] = {{"]
    for i in range(0, len(gz), 24):
        lines.append("  " + ",".join(f"0x{b:02x}" for b in gz[i:i + 24]) + ",")
    lines += ["};", "", "}  // namespace remeha_confida", "}  // namespace esphome", ""]
    hdr.write_text("\n".join(lines), encoding="utf-8")
    print(f"{hdr.relative_to(ROOT)}: {len(gz) // 1024} kB gzip")

    basis = data["presets"]["basis"]
    for route, fname in (("gtw22", "remeha-start.yaml"), ("gtwiot", "remeha-start-gtwiot.yaml")):
        h = (head_template(route)
             .replace("{DEVICE_NAME}", "remeha-ble")
             .replace("{FRIENDLY_NAME}", "Remeha")
             .replace("{BLE_MAC}", "00:00:00:00:00:00")
             .replace("{REF}", "main")
             .replace("{EXPECTED}", ""))
        h = h.replace("Gemaakt met de configurator van esphome-remeha-ble.",
                      "START-YAML: eerste flash. Daarna: druk op \"Remeha discovery-dump\", plak de\n"
                      "#  DUMP-regels uit de log in de configurator en kies wat je wilt zien.")
        body = "\n# --- Basisset (preset 'basis'); vervang dit later door de uitvoer van de configurator ---" \
               + preset_entries(basis)
        (ROOT / fname).write_text(h + body, encoding="utf-8")
        print(f"{fname}: geschreven")


if __name__ == "__main__":
    main()
