# ----------------------------------------------------------------------------
#  Built-in codebook (compile time only, nothing of this ends up on the ESP).
#
#  Lets an entity be declared with just the appliance code, e.g.
#      - platform: remeha_ble
#        code: HM001
#  and fills in index, subindex, value_type, gain, unit, device/state class,
#  accuracy and a Dutch name from codebook.json (generated from
#  data/Remeha_parametercodeboek.xlsx by tools/gen_codebook_json.py).
#  Anything set explicitly in the YAML always wins over the codebook.
# ----------------------------------------------------------------------------
import json
import math
import pathlib

import esphome.config_validation as cv

CONF_CODE = "code"

_DB = None


def _db():
    global _DB
    if _DB is None:
        path = pathlib.Path(__file__).with_name("codebook.json")
        _DB = json.loads(path.read_text(encoding="utf-8"))
    return _DB


def lookup(code):
    code = str(code).strip().upper()
    e = _db().get(code)
    if e is None:
        raise cv.Invalid(f"code '{code}' staat niet in het codeboek; gebruik index/subindex")
    if e.get("dup"):
        raise cv.Invalid(f"code '{code}' komt meerdere keren voor in het codeboek; gebruik index/subindex")
    return code, e


# OBD datatype -> component value_type
_VT = {"U8": "u8", "I8": "i8", "U16": "u16", "I16": "i16", "U32": "u32", "I32": "i32", "Enum": "enum"}
_NUMERIC = set(_VT)

# codebook unit -> (HA unit, device_class)
_UNITS = {
    "°C": ("°C", "temperature"),
    "K": ("K", None),
    "%": ("%", None),
    "bar": ("bar", "pressure"),
    "kPa": ("kPa", "pressure"),
    "Pa": ("Pa", "pressure"),
    "kW": ("kW", "power"),
    "W": ("W", "power"),
    "kWh": ("kWh", "energy"),
    "Wh": ("Wh", "energy"),
    "V": ("V", "voltage"),
    "A": ("A", "current"),
    "µA": ("µA", "current"),
    "Hz": ("Hz", "frequency"),
    "Rpm": ("rpm", None),
    "l/m": ("L/min", "volume_flow_rate"),
    "l": ("L", "water"),
    "Hours": ("h", "duration"),
    "Min": ("min", "duration"),
    "Sec": ("s", "duration"),
    "mSec": ("ms", "duration"),
    "Days": ("d", "duration"),
    "ppm": ("ppm", None),
}


def _decimals(gain):
    if gain >= 1:
        return 0
    return max(0, min(4, int(round(-math.log10(gain)))))


def _type_range(t, gain):
    lo, hi = {"U8": (0, 255), "I8": (-128, 127), "U16": (0, 65535), "I16": (-32768, 32767),
              "U32": (0, 4294967295), "I32": (-2147483648, 2147483647)}.get(t, (0, 255))
    return lo * gain, hi * gain


def enum_choices(e):
    """[(raw, text)] with unique texts (select needs unique options)."""
    seen, out = set(), []
    for raw, txt in e.get("e", []):
        t = txt or str(raw)
        if t in seen:
            t = f"{t} ({raw})"
        seen.add(t)
        out.append((int(raw), t))
    return out


def apply_code(platform):
    """Validator (run BEFORE the platform schema) that fills defaults from `code:`."""

    def validator(config):
        if not isinstance(config, dict) or CONF_CODE not in config:
            return config
        code, e = lookup(config[CONF_CODE])
        c = dict(config)
        kind, t, gain = e["k"], e["t"], float(e["g"])
        soort = {"P": "Parameter", "S": "Signal", "C": "Counter"}.get(kind, kind)

        def default(key, value):
            if key not in c and value is not None:
                c[key] = value

        default("name", f"{e['n']} ({code})")
        default("index", e["i"])
        default("subindex", 1 if e["a"] else e["s"])
        default("read", "auto")

        unit, dev_class = _UNITS.get(e["u"], (e["u"] or None, None))

        if platform == "sensor":
            if t not in _NUMERIC:
                hint = "text_sensor" if t == "VisibleString" else "geen ondersteund platform"
                raise cv.Invalid(f"{code} heeft datatype {t}: niet als sensor te lezen ({hint})")
            default("value_type", _VT[t])
            default("gain", gain)
            default("unit_of_measurement", unit)
            default("accuracy_decimals", _decimals(gain))
            if kind == "C":
                default("state_class", "total_increasing")
                default("device_class", dev_class if dev_class in ("energy", "water", "duration") else None)
            elif t != "Enum":
                default("state_class", "measurement")
                default("device_class", dev_class if dev_class != "energy" else None)
        elif platform == "number":
            if kind != "P":
                raise cv.Invalid(f"{code} is geen instelbare parameter (Soort={soort}); gebruik sensor")
            if t == "Enum":
                raise cv.Invalid(f"{code} is een keuzelijst; gebruik select (of switch bij aan/uit)")
            if t not in _NUMERIC:
                raise cv.Invalid(f"{code} heeft datatype {t}: niet als number te gebruiken")
            lo, hi = _type_range(t, gain)
            default("value_type", _VT[t])
            default("gain", gain)
            default("unit_of_measurement", unit)
            default("device_class", dev_class if dev_class in ("temperature", "pressure", "power") else None)
            default("min_value", lo)
            default("max_value", hi)
            default("step", gain)
            default("mode", "box")
            default("entity_category", "config")
        elif platform in ("select", "switch"):
            if kind != "P":
                raise cv.Invalid(f"{code} is geen instelbare parameter (Soort={soort}); "
                                 f"gebruik {'text_sensor' if platform == 'select' else 'binary_sensor'}")
            if t != "Enum":
                raise cv.Invalid(f"{code} is geen keuzelijst (datatype {t}); gebruik number")
            default("entity_category", "config")
        elif platform == "binary_sensor":
            if t not in _NUMERIC:
                raise cv.Invalid(f"{code} heeft datatype {t}: niet als binary_sensor te lezen")
        elif platform == "text_sensor":
            if t not in ("Enum", "VisibleString"):
                raise cv.Invalid(f"{code} heeft datatype {t}: text_sensor kan alleen Enum of VisibleString")
        return c

    return validator


def code_entry(config):
    """Codebook entry for a validated config, or None when no code was used."""
    if CONF_CODE not in config:
        return None
    return lookup(config[CONF_CODE])[1]
