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

### Let op bij updaten
- In beide YAML's zijn zeven waarden van `sensor` naar `binary_sensor` verhuisd: HM007,
  HM030, HM008, HM009, AM015 en de vlaggen 0x502E:1 en 0x502E:7. In Home Assistant
  krijgen ze daardoor een nieuwe entiteit (`binary_sensor.…` in plaats van
  `sensor.…`). Pas automatiseringen en dashboards aan en verwijder de oude, nu
  onbeschikbare sensoren.

### Overig
- Repository hernoemd naar `esphome-remeha-ble`. De oude naam stuurt automatisch door.
