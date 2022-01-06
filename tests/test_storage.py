from zkevm_specs.encoding import u256_to_u8s
from zkevm_specs.opcode.storage import Storage
from zkevm_specs.opcode.sload_sstore import *


def test_check_storage_ops():
    storage = Storage()
    z8s = u256_to_u8s(0)

    # Load a value from key 0.
    check_storage_ops(OP_SLOAD, storage, z8s, z8s, z8s, z8s, False, G_COLD_SLOAD, 0)
