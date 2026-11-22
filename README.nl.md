[English](README.md) | **Nederlands** | [Deutsch](README.de.md)

# ESPHome Remeha BLE

Lees en bedien een **Remeha**-warmtepomp of -ketel vanuit **Home Assistant** via
**Bluetooth**, met een ESP32 met ESPHome. Geen gateway, geen cloud: de ESP spreekt het
eigen Bluetooth-protocol van het toestel en geeft temperaturen, drukken, debiet,
vermogen, COP, tellers en status door aan Home Assistant. Instellingen zoals de stooklijn
kun je ook wijzigen.

Wat je ziet, bepaal je zelf: de ESP scant wat **jouw** toestel kan en een ingebouwde
webpagina, de **configurator**, maakt van je keuze een complete ESPHome-YAML.

- Werkt met beide Bluetooth-routes van Remeha: de **ingebouwde Bluetooth**-module
  (adverteert als `EHC-...`, bv. Confida 40) en de **GTW-IoT home-hub** (adverteert als
  `GTW-IOT_...`, bv. Confida 10). De component herkent de route zelf.
- Getest op een Remeha Confida 40. Andere Remeha-toestellen die hetzelfde protocol
  spreken (EHC-regelaar) werken naar verwachting ook; meld je ervaring in een issue.
- Gebruik op eigen risico. Dit project staat los van Remeha.

![De configurator op de ESP](docs/images/configurator.png)

## Wat heb je nodig

- Een **ESP32**-board (standaard `esp32dev`; pas het board in de YAML aan als je een
  ander hebt). Een ESP8266 heeft geen Bluetooth LE en werkt niet.
- **ESPHome** 2026.10 of nieuwer (los of de Home Assistant-add-on).
- Voor de ingebouwde Bluetooth: het **6-cijferige nummer van de BLE-sticker** op je
  toestel (de koppelcode). De GTW-IoT-hub heeft geen nummer nodig.

## Snel aan de slag

1. **Secrets.** Zet in de `secrets.yaml` van je ESPHome (zie
   [`secrets.yaml.example`](secrets.yaml.example)):
   ```yaml
   wifi_ssid: "JouwWifi"
   wifi_password: "JouwWifiWachtwoord"
   remeha_bt_key: "012345"   # stickernummer, tussen aanhalingstekens; GTW-IoT: "000000"
   ```
   Laat de aanhalingstekens staan: zonder leest YAML een getal met een voorloopnul als
   octaal.
2. **Eerste keer flashen.** Maak in ESPHome een nieuw apparaat met de inhoud van
   [`remeha-start.yaml`](remeha-start.yaml) en installeer het. De component wordt
   automatisch van GitHub gehaald. De ESP zoekt het toestel zelf, koppelt en toont een
   basisset waarden.
   GTW-IoT: druk kort op de knop van de hub zodat die een verbinding accepteert.
3. **Configurator.** Open `http://<ip-van-de-esp>/remeha` in je browser en druk op
   **Scan toestel**. In ongeveer een halve minuut leest de ESP welke objecten jouw
   toestel heeft, met de grenzen die het toestel zelf opgeeft.
4. **Kiezen en flashen.** Vink aan wat je wilt lezen en wat je wilt kunnen wijzigen,
   kopieer de YAML, vervang daarmee de start-YAML in ESPHome en installeer opnieuw.

### Kom je van v1.x (`remeha_confida`)?

Versie 2.0 heeft de component hernoemd naar `remeha_ble`. De snelste weg: flash de nieuwe
versie met de start-YAML, open de configurator, kies *YAML inlezen* en plak je oude YAML.
Je keuze en de namen van je entiteiten worden overgenomen. Met de hand: zie de
[CHANGELOG](CHANGELOG.md).

## De configurator

![Waarden kiezen, met twee regels opengeklapt](docs/images/configurator-choose.png)

De pagina op `http://<ip-van-de-esp>/remeha` komt van de ESP zelf.

- **Scan toestel** leest de menubeschrijving van het toestel (object 0x502B): elk object
  dat het toestel aanbiedt, met minimum, maximum, stap en toegangsniveau. Alleen lezen,
  er wordt niets geschreven.
- **Lezen** zet een waarde als sensor in Home Assistant. **Instelbaar** (oranje) voegt
  een bediening toe die een echte instelling van het toestel wijzigt; dat kan alleen bij
  instellingen die schrijfbaar zijn.
- Met **Snel aanvinken** kies je een hele groep: Basis, Energie, Buitenunit, Ruimte,
  Stooklijn. Ze zijn gemaakt op een warmtepomp en vinken alleen aan wat jouw toestel heeft.
- Objecten met meerdere elementen (per groep, per activiteit, per producent) staan op
  één regel met een **+** om de elementen te tonen (zie *Regels met een +* hieronder).
- Met de knop in de kolom **Waarde** lees je de huidige waarde van dat object één keer
  uit. Zo zie je vóór het aanvinken of het op jouw toestel iets zinnigs geeft.
