from zkevm_specs.opcode.storage import Storage

OP_SLOAD = 0x54
OP_SSTORE = 0x55

@is_circuit_code
def check_storage_ops(
    opcode: U8,
    storage: Storage,
):
    # TODO:
