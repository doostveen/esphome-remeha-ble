# ----------------------------------------------------------------------------
#  select platform: a WRITABLE enum parameter shown as a choice list with texts
#  (e.g. CP780 Regelstrategie: Automatisch / Ruimteregeling / Weersafhankelijk /
#  Buiten&ruimte gebas.). Like number/switch it does two things:
#   1. a RemehaSelect whose control() writes the raw choice number (op 0x04);
#   2. a RemehaItem on the hub's poll list (select_=var) so the select shows the
#      appliance's ACTUAL choice (read-back), translated to its text.
#
#  Texts come from the codebook (`code: CP780`) or from `options:` in the YAML.
#  A select changes a real appliance setting.
# ----------------------------------------------------------------------------
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import select
from . import (
    remeha_ns, RemehaBle, RemehaSelect, READ_MODES, read_fields, enum_map_expr,
    CONF_REMEHA_ID, CONF_NODE, CONF_INDEX, CONF_SUBINDEX, CONF_READ,
)
from .codebook import CONF_CODE, apply_code, code_entry, enum_choices

DEPENDENCIES = ["remeha_ble"]
CONF_OPTIONS = "options"


def _need_options(config):
    if CONF_OPTIONS not in config and CONF_CODE not in config:
        raise cv.Invalid("select heeft 'code:' of 'options:' nodig")
    return config


CONFIG_SCHEMA = cv.All(
    apply_code("select"),
    select.select_schema(RemehaSelect)
    .extend(
        {
            cv.GenerateID(CONF_REMEHA_ID): cv.use_id(RemehaBle),
            cv.Optional(CONF_CODE): cv.string,
            cv.Optional(CONF_NODE, default=1): cv.hex_uint8_t,
            cv.Required(CONF_INDEX): cv.hex_uint16_t,
            cv.Optional(CONF_SUBINDEX, default=0): cv.hex_uint8_t,
            cv.Optional(CONF_READ, default="bulk"): cv.enum(READ_MODES, lower=True),
            # Own choices {raw: "text"}; overrides the codebook. Also restricts the
            # list, e.g. to hide choices your appliance does not support.
            cv.Optional(CONF_OPTIONS): cv.Schema({cv.int_: cv.string}),
        }
    )
    .extend(cv.COMPONENT_SCHEMA),
    _need_options,
)


async def to_code(config):
    if CONF_OPTIONS in config:
        choices = sorted(config[CONF_OPTIONS].items())
    else:
        choices = enum_choices(code_entry(config))
    if not choices:
        raise cv.Invalid("geen keuzes gevonden voor deze select")
    hub = await cg.get_variable(config[CONF_REMEHA_ID])
    var = await select.new_select(config, options=[t for _, t in choices])
    await cg.register_component(var, config)
    cg.add(var.set_parent(hub))
    cg.add(var.set_node(config[CONF_NODE]))
    cg.add(var.set_index(config[CONF_INDEX]))
    cg.add(var.set_sub(config[CONF_SUBINDEX]))
    cg.add(var.set_enum_map(enum_map_expr(choices)))
    item = cg.StructInitializer(
        remeha_ns.struct("RemehaItem"),
        ("node", config[CONF_NODE]),
        ("index", config[CONF_INDEX]),
        ("sub", config[CONF_SUBINDEX]),
        ("type", remeha_ns.enum("ValueType").VT_ENUM),
        ("gain", 1.0),
        ("select_", var),
        ("enum_map", enum_map_expr(choices)),
        *read_fields(config),
    )
    cg.add(hub.add_item(item))
