from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag
from .storage_gas import (
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
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RwCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()

    instruction.account_storage_read(callee_address, storage_key)

    new_is_warm, is_warm = instruction.add_account_storage_to_access_list_with_reversion(
        tx_id, callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )

    instruction.stack_push()

    # TODO: Use intrinsic gas (EIP 2028, 2930)
    dynamic_gas_cost = WARM_STORAGE_READ_COST if is_warm else COLD_SLOAD_COST

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
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RwCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()
    new_value = instruction.stack_pop()

    current_value, _, txid, original_value = instruction.account_storage_read(callee_address, storage_key)
    instruction.constrain_equal(tx_id, txid)

    instruction.account_storage_write_with_reversion(
        callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )

    new_is_warm, is_warm = instruction.add_account_storage_to_access_list_with_reversion(
        tx_id, callee_address, storage_key, is_persistent, rw_counter_end_of_reversion
    )

    gas_refund, gas_refund_prev = instruction.tx_refund_write_with_reversion(
        tx_id, is_persistent, rw_counter_end_of_reversion
    )
    new_gas_refund = gas_refund_prev
    if current_value != new_value:
        if original_value == current_value:
            if original_value != 0 and new_value == 0:
                new_gas_refund = new_gas_refund + SSTORE_CLEARS_SCHEDULE
        else:
            if original_value != 0:
                if current_value == 0:
                    new_gas_refund = new_gas_refund - SSTORE_CLEARS_SCHEDULE
                if new_value == 0:
                    new_gas_refund = new_gas_refund + SSTORE_CLEARS_SCHEDULE
            if original_value == new_value:
                if original_value == 0:
                    new_gas_refund = new_gas_refund + SSTORE_SET_GAS - SLOAD_GAS
                else:
                    new_gas_refund = new_gas_refund + SSTORE_RESET_GAS - SLOAD_GAS
    instruction.constrain_equal(gas_refund, new_gas_refund)

    # TODO: Use intrinsic gas (EIP 2028, 2930)
    if current_value == new_value:
        dynamic_gas_cost = SLOAD_GAS
    else:
        if original_value == current_value:
            if original_value == 0:
                dynamic_gas_cost = SSTORE_SET_GAS
            else:
                dynamic_gas_cost = SSTORE_RESET_GAS
        else:
            dynamic_gas_cost = SLOAD_GAS
    if not is_warm:
        dynamic_gas_cost = dynamic_gas_cost + COLD_SLOAD_COST

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(10),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
        state_write_counter=Transition.delta(3),
        dynamic_gas_cost=dynamic_gas_cost,
    )
