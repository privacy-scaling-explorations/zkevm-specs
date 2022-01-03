from zkevm_specs.opcode.storage import Storage
from ..encoding import U256, is_circuit_code

OP_SLOAD = 0x54
OP_SSTORE = 0x55


@is_circuit_code
def calc_storage_gas_cost(
    is_write: bool,
) -> U128:
    if is_write:
        return 1
    else:
        return 2

@is_circuit_code
def check_storage_ops(
    opcode: U8,
    storage: Storage,
    address: U256,
    value: U256,
):
    # TODO:

    # Check if this is an SLOAD, SSTORE
    is_sload = opcode == OP_SLOAD
    is_sstore = 1 - is_sload

    # TODO: storage gas after XXX fork depends on warm/cold address and read/write,
    # we use static gas for now
    gas_cost = calc_storage_gas_cost(is_sstore)

    storage.op(address, value, is_sstore)
