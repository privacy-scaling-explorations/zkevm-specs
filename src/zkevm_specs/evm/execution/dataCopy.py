from ..instruction import Instruction
from ..table import (
    CallContextFieldTag,
    FixedTableTag,
    RW,
    CopyDataTypeTag,
)
from ...util import FQ, IdentityBaseGas, IdentityPerWordGas


def dataCopy(instruction: Instruction):
    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        instruction.call_context_lookup(CallContextFieldTag.CalleeAddress, RW.Read).value(),
        FQ(IdentityBaseGas),
    )

    caller_id = instruction.call_context_lookup(CallContextFieldTag.CallerId, RW.Read).value()
    call_data_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset, RW.Read).value()
    call_data_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength, RW.Read).value()
    return_data_offset = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataOffset, RW.Read
    ).value()
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataLength, RW.Read
    ).value()

    # Copy current call data to return data
    size = call_data_length

    gas_cost = FQ(IdentityBaseGas) + instruction.memory_copier_gas_cost(
        call_data_length, FQ(0), IdentityPerWordGas
    )

    copy_rwc_inc, _ = instruction.copy_lookup(
        caller_id,
        CopyDataTypeTag.Memory,
        caller_id,
        CopyDataTypeTag.Memory,
        call_data_offset,
        call_data_offset + size,
        return_data_offset,
        return_data_offset + return_data_length,
        instruction.curr.rw_counter + instruction.rw_counter_offset,
    )

    # Copy current call data to next call context memory
    copy_rwc_inc, _ = instruction.copy_lookup(
        caller_id,
        CopyDataTypeTag.Memory,
        instruction.curr.call_id,
        CopyDataTypeTag.Memory,
        call_data_offset,
        call_data_offset + size,
        FQ(0),
        return_data_length,
        instruction.curr.rw_counter + instruction.rw_counter_offset + copy_rwc_inc,
    )
    instruction.rw_counter_offset += 4 * int(size)

    # Restore caller state to next StepState
    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=instruction.rw_counter_offset,
        return_data_offset=FQ(0),
        return_data_length=size,
        gas_left=instruction.curr.gas_left - gas_cost,
        caller_id=caller_id,
    )
