from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag, TxContextFieldTag
from .params import (
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
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RWCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.tx_lookup(tx_id, TxContextFieldTag.CalleeAddress)

    storage_slot = instruction.stack_pop()
    warm = instruction.access_list_storage_slot_read(tx_id, callee_address, storage_slot)

    # TODO: Use intrinsic gas (EIP 2028, 2930)
    dynamic_gas_cost = WARM_STORAGE_READ_COST if warm else COLD_SLOAD_COST

    instruction.storage_slot_read(callee_address, storage_slot)
    instruction.add_storage_slot_to_access_list_with_reversion(
        tx_id, callee_address, storage_slot, is_persistent, rw_counter_end_of_reversion
    )
    instruction.stack_push()

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(5),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
        state_write_counter=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas_cost,
    )


def sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SSTORE)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RWCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    callee_address = instruction.tx_lookup(tx_id, TxContextFieldTag.CalleeAddress)

    storage_slot = instruction.stack_pop()
    new_value = instruction.stack_pop()
    warm = instruction.access_list_storage_slot_read(tx_id, callee_address, storage_slot)
    original_value = instruction.storage_slot_original_value_read(tx_id, callee_address, storage_slot)
    current_value, _ = instruction.storage_slot_read(callee_address, storage_slot)

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
    if not warm:
        dynamic_gas_cost = dynamic_gas_cost + COLD_SLOAD_COST

    instruction.storage_slot_write_with_reversion(
        callee_address, storage_slot, is_persistent, rw_counter_end_of_reversion
    )
    instruction.add_storage_slot_to_access_list_with_reversion(
        tx_id, callee_address, storage_slot, is_persistent, rw_counter_end_of_reversion
    )
    if is_persistent:
        gas_refund = instruction.gas_refund_read(tx_id)
        if current_value != new_value:
            if original_value == current_value:
                if original_value != 0 and new_value == 0:
                    gas_refund = gas_refund + SSTORE_CLEARS_SCHEDULE
            else:
                if original_value != 0:
                    if current_value == 0:
                        gas_refund = gas_refund - SSTORE_CLEARS_SCHEDULE
                    if new_value == 0:
                        gas_refund = gas_refund + SSTORE_CLEARS_SCHEDULE
                if original_value == new_value:
                    if original_value == 0:
                        gas_refund = gas_refund + SSTORE_SET_GAS - SLOAD_GAS
                    else:
                        gas_refund = gas_refund + SSTORE_RESET_GAS - SLOAD_GAS
        instruction.gas_refund_write(tx_id)

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(9) if is_persistent else Transition.delta(7),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
        state_write_counter=Transition.delta(2),
        dynamic_gas_cost=dynamic_gas_cost,
    )
