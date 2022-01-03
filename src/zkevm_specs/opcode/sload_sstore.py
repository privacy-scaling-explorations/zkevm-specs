from zkevm_specs.opcode.storage import Storage
from ..encoding import U256, is_circuit_code

OP_SLOAD = 0x54
OP_SSTORE = 0x55


# storage gas cost calculation based on EIP-150
# https://github.com/djrtwo/evm-opcode-gas-costs/blob/master/opcode-gas-costs_EIP-150_revision-1e18248_2017-04-12.csv
@is_circuit_code
def calc_storage_gas_cost(
    address: U256,
    value: U256,
    is_write: bool,
) -> U128:
    if is_write:
        return ((value != 0) && (address == 0)) ? 20000 : 5000  
    else:
        return 200

@is_circuit_code
def check_storage_ops(
    opcode: U8,
    storage: Storage,
    address: U256,
    value: U256,
):
    # Check if this is an SLOAD, SSTORE
    is_sload = opcode == OP_SLOAD
    is_sstore = 1 - is_sload

    # TODO: storage gas after Berlin fork depends on warm/cold address and read/write,
    # we use static gas (EIP-150 revision) for now
    gas_cost = calc_storage_gas_cost(address, value, is_sstore)

    storage.op(address, value, is_sstore)
