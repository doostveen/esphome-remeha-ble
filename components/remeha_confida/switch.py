# ----------------------------------------------------------------------------
#  switch platform: a WRITABLE on/off parameter, e.g. a YesNo/OffOn enum.
#  Creating one does two things:
#   1. a RemehaSwitch whose write_state() builds a write frame (op 0x04):
#      on = true_value (default 1), off = 0;
#   2. a RemehaItem added to the hub's poll list (switch_=var) so the switch
#      also shows the ACTUAL read-back state, not just the last value written.
#
#  restore_mode defaults to DISABLED: the switch never writes on boot, it only
#  shows what the appliance reports. A switch changes a real appliance setting.
#
#  Based on the switch proposal by Robert Klep (PR #1).
# ----------------------------------------------------------------------------
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import switch
from . import (
    remeha_ns, RemehaConfida, RemehaSwitch, VALUE_TYPES, READ_MODES,
    CONF_REMEHA_ID, CONF_NODE, CONF_INDEX, CONF_SUBINDEX, CONF_READ,
    CONF_TRUE_VALUE,
)

DEPENDENCIES = ["remeha_confida"]

CONFIG_SCHEMA = (
    switch.switch_schema(RemehaSwitch, default_restore_mode="DISABLED")
    .extend(
        {
            cv.GenerateID(CONF_REMEHA_ID): cv.use_id(RemehaConfida),
            cv.Optional(CONF_NODE, default=1): cv.hex_uint8_t,
            cv.Required(CONF_INDEX): cv.hex_uint16_t,
            cv.Optional(CONF_SUBINDEX, default=0): cv.hex_uint8_t,
            cv.Optional(CONF_TRUE_VALUE): cv.int_range(min=1, max=255),
            cv.Optional(CONF_READ, default="bulk"): cv.enum(READ_MODES, lower=True),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_REMEHA_ID])
    var = await switch.new_switch(config)
    await cg.register_component(var, config)
    cg.add(var.set_parent(hub))
    cg.add(var.set_node(config[CONF_NODE]))
    cg.add(var.set_index(config[CONF_INDEX]))
    cg.add(var.set_sub(config[CONF_SUBINDEX]))
    cg.add(var.set_true_value(config.get(CONF_TRUE_VALUE, 1)))
    # Also poll this object so the switch shows the ACTUAL current state (read-back).
    item = cg.StructInitializer(
        remeha_ns.struct("RemehaItem"),
        ("node", config[CONF_NODE]),
        ("index", config[CONF_INDEX]),
        ("sub", config[CONF_SUBINDEX]),
        ("type", VALUE_TYPES["enum"]),
        ("gain", 1.0),
        ("switch_", var),
        ("has_true_value", CONF_TRUE_VALUE in config),
        ("true_value", config.get(CONF_TRUE_VALUE, 1)),
        ("single", config[CONF_READ]),
    )
    cg.add(hub.add_item(item))
