# Data — codeboek

Naslag bij de ESPHome-component: welke CAN-objecten er zijn, hoe je ze decodeert,
welke keuzes een enum-parameter heeft en welke foutcodes bestaan. Hiermee zoek je
objecten op als je zelf een sensor of parameter aan de YAML wilt toevoegen (zie de
README in de hoofdmap).

## Bestanden

| bestand | inhoud |
|---|---|
| **`Remeha_parametercodeboek.xlsx`** | Het codeboek: 3 tabbladen met Nederlandse namen. Zie hieronder. |

### Tabbladen in het codeboek

| tabblad | rijen | inhoud |
|---|---|---|
| **Parameters** | 3092 | Alle objecten van het protocol, van álle toestellen die het gebruiken (dus ook bijvoorbeeld cv-ketels), niet alleen de Confida. Per object: index, subindex, code, Nederlandse naam, soort, datatype, gain, eenheid, enum, technisch bereik, hoe je het uitleest, wetenswaardigheden en functiegroep. |
| **Enums** | 1160 | Keuzelijsten voor enum-parameters: waarde → Nederlandse omschrijving. |
| **Foutcodes** | 1986 | De foutcodes in 24 categorieën, weergave `H{categorie}.{nummer}`, met korte Nederlandse omschrijving. |

## Andere Remeha-toestellen

Omdat het codeboek alle objecten van het protocol bevat, is het mogelijk ook bruikbaar
voor **andere Remeha-toestellen met Bluetooth** die hetzelfde protocol spreken. Dat is
niet getest.

**Niet elk object bestaat op elk toestel.** Een Confida 40 gebruikt er een paar
honderd. Of jouw toestel een object kent, zie je in de ESPHome-log: krijg je een echte
waarde terug, of een foutmelding / `0` / `-327,68`?

## Kolom "Soort"

`Soort` bepaalt of een object een instelling of een meetwaarde is, en daarmee of het
onder `sensor:` of `number:` in de YAML hoort: `Parameter` = instelbaar (`number`, of
alleen-lezen als `sensor`), `Signal` = live meetwaarde (`sensor`), `Counter` = oplopende
teller (`sensor` met `state_class: total_increasing`). Er is bewust géén "schrijfbaar"-
kolom: de alleen-lezen-vlag in het object-woordenboek markeert ook meetwaarden als
schrijfbaar en is dus onbetrouwbaar.

## Kolom "Uitlezen"

"bulk GetList" = het object zit in de standaard lijst die de component elke ronde
ophaalt; in de YAML hoef je niets te doen (`read: bulk` is standaard). "individuele
read" = het object zit vaak niet in die lijst (meestal instellingen); zet dan
`read: single` in de YAML, zodat de component het los uitleest.

> De numerieke min/max/stap van parameters staan niet in het codeboek. **Bereik
> (technisch)** is alleen de theoretische range van het datatype × gain. Het toestel
> stuurt de echte grenzen wel zelf (object `0x502B`), maar de component leest die nog
> niet uit. De `min_value`/`max_value` in de YAML zijn daarom grenzen voor de
> Home Assistant-interface; het toestel weigert een ongeldige waarde zelf.
