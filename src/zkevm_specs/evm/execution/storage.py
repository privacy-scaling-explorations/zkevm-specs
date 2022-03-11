from ...util import (
    FQ,
    COLD_SLOAD_COST,
    WARM_STORAGE_READ_COST,
    SLOAD_GAS,
    SSTORE_SET_GAS,
    SSTORE_RESET_GAS,
    SSTORE_CLEARS_SCHEDULE,
)
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import CallContextFieldTag


def sload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SLOAD)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    reversion_info = instruction.reversion_info()
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()

    instruction.constrain_equal(
        instruction.account_storage_read(callee_address, storage_key, tx_id),
        instruction.stack_push(),
    )

    is_cold = instruction.add_account_storage_to_access_list(
        tx_id,
        callee_address,
        storage_key,
        reversion_info,
    )

    dynamic_gas_cost = instruction.select(is_cold, FQ(COLD_SLOAD_COST), FQ(WARM_STORAGE_READ_COST))

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
    reversion_info = instruction.reversion_info()
    callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)

    storage_key = instruction.stack_pop()
    storage_value = instruction.stack_pop()
    value, value_prev, original_value = instruction.account_storage_write(
        callee_address,
        storage_key,
        tx_id,
        reversion_info,
    )
    instruction.constrain_equal(storage_value, value)

    is_cold = instruction.add_account_storage_to_access_list(
        tx_id,
        callee_address,
        storage_key,
        reversion_info,
    )

    gas_refund, gas_refund_prev = instruction.tx_refund_write(tx_id, reversion_info)

    # original_value, value_prev, value all are different; original_value!=0
    nz_allne_case_refund = instruction.select(
        instruction.is_zero(value_prev),
        gas_refund_prev - SSTORE_CLEARS_SCHEDULE,
        instruction.select(
            instruction.is_zero(value),
            gas_refund_prev + SSTORE_CLEARS_SCHEDULE,
            gas_refund_prev,
        ),
    )
    # original_value!=value_prev, value_prev!=value, original_value!=0
    nz_ne_ne_case_refund = instruction.select(
        1 - instruction.is_equal(original_value, value),
        nz_allne_case_refund,
        nz_allne_case_refund + SSTORE_RESET_GAS - SLOAD_GAS,
    )
    # original_value!=value_prev, value_prev!=value
    ne_ne_case_refund = instruction.select(
        1 - instruction.is_zero(original_value),
        nz_ne_ne_case_refund,
        instruction.select(
            instruction.is_equal(original_value, value),
            gas_refund_prev + SSTORE_SET_GAS - SLOAD_GAS,
            gas_refund_prev,
        ),
    )
    gas_refund_new = instruction.select(
        instruction.is_equal(value_prev, value),
        gas_refund_prev,
        instruction.select(
            instruction.is_equal(original_value, value_prev),
            instruction.select(
                (1 - instruction.is_zero(original_value)) * instruction.is_zero(value),
                gas_refund_prev + SSTORE_CLEARS_SCHEDULE,
                gas_refund_prev,
            ),
            ne_ne_case_refund,
        ),
    )

    instruction.constrain_equal(gas_refund, gas_refund_new)

    eq_prev = instruction.is_equal(value_prev, value)
    prev_ne_original = 1 - instruction.is_equal(value_prev, original_value)
    warm_case_gas = instruction.select(
        eq_prev + prev_ne_original - eq_prev * prev_ne_original,
        FQ(SLOAD_GAS),
        instruction.select(
            instruction.is_zero(original_value),
            FQ(SSTORE_SET_GAS),
            FQ(SSTORE_RESET_GAS),
        ),
    )
    dynamic_gas_cost = instruction.select(is_cold, warm_case_gas + COLD_SLOAD_COST, warm_case_gas)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(9),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2),
        state_write_counter=Transition.delta(3),
        dynamic_gas_cost=dynamic_gas_cost,
    )
