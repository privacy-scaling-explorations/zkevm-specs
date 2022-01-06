from typing import Sequence, Tuple
from zkevm_specs.opcode.storage import Storage
from zkevm_specs.opcode.stack import Stack
from ..encoding import U8, U128, U256, is_circuit_code, u8s_to_u256

OP_SLOAD = 0x54
OP_SSTORE = 0x55

G_WARM_ACCESS = 100
G_COLD_SLOAD = 2100
G_S_SET = 20000
G_S_RESET = 2900

R_S_CLEAR = 15000

"""
The Yellow Paper defines:
We remind the reader that the checkpoint ("original") state sigma_0 is the
state if the current transaction were to revert.
Therefore to compute the required gas for an SSTORE we need both the current
storage and the original storage from the beginning of the transaction.
"""


@is_circuit_code
def check_storage_ops(
    opcode: U8,
    storage: Storage,
    key8s: Sequence[U8],
    new_value8s: Sequence[U8],
    original_value8s: Sequence[U8],
    current_value8s: Sequence[U8],
    is_touched: bool,
    expected_storage_cost: U128,
    expected_storage_refund: U128,
):
    assert len(key8s) == len(new_value8s) == 32

    # Check if this is an SLOAD or SSTORE
    is_sload = opcode == OP_SLOAD
    is_sstore = opcode == OP_SSTORE

    assert is_sload or is_sstore

    key = u8s_to_u256(key8s)
    new_value = u8s_to_u256(new_value8s)
    original_value = u8s_to_u256(original_value8s)
    current_value = u8s_to_u256(current_value8s)

    if is_sload:
        assert storage.read(key) == new_value
    else:
        assert storage.read(key) == current_value
        storage.write(key, new_value)

    gas_cost = 0
    gas_refund = 0

    if is_sload:
        if is_touched:  # warm access
            gas_cost = G_WARM_ACCESS
        else:  # cold access
            gas_cost = G_COLD_SLOAD
    else:
        # gas
        if not is_touched:  # cold access
            gas_cost = G_COLD_SLOAD

        if current_value == new_value or original_value != current_value:
            gas_cost += G_WARM_ACCESS
        elif current_value != new_value and original_value == current_value and original_value == 0:
            gas_cost += G_S_SET
        elif current_value != new_value and original_value == current_value and original_value != 0:
            gas_cost += G_S_RESET

        # refund
        if current_value != new_value and original_value == current_value and new_value == 0:
            gas_refund = R_S_CLEAR
        elif current_value != new_value and original_value != current_value:
            r_dirty_clear = 0
            if original_value != 0 and current_value == 0:
                r_dirty_clear = -R_S_CLEAR
            elif original_value != 0 and new_value == 0:
                r_dirty_clear = R_S_CLEAR

            r_dirty_reset = 0
            if original_value == new_value and original_value == 0:
                r_dirty_reset = G_S_SET - G_WARM_ACCESS
            elif original_value == new_value and original_value != 0:
                r_dirty_reset = G_S_RESET - G_WARM_ACCESS

            gas_refund = r_dirty_clear + r_dirty_reset
        else:
            gas_refund = 0

    assert expected_storage_cost == gas_cost
    assert expected_storage_refund == gas_refund
