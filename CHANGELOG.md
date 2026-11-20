# Wijzigingen

## In ontwikkeling (branch `dev`)

### Nieuw
- **`binary_sensor`**: aan/uit-waarden (YesNo, OffOn, InactiveActive, statusvlaggen)
  komen in Home Assistant als aan/uit in plaats van 0/1. Optioneel `true_value`.
- **`switch`**: instelbare aan/uit-parameters. Aan schrijft `1` (of `true_value`),
  uit schrijft `0`. Wordt meegepolld en schrijft niets bij het opstarten.
- **Discovery-dump (verkenning)**: `id(confida).start_discovery_dump()` leest eenmalig
  identificatie- en discovery-objecten (o.a. 0x2001, 0x2007, 0x502B, 0x5170) en zet de
  ruwe bytes als `DUMP`-regels in de log. Alleen lezen. Koppel het aan een template-knop:
  ```yaml
  button:
    - platform: template
      name: "Remeha discovery-dump"
      entity_category: diagnostic
      on_press:
        - lambda: 'id(confida).start_discovery_dump();'
  ```
  Let op: de dump bevat serienummers. Deel de log niet openbaar.
- Met dank aan Robert Klep (@robertklep), wiens voorstel in PR #1 hiervoor de basis was.

- **`code:`**: entiteiten met alleen de code uit het codeboek (bv. `code: HM001`). De
  component vult index, subindex, datatype, gain, eenheid, klassen en naam zelf in, en
  controleert bij het valideren of het platform past.
- **`select`**: instelbare keuzelijsten met teksten (bv. CP780 Regelstrategie).
- **`text_sensor`** toont keuzelijsten als tekst (met `code:` of eigen `options:`).
- **`read: auto`** (standaard bij `code:`): eerst bulk, zelf overstappen op los uitlezen
  als het toestel het object niet in de bulk-lijst teruggeeft.
- Objecten die niet bestaan op het toestel worden gemeld en niet meer uitgelezen.
- **Grenzen uit het toestel**: na het verbinden wordt de menubeschrijving (0x502B) gelezen.
  `number` krijgt de echte min/max/stap van het toestel (bewaard in flash, zichtbaar in HA
  na herstart of herverbinding); waarden daarbuiten worden niet geschreven. `select` weigert
  keuzes die het toestel niet toestaat. Uitzetten per number met `device_limits: false`.
  Let op: dit kan de grenzen in je bestaande YAML vervangen (bv. AP058 wordt 0 tot 2,0 bar).
- Meerdere entiteiten op hetzelfde object (bv. een `sensor` en een `select`) krijgen nu allemaal
  de waarde.

- **Presets** in `presets/`: basis, energie, buitenunit, ruimte en stooklijn, als package
  in te voegen.
- **Toestelherkenning**: artikelnummer (0x2000:09) en interne naam (0x3047) in de log,
  optioneel als entiteit (`appliance:`) en met een waarschuwing bij een ander toestel
  (`expected_article_number:`).
- **Sneller eerste waarden**: de eerste uitlezing start direct na het verbinden; objecten
  die niet in de bulk-lijst zitten worden meteen in dezelfde ronde los gelezen; de
  menubeschrijving komt pas daarna.

- **Configurator** (`configurator/index.html`): plak de discovery-dump, kies per object
  lezen of instelbaar (of een groep in één klik) en kopieer een complete YAML. Werkt in de
  browser, verstuurt niets.
- **Start-YAML's** (`remeha-start.yaml`, `remeha-start-gtwiot.yaml`): eerste flash met
  basisset en dump-knop.

### Let op bij updaten
- In beide YAML's zijn zeven waarden van `sensor` naar `binary_sensor` verhuisd: HM007,
  HM030, HM008, HM009, AM015 en de vlaggen 0x502E:1 en 0x502E:7. In Home Assistant
  krijgen ze daardoor een nieuwe entiteit (`binary_sensor.…` in plaats van
  `sensor.…`). Pas automatiseringen en dashboards aan en verwijder de oude, nu
  onbeschikbare sensoren.

### Overig
- Repository hernoemd naar `esphome-remeha-ble`. De oude naam stuurt automatisch door.
