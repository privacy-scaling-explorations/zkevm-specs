from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag
from ...util.param import (
    COLD_SLOAD_COST,
    WARM_STORAGE_READ_COST,
    SLOAD_GAS,
    SSTORE_SET_GAS,
    SSTORE_RESET_GAS,
    SSTORE_CLEARS_SCHEDULE,
)


def sload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SLOAD)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    rw_counter_end_of_reversion = instruction.call_context_lookup(
        CallContextFieldTag.RwCounterEndOfReversion
    )
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()

    instruction.constrain_equal(
        instruction.account_storage_read(callee_address, storage_key, tx_id),
        instruction.stack_push(),
    )

    is_warm_new, is_warm = instruction.add_account_storage_to_access_list_with_reversion(
        tx_id, callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )

    dynamic_gas_cost = WARM_STORAGE_READ_COST if is_warm == 1 else COLD_SLOAD_COST

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(8),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
        state_write_counter=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas_cost,
    )


def sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SSTORE)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    rw_counter_end_of_reversion = instruction.call_context_lookup(
        CallContextFieldTag.RwCounterEndOfReversion
    )
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()
    value_new = instruction.stack_pop()

    _, value_prev, txid, original_value = instruction.account_storage_write_with_reversion(
        callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )
    instruction.constrain_equal(tx_id, txid)

    is_warm_new, is_warm = instruction.add_account_storage_to_access_list_with_reversion(
        tx_id, callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )

    gas_refund, gas_refund_prev = instruction.tx_refund_write_with_reversion(
        tx_id, is_persistent, rw_counter_end_of_reversion
    )
    gas_refund_new = gas_refund_prev
    if value_prev != value_new:
        if original_value == value_prev:
            if original_value != 0 and value_new == 0:
                gas_refund_new = gas_refund_new + SSTORE_CLEARS_SCHEDULE
        else:
            if original_value != 0:
                if value_prev == 0:
                    gas_refund_new = gas_refund_new - SSTORE_CLEARS_SCHEDULE
                if value_new == 0:
                    gas_refund_new = gas_refund_new + SSTORE_CLEARS_SCHEDULE
            if original_value == value_new:
                if original_value == 0:
                    gas_refund_new = gas_refund_new + SSTORE_SET_GAS - SLOAD_GAS
                else:
                    gas_refund_new = gas_refund_new + SSTORE_RESET_GAS - SLOAD_GAS
    instruction.constrain_equal(gas_refund, gas_refund_new)

    if value_prev == value_new:
        dynamic_gas_cost = SLOAD_GAS
    else:
        if original_value == value_prev:
            if original_value == 0:
                dynamic_gas_cost = SSTORE_SET_GAS
            else:
                dynamic_gas_cost = SSTORE_RESET_GAS
        else:
            dynamic_gas_cost = SLOAD_GAS
    if is_warm == 0:
        dynamic_gas_cost = dynamic_gas_cost + COLD_SLOAD_COST

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(9),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
        state_write_counter=Transition.delta(3),
        dynamic_gas_cost=dynamic_gas_cost,
    )
