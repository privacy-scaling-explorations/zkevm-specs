from ..instruction import Instruction
from ..table import (
    CallContextFieldTag,
    FixedTableTag,
    RW,
    CopyDataTypeTag,
)
from ...util import FQ, IdentityPerWordGas


def dataCopy(instruction: Instruction):
    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        instruction.call_context_lookup(CallContextFieldTag.CalleeAddress, RW.Read),
    )
    call_data_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset, RW.Read)
    call_data_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength, RW.Read)
    return_data_offset = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataOffset, RW.Read
    )
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataLength, RW.Read
    )

    opcall_call_id = instruction.call_context_lookup(CallContextFieldTag.CallerId, RW.Read)
    precompile_call_id = instruction.curr.call_id

    rwc_delta = 5

    # Copy current call data to return data
    size = call_data_length.expr()
    copy_rwc_inc, _ = instruction.copy_lookup(
        opcall_call_id,
        CopyDataTypeTag.Memory,
        opcall_call_id,
        CopyDataTypeTag.Memory,
        call_data_offset,
        call_data_offset + size,
        return_data_offset,
        return_data_offset + return_data_length.expr(),
        instruction.curr.rw_counter + instruction.rw_counter_offset,
    )
    rwc_delta += int(copy_rwc_inc)

    # Copy current call data to next call context memory
    copy_rwc_inc, _ = instruction.copy_lookup(
        opcall_call_id,
        CopyDataTypeTag.Memory,
        precompile_call_id,
        CopyDataTypeTag.Memory,
        call_data_offset,
        call_data_offset + size,
        FQ(0),
        return_data_length,
        instruction.curr.rw_counter + instruction.rw_counter_offset + copy_rwc_inc,
    )
    rwc_delta += int(copy_rwc_inc)

    # Update last callee information
    for (field_tag, expected_value) in [
        (CallContextFieldTag.LastCalleeId, precompile_call_id),
        (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
        (CallContextFieldTag.LastCalleeReturnDataLength, size),
    ]:
        instruction.constrain_equal(
            instruction.call_context_lookup(field_tag, RW.Write, call_id=opcall_call_id),
            expected_value,
        )
    rwc_delta += 3

    gas_cost = instruction.memory_copier_gas_cost(call_data_length, FQ(0), IdentityPerWordGas)

    # Restore caller state to next StepState
    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=rwc_delta,
        return_data_offset=return_data_offset,
        return_data_length=return_data_length,
        gas_left=instruction.curr.gas_left - gas_cost,
    )
