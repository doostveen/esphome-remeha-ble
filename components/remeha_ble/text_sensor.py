# ----------------------------------------------------------------------------
#  text_sensor platform: a read-only TEXT value.
#   - a string object (e.g. the device name at 0x300F): the raw bytes are
#     published verbatim up to the first NUL;
#   - an enum (when declared with `code:` of an Enum, or with `options:`): the
#     raw choice number is published as its text, e.g. "Weersafhankelijk".
# ----------------------------------------------------------------------------
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text_sensor
from . import (
    remeha_ns, RemehaBle, READ_MODES, read_fields, enum_map_expr,
    CONF_REMEHA_ID, CONF_NODE, CONF_INDEX, CONF_SUBINDEX, CONF_READ,
)
from .codebook import CONF_CODE, apply_code, code_entry, enum_choices

DEPENDENCIES = ["remeha_ble"]
CONF_OPTIONS = "options"

CONFIG_SCHEMA = cv.All(
    apply_code("text_sensor"),
    text_sensor.text_sensor_schema().extend(
        {
            cv.GenerateID(CONF_REMEHA_ID): cv.use_id(RemehaBle),
            cv.Optional(CONF_CODE): cv.string,
            cv.Optional(CONF_NODE, default=1): cv.hex_uint8_t,
            cv.Required(CONF_INDEX): cv.hex_uint16_t,
            cv.Optional(CONF_SUBINDEX, default=0): cv.hex_uint8_t,
            cv.Optional(CONF_READ, default="bulk"): cv.enum(READ_MODES, lower=True),
            # Own enum texts: {0: "Uit", 1: "Aan"}; overrides the codebook texts.
            cv.Optional(CONF_OPTIONS): cv.Schema({cv.int_: cv.string}),
        }
    ),
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_REMEHA_ID])
    ts = await text_sensor.new_text_sensor(config)
    choices = None
    if CONF_OPTIONS in config:
        choices = sorted(config[CONF_OPTIONS].items())
    else:
        e = code_entry(config)
        if e is not None and e["t"] == "Enum":
            choices = enum_choices(e)
    fields = [
        ("node", config[CONF_NODE]),
        ("index", config[CONF_INDEX]),
        ("sub", config[CONF_SUBINDEX]),
        ("type", remeha_ns.enum("ValueType").VT_ENUM if choices else remeha_ns.enum("ValueType").VT_U8),
        ("gain", 1.0),
        ("text_sensor", ts),
    ]
    if choices:
        fields.append(("enum_map", enum_map_expr(choices)))
    item = cg.StructInitializer(remeha_ns.struct("RemehaItem"), *fields, *read_fields(config))
    cg.add(hub.add_item(item))