- **Zoeken en filteren** op code, naam, groep, soort en niveau.
- **Begin bij je huidige keuze:** *Keuze van deze ESP overnemen* vinkt aan wat de
  firmware nu uitleest; *YAML inlezen* neemt de remeha_ble-entiteiten over uit een
  YAML die je plakt, inclusief namen die je zelf hebt gegeven.
- **Talen:** Nederlands, Engels en Duits. De taal bepaalt ook de entiteitnamen en
  keuzeteksten in de YAML die je krijgt.
- **Waarschuwen als deze YAML op een ander type toestel draait:** zet het artikelnummer
  van het gescande toestel in de YAML. Sluit je de ESP later aan op een ander type, dan
  meldt de log dat en zie je het bij de entiteit *Remeha toestel*.

### Regels met een +

Sommige objecten zijn geen losse waarde maar een korte rij waarden onder één code,
bijvoorbeeld één per groep. Zo'n object krijgt één regel met **+** en het aantal
elementen (`CP000 2×`). Druk op **+** om de elementen eronder te tonen, elk met een
label:

- **groep 1, groep 2:** groepsobjecten (codes die met C beginnen, zoals de stooklijn en
  de ruimtetemperaturen).
- **activiteit 1 tot 6:** de ruimtesetpunten per activiteit van het klokprogramma
  (CP080, CP140); met meer groepen zie je *groep 2, activiteit 1* enzovoort.
- **producent 1, producent 2:** energietellers per producent. Producent 1 is de
  warmtepomp; producent 2 is waarschijnlijk de bijverwarming.

De vinkjes op de regel met **+** kiezen of wissen alle elementen tegelijk; een half
gevuld vakje betekent dat er maar een deel gekozen is. Je kunt ook losse elementen
aanvinken. Heeft een print maar één element van een object, dan staat het als gewone
regel met het elementnummer, zoals `CP000:1`.

Dezelfde code kan op twee regels staan met een andere **Print**: de *regelaar*
(node 1) en de *uitbreidingsprint* (node 4) hebben elk een eigen kopie van veel
objecten. Voor de meeste installaties wil je die van de regelaar.

### Objecten buiten het menu

De scan laat zien wat het toestel in zijn eigen menubeschrijving opgeeft: het menu van
het display. De Remeha-app toont meer, bijvoorbeeld de verdamper- en
condensortemperatuur van de buitenunit. Bijna al die objecten staan in het codeboek,
en je krijgt ze op twee manieren in de configurator:

- **+ Uit codeboek** opent een zoekvak op code, index of naam. **Lees** laat meteen
  zien of het object op jouw toestel bestaat; **Toevoegen** zet het als regel met
  *buiten menu* in de tabel. Een code uit de Remeha-app die niet in het codeboek staat,
  zoals `AC089` of `CP083`, is meestal een element van een lijst (`AC088` element 2,
  `CP080` activiteit 4); het zoekvak meldt dat.
- **Zoek buiten het menu** laat de ESP elk codeboekobject proberen dat niet in het
  menu staat (alleen lezen). Stap 1 vraagt de meetwaarden en tellers op in groepjes
  van 32 en duurt ongeveer een minuut; stap 2 leest de overige instellingen een
  voor een en duurt een paar minuten. Zolang dat loopt, staat het gewone uitlezen
  stil. Alles wat een waarde geeft, komt erbij als *buiten menu*; kies *Tonen: alleen
  buiten menu* om ze te zien.

Een object buiten het menu heeft geen grenzen van het toestel: een instelbare entiteit
ervoor kent geen minimum of maximum van het toestel, dus maak die alleen als je weet
wat de instelling doet.

De configurator staat aan met `configurator: true` onder `remeha_ble:` en heeft
`web_server:` nodig. Hij kost ongeveer 150 kB flash; zet hem op `false` als je klaar
bent en die ruimte nodig hebt.

## De YAML in het kort

De configurator schrijft het hele bestand, maar het helpt om te weten wat erin staat.

![De gemaakte YAML](docs/images/configurator-yaml.png)

```yaml
remeha_ble:
  id: remeha
  ble_client_id: remeha_client
  passkey: !secret remeha_bt_key   # ingebouwde Bluetooth; genegeerd bij de GTW-IoT
  appliance:
    name: "Remeha toestel"         # herkend toestel (artikelnummer en naam)
  configurator: true               # pagina op http://<ip-van-de-esp>/remeha

sensor:
  - platform: remeha_ble
    code: HM001                    # aanvoertemperatuur warmtepomp
  - platform: remeha_ble
    code: HM116
    name: "Hogedruk"               # wat je zelf invult, gaat voor

number:
  - platform: remeha_ble
    code: CP230                    # hellingshoek stooklijn (wijzigt het toestel!)
```

- **`code:`** is de toestelcode uit het codeboek (bijvoorbeeld `HM001`). Index,
  subindex, datatype, schaal, eenheid, Home Assistant-klassen en een naam worden
  automatisch ingevuld.
