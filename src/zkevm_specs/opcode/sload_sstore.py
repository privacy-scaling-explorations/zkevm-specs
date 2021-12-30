from zkevm_specs.opcode.storage import Storage
from ..encoding import U256, is_circuit_code

OP_SLOAD = 0x54
OP_SSTORE = 0x55

@is_circuit_code
def check_storage_ops(
    opcode: U8,
    storage: Storage,
    address: U256,
    value: U256,
):
    # TODO:
