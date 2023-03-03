from zkevm_specs.util.param import GAS_COST_CODE_DEPOSIT, MAX_CODE_SIZE
from ...util import EMPTY_HASH, FQ, N_BYTES_MEMORY_ADDRESS, RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, CopyDataTypeTag, AccountFieldTag
from ..execution_state import ExecutionState


def return_revert(instruction: Instruction):
    # We do this check explicitly because we're not using same_context transition.
    opcode = instruction.opcode_lookup(True)
    is_return, _ = instruction.pair_select(opcode, Opcode.RETURN, Opcode.REVERT)

    # When a call ends with RETURN this call must be successful, but it's not
    # necessary persistent depends on if it's a sub-call of a failed call or not.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)  # rwc += 1
    instruction.constrain_equal(is_success, is_return)

    return_offset_rlc = instruction.stack_pop()  # rwc += 1
    return_length_rlc = instruction.stack_pop()  # rwc += 1

    return_offset = instruction.rlc_to_fq(return_offset_rlc, N_BYTES_MEMORY_ADDRESS)
    return_length = instruction.rlc_to_fq(return_length_rlc, N_BYTES_MEMORY_ADDRESS)
    return_end = return_offset + return_length

    rwc_delta = 3

    callee_gas_left = instruction.curr.gas_left
    if instruction.curr.is_create and is_success:
        # A. Returns the specified memory chunk as deployment code.

        # TODO: Untested case.  Test it once create Tx is implemented, and once
        # CREATE/CREATE2 are implemented.
        callee_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
        reversion_info = instruction.reversion_info()
        code_hash, code_hash_prev = instruction.account_write(
            callee_address, AccountFieldTag.CodeHash
        )
        instruction.constrain_equal(code_hash_prev, RLC(EMPTY_HASH))
        instruction.constrain_equal(code_hash, instruction.curr.aux_data)

        # verify bytecode size less than 24,576 bytes
        instruction.range_lookup(return_length, MAX_CODE_SIZE)

        # gas cost of CREATE = GAS_COST_CREATE + memory expansion + GAS_COST_CODE_DEPOSIT * len(byte_code)
        # first two part were handled in create.py
        callee_gas_left = callee_gas_left - return_length * GAS_COST_CODE_DEPOSIT
        instruction.constrain_equal(
            instruction.call_context_lookup(CallContextFieldTag.GasLeft, RW.Write), callee_gas_left
        )

        # Return a memory chunk as deployment code by copying each byte from
        # callee's memory to bytecode, using the copy circuit.
        copy_length = return_length
        if return_length > 0:
            copy_rwc_inc, _ = instruction.copy_lookup(
                instruction.curr.call_id,  # src_id
                CopyDataTypeTag.Memory,  # src_type
                code_hash,  # dst_id
                CopyDataTypeTag.Bytecode,  # dst_type
                return_offset,  # src_addr
                return_end,  # src_addr_boundary
                FQ(0),  # dst_addr
                copy_length,  # length
                instruction.curr.rw_counter + instruction.rw_counter_offset,
            )
            instruction.constrain_equal(copy_rwc_inc, copy_length)  # rwc += copy_length
            instruction.rw_counter_offset += int(copy_rwc_inc)
            rwc_delta += int(copy_length)

    if not instruction.curr.is_root and not instruction.curr.is_create:
        # D. Returns the specified memory chunk to the caller.

        # Return a memory chunk as return data by copying each byte from
        # callee's memory to caller's memory, using the copy circuit.
        caller_return_offset = instruction.call_context_lookup(
            CallContextFieldTag.ReturnDataOffset
        )  # rwc += 1
        caller_return_length = instruction.call_context_lookup(
            CallContextFieldTag.ReturnDataLength
        )  # rwc += 1
        copy_length = instruction.min(return_length, caller_return_length, N_BYTES_MEMORY_ADDRESS)
        copy_rwc_inc, _ = instruction.copy_lookup(
            instruction.curr.call_id,  # src_id
            CopyDataTypeTag.Memory,  # src_type
            instruction.next.call_id,  # dst_id
            CopyDataTypeTag.Memory,  # dst_type
            return_offset,  # src_addr
            return_end,  # src_addr_boundary
            caller_return_offset,  # dst_addr
            copy_length,  # length
            instruction.curr.rw_counter + instruction.rw_counter_offset,
        )
        instruction.constrain_equal(copy_rwc_inc, 2 * copy_length)  # rwc += 2 * copy_length
        instruction.rw_counter_offset += int(copy_rwc_inc)
        rwc_delta += 2 + 2 * int(copy_length)

    # B1. End the execution
    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    _next_memory_size, memory_expansion_gas = instruction.memory_expansion_dynamic_length(
        return_offset, return_length
    )

    # E. Revert state changes
    if not is_return:
        rwc_delta += int(instruction.curr.reversible_write_counter)

    if instruction.curr.is_root:
        # B2. End the execution

        # When a transaction ends with RETURN, this call must be persistent
        is_persistent = instruction.call_context_lookup(
            CallContextFieldTag.IsPersistent
        )  # rwc += 1
        instruction.constrain_equal(is_persistent, FQ(is_return))

        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(rwc_delta + 1),
            gas_left=Transition.to(callee_gas_left),
            call_id=Transition.same(),
        )
    else:
        # C. Restores caller's context and switch to it.

        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=rwc_delta,
            return_data_offset=return_offset,
            return_data_length=return_length,
            gas_left=instruction.curr.gas_left - memory_expansion_gas,
        )  # rwc += 12