- **Welk platform?** `sensor` voor getallen, `text_sensor` voor een keuzelijst als tekst,
  `binary_sensor` voor aan/uit, `number` voor een instelbaar getal, `select` voor een
  instelbare keuzelijst, `switch` voor een instelbare aan/uit-waarde. ESPHome meldt het
  als een platform niet bij het object past.
- **`subindex:`** kiest een element van een array-object (groep, producent); **`node:`**
  een andere print in het toestel (1 = regelaar, 4 = uitbreidingsprint).
- **Grenzen uit het toestel:** een `number` neemt het echte minimum, maximum en de stap
  van het toestel over en weigert waarden daarbuiten; een `select` weigert keuzes die het
  toestel niet toestaat. Zet `device_limits: false` op een `number` om dit uit te zetten.
- **Objecten zonder code** voeg je toe met `index:`, `subindex:` en `value_type:`; zie
  het codeboek in [`data/`](data/README.md).

### Verbindingsopties

| optie | betekenis |
|---|---|
| `passkey` | het stickernummer (ingebouwde Bluetooth) |
| `connection` | `auto` (standaard): route herkennen aan de naam; `paired` of `plain` om hem vast te zetten |
| `device_name_prefix` | alleen verbinden met een apparaat waarvan de naam hiermee begint (standaard: `EHC-` of `GTW-IOT`) |
| `ble_mac` (substitution) | `00:00:00:00:00:00` zoekt het toestel automatisch; heb je meerdere toestellen in bereik, vul dan het MAC uit de log in (`BLE gezien: ...`) |
| `expected_article_number` | waarschuwen als het verbonden toestel een ander type is |
| `update_interval` | hoe vaak de waarden worden gelezen (standaard 30 s) |

Diagnose-entiteiten: `write_result` (laatste schrijfactie, geaccepteerd of geweigerd met
reden), `reconnect_reason` en `reconnect_count`.

### De schakelaar "Remeha uitlezing"

Er kan maar **één** Bluetooth-verbinding tegelijk met het toestel zijn. Zet *Remeha
uitlezing* uit om de ESP de verbinding te laten loslaten en te laten stoppen met
herverbinden, zodat een telefoon-app of servicetool kan verbinden. Zet hem weer aan om
verder te gaan. Na een herstart staat hij aan.

## Instellingen wijzigen: wees voorzichtig

Een instelbare entiteit (`number`, `select`, `switch`) wijzigt een **echte instelling**
van het toestel. Gebruik dat alleen als je weet wat de instelling doet. Na elke
schrijfactie leest de ESP de waarde terug, zodat de entiteit toont wat er echt in het
toestel staat. Een geweigerde schrijfactie zie je met de reden bij de entiteit *laatste
schrijfresultaat*.

## Problemen oplossen

- **Koppelen mislukt / "auth fail":** bijna altijd een verkeerde passkey. Controleer
  `remeha_bt_key` en de aanhalingstekens. In de opstartlog staat `passkey ****xx` met de
  laatste twee cijfers.
- **Na een verkeerde passkey blijft het mislukken:** het toestel blokkeert nieuwe
  pogingen 60 s. De component wacht steeds langer (90 s, 3, 5, 10 min). Even geduld in
  plaats van herstarten.
- **GTW-IoT wordt niet gevonden:** druk kort op de knop van de hub en zorg dat de
  Remeha-app niet tegelijk verbonden is. De log toont
  `route herkend aan de naam: GTW-IoT (zonder koppelen)` als hij herkend is.
- **Een telefoon kan niet verbinden:** de ESP is verbonden. Zet *Remeha uitlezing* uit.
- **Ingebouwde Bluetooth onthoudt 3 apparaten:** koppel je een vierde, dan vergeet hij
  het oudste.
- **Een waarde blijft leeg:** niet elk object bestaat op elk toestel. Objecten die het
  toestel niet kent, worden één keer in de log gemeld en daarna niet meer opgevraagd.

## Hoe het werkt

Koppelen, de twee challenge/response-gates, het frameformaat en de lees- en
schrijfoperaties staan in [`docs/readme.md`](docs/readme.md). Het codeboek met alle
objecten, keuzelijsten en foutcodes staat in [`data/`](data/README.md).

## Mapindeling

```
remeha-start.yaml           eerste flash: verbindt, basisset, configurator aan
components/remeha_ble/  de ESPHome external component
data/                       codeboek: objecten, keuzelijsten, foutcodes, vertalingen
docs/readme.md              beschrijving van het protocol
tools/                      scripts die codebook.json en de configurator-pagina bouwen
secrets.yaml.example        voorbeeld-secrets.yaml
CHANGELOG.md                wijzigingen per versie
LICENSE                     MIT-licentie
```

## Wijzigingen

Zie [CHANGELOG.md](CHANGELOG.md).

## Licentie

De code valt onder de [MIT-licentie](LICENSE). Het codeboek in [`data/`](data/README.md)
is naslag zonder garantie; het is niet officieel en niet gemaakt of goedgekeurd door
Remeha. Merknamen zijn van hun eigenaars.
