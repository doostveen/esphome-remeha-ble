# Wijzigingen

## In ontwikkeling (branch `dev`)

### Nieuw
- **`binary_sensor`**: aan/uit-waarden (YesNo, OffOn, InactiveActive, statusvlaggen)
  komen in Home Assistant als aan/uit in plaats van 0/1. Optioneel `true_value`.
- **`switch`**: instelbare aan/uit-parameters. Aan schrijft `1` (of `true_value`),
  uit schrijft `0`. Wordt meegepolld en schrijft niets bij het opstarten.
- Met dank aan Robert Klep (@robertklep), wiens voorstel in PR #1 hiervoor de basis was.

### Let op bij updaten
- In beide YAML's zijn zeven waarden van `sensor` naar `binary_sensor` verhuisd: HM007,
  HM030, HM008, HM009, AM015 en de vlaggen 0x502E:1 en 0x502E:7. In Home Assistant
  krijgen ze daardoor een nieuwe entiteit (`binary_sensor.…` in plaats van
  `sensor.…`). Pas automatiseringen en dashboards aan en verwijder de oude, nu
  onbeschikbare sensoren.

### Overig
- Repository hernoemd naar `esphome-remeha-ble`. De oude naam stuurt automatisch door.
