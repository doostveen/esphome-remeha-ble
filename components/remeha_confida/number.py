# ----------------------------------------------------------------------------
#  number platform: a WRITABLE parameter. Creating one does two things:
#   1. a RemehaNumber whose control() builds a write frame (op 0x04) on change;
#   2. a RemehaItem added to the hub's poll list (number=var) so the number also
#      shows the ACTUAL read-back value, not just the last value written.
#  The platform is unit-agnostic: set unit_of_measurement / device_class per
#  number in YAML. min/max/step are HA UI guards only (not enforced on the wire).
# ----------------------------------------------------------------------------
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import number
from esphome.const import CONF_MIN_VALUE, CONF_MAX_VALUE, CONF_STEP
from . import (
    remeha_ns, RemehaConfida, RemehaNumber, VALUE_TYPES, READ_MODES, read_fields,
    CONF_REMEHA_ID, CONF_NODE, CONF_INDEX, CONF_SUBINDEX, CONF_TYPE, CONF_GAIN, CONF_READ,
)
from .codebook import CONF_CODE, apply_code

DEPENDENCIES = ["remeha_confida"]
CONF_DEVICE_LIMITS = "device_limits"

CONFIG_SCHEMA = cv.All(
    # `code: CP230` fills index/value_type/gain/unit/name and the technical
    # min/max from the codebook (explicit YAML fields win).
    apply_code("number"),
    # No hardcoded unit/device_class: each number sets its own in YAML
    # (unit_of_measurement / device_class), so the platform is generic.
    number.number_schema(RemehaNumber)
    .extend(
        {
            cv.GenerateID(CONF_REMEHA_ID): cv.use_id(RemehaConfida),
            cv.Optional(CONF_CODE): cv.string,
            cv.Optional(CONF_NODE, default=1): cv.hex_uint8_t,
            cv.Required(CONF_INDEX): cv.hex_uint16_t,
            cv.Optional(CONF_SUBINDEX, default=0): cv.hex_uint8_t,
            cv.Required(CONF_TYPE): cv.enum(VALUE_TYPES, lower=True),
            cv.Optional(CONF_GAIN, default=1.0): cv.float_,
            cv.Optional(CONF_MIN_VALUE, default=0.0): cv.float_,
            cv.Optional(CONF_MAX_VALUE, default=100.0): cv.float_,
            cv.Optional(CONF_STEP, default=1.0): cv.float_,
            cv.Optional(CONF_READ, default="bulk"): cv.enum(READ_MODES, lower=True),
            # Use the appliance's own min/max/step (menu descriptor 0x502B) once known.
            cv.Optional(CONF_DEVICE_LIMITS, default=True): cv.boolean,
        }
    )
    .extend(cv.COMPONENT_SCHEMA),
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_REMEHA_ID])
    var = await number.new_number(
        config,
        min_value=config[CONF_MIN_VALUE],
        max_value=config[CONF_MAX_VALUE],
        step=config[CONF_STEP],
    )
    await cg.register_component(var, config)
    cg.add(var.set_parent(hub))
    cg.add(var.set_node(config[CONF_NODE]))
    cg.add(var.set_index(config[CONF_INDEX]))
    cg.add(var.set_sub(config[CONF_SUBINDEX]))
    cg.add(var.set_value_type(config[CONF_TYPE]))
    cg.add(var.set_gain(config[CONF_GAIN]))
    cg.add(var.set_use_device_limits(config[CONF_DEVICE_LIMITS]))
    # Also poll this object so the number shows the ACTUAL current value (read-back).
    item = cg.StructInitializer(
        remeha_ns.struct("RemehaItem"),
        ("node", config[CONF_NODE]),
        ("index", config[CONF_INDEX]),
        ("sub", config[CONF_SUBINDEX]),
        ("type", config[CONF_TYPE]),
        ("gain", config[CONF_GAIN]),
        ("number", var),
        *read_fields(config),
    )
    cg.add(hub.add_item(item))
