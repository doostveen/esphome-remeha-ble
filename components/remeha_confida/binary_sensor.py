# ----------------------------------------------------------------------------
#  binary_sensor platform: a read-only ON/OFF value, e.g. a YesNo/OffOn enum
#  (0/1) or a status flag (0/0xFF). Each entry binds one appliance object
#  (node/index/subindex) to an HA binary sensor and is registered as a
#  RemehaItem on the hub so update() polls it. `read: single` fetches it with
#  an individual request instead of the bulk GetList.
#
#  By default any non-zero raw value is "on". Set `true_value` when only one
#  specific raw value should count as on (other values are then "off").
#  To invert, use the standard binary_sensor filter `filters: [invert]`.
#
#  Based on the binary_sensor proposal by Robert Klep (PR #1).
# ----------------------------------------------------------------------------
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from . import (
    remeha_ns, RemehaConfida, VALUE_TYPES, READ_MODES, read_fields,
    CONF_REMEHA_ID, CONF_NODE, CONF_INDEX, CONF_SUBINDEX, CONF_TYPE, CONF_READ,
    CONF_TRUE_VALUE,
)
from .codebook import CONF_CODE, apply_code

DEPENDENCIES = ["remeha_confida"]

CONFIG_SCHEMA = cv.All(apply_code("binary_sensor"), binary_sensor.binary_sensor_schema().extend(
    {
        cv.GenerateID(CONF_REMEHA_ID): cv.use_id(RemehaConfida),
        cv.Optional(CONF_CODE): cv.string,
        cv.Optional(CONF_NODE, default=1): cv.hex_uint8_t,
        cv.Required(CONF_INDEX): cv.hex_uint16_t,
        cv.Optional(CONF_SUBINDEX, default=0): cv.hex_uint8_t,
        # 1-byte value by default (enums and flags); override for wider objects.
        cv.Optional(CONF_TYPE, default="enum"): cv.enum(VALUE_TYPES, lower=True),
        cv.Optional(CONF_TRUE_VALUE): cv.int_range(min=0, max=255),
        cv.Optional(CONF_READ, default="bulk"): cv.enum(READ_MODES, lower=True),
    }
))


async def to_code(config):
    hub = await cg.get_variable(config[CONF_REMEHA_ID])
    sens = await binary_sensor.new_binary_sensor(config)
    item = cg.StructInitializer(
        remeha_ns.struct("RemehaItem"),
        ("node", config[CONF_NODE]),
        ("index", config[CONF_INDEX]),
        ("sub", config[CONF_SUBINDEX]),
        ("type", config[CONF_TYPE]),
        ("gain", 1.0),
        ("binary_sensor", sens),
        ("has_true_value", CONF_TRUE_VALUE in config),
        ("true_value", config.get(CONF_TRUE_VALUE, 1)),
        *read_fields(config),
    )
    cg.add(hub.add_item(item))
