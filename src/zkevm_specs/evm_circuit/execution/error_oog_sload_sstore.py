from zkevm_specs.util.param import GAS_COST_SSTORE_SENTRY_EIP2200, N_BYTES_GAS
from ...util import (
    FQ,
    COLD_SLOAD_COST,
    WARM_STORAGE_READ_COST,
    SLOAD_GAS,
    SSTORE_SET_GAS,
    SSTORE_RESET_GAS,
)
from ..instruction import Instruction
from ..opcode import Opcode
from ..table import CallContextFieldTag


def error_oog_sload_sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    (is_sstore, is_sload) = instruction.multiple_select(opcode, (Opcode.SSTORE, Opcode.SLOAD))
    instruction.constrain_equal(is_sstore + is_sload, FQ(1))

    storage_key = instruction.stack_pop()

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    callee_address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    callee_address = instruction.word_to_address(callee_address_word)
    is_warm = instruction.read_account_storage_to_access_list(tx_id, callee_address, storage_key)

    if is_sload == FQ(1):
        gas_cost = FQ(WARM_STORAGE_READ_COST) if is_warm == FQ(1) else FQ(COLD_SLOAD_COST)
    else:
        value = instruction.stack_pop()
        _, value_prev = instruction.account_storage_read(callee_address, storage_key, tx_id)
        original_value = instruction.curr.aux_data

        if value == value_prev:
            gas_cost = SLOAD_GAS  # 100
        elif value_prev == original_value:
            if original_value == 0:
                gas_cost = SSTORE_SET_GAS  # 20000
            else:
                gas_cost = SSTORE_RESET_GAS  # 2900
        else:
            gas_cost = SLOAD_GAS  # 100
        if is_warm == FQ(0):
            gas_cost += COLD_SLOAD_COST

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    if is_sload == FQ(1):
        instruction.constrain_equal(insufficient_gas, FQ(1))
    else:
        # For SSTORE, the OOG error occurs when the gas left is less than or equal to `SSTORE_SENTRY`
        lt_gas, eq_gas = instruction.compare(
            instruction.curr.gas_left, GAS_COST_SSTORE_SENTRY_EIP2200, N_BYTES_GAS
        )
        instruction.constrain_equal(lt_gas + eq_gas + insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter + 1
    )
