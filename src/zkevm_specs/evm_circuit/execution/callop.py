from zkevm_specs.evm_circuit.util.call_gadget import CallGadget
from zkevm_specs.evm_circuit.util.precompile_gadget import PrecompileGadget
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import N_BYTES_GAS, N_BYTES_MEMORY_WORD_SIZE, N_BYTES_STACK
from ...util import FQ, GAS_STIPEND_CALL_WITH_VALUE, Word, WordOrValue
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, AccountFieldTag, CopyDataTypeTag
from ..execution_state import precompile_execution_states


def callop(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    is_call, is_callcode, is_delegatecall, is_staticcall = instruction.multiple_select(
        opcode, (Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL)
    )
    instruction.responsible_opcode_lookup(opcode)

    callee_call_id = instruction.curr.rw_counter

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    reversion_info = instruction.reversion_info()
    ctx_caller_address_word = instruction.call_context_lookup_word(
        CallContextFieldTag.CalleeAddress
    )
    ctx_caller_address = instruction.word_to_address(ctx_caller_address_word)
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    parent_caller_address_word, parent_call_value = (
        (
            instruction.call_context_lookup_word(CallContextFieldTag.CallerAddress),
            instruction.call_context_lookup_word(CallContextFieldTag.Value),
        )
        if is_delegatecall == 1
        else (Word(0), Word(0))
    )

    call = CallGadget(instruction, FQ(1), is_call, is_callcode, is_delegatecall, is_staticcall)

    # For opcode CALLCODE:
    # - callee_address = caller_address
    #
    # For opcode DELEGATECALL:
    # - callee_address = caller_address
    # - caller_address = parent_caller_address
    #
    callee_address = instruction.select(
        is_callcode + is_delegatecall, ctx_caller_address, call.callee_address
    )
    callee_address_word = instruction.address_to_word(callee_address)
    caller_address_word = instruction.select_word(
        is_delegatecall, parent_caller_address_word, ctx_caller_address_word
    )
    caller_address = instruction.word_to_address(caller_address_word)

    # Add `callee_address` to access list
    is_warm_access = instruction.add_account_to_access_list(
        tx_id, call.callee_address, reversion_info
    )

    # CALL with value must not be in static call stack
    has_value = call.has_value
    instruction.constrain_zero(has_value * is_static)

    # Propagate rw_counter_end_of_reversion and is_persistent
    callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)
    instruction.constrain_equal(
        callee_reversion_info.is_persistent,
        reversion_info.is_persistent * call.is_success,
    )
    is_reverted_by_caller = call.is_success == FQ(1) and reversion_info.is_persistent == FQ(0)
    if is_reverted_by_caller:
        # Propagate rw_counter_end_of_reversion when callee succeeds but one of callers revert at some point.
        # Note that we subtract it with current caller's reversible_write_counter as callee's endpoint, where caller's
        # reversible_write_counter here is added by 1 due to adding callee to access list
        instruction.constrain_equal(
            callee_reversion_info.rw_counter_end_of_reversion,
            reversion_info.rw_counter_of_reversion(),
        )

    ### Do stack depth and balance pre-check
    insufficient_balance = FQ(0)
    if is_call == FQ(1) or is_callcode == FQ(1):
        caller_balance = instruction.account_read_word(caller_address, AccountFieldTag.Balance)
        # ErrInsufficientBalance constraint
        insufficient_balance, _ = instruction.compare_word(caller_balance, call.value)
    is_depth_ok, _ = instruction.compare(depth, FQ(1025), N_BYTES_STACK)
    is_precheck_ok = is_depth_ok == FQ(1) and insufficient_balance == FQ(0)

    # If precheck is false, this call must be failed
    if not is_precheck_ok:
        instruction.constrain_zero(call.is_success)

    # For CALL opcode, transfer only when is_precheck_ok is true
    if is_call == FQ(1) and is_precheck_ok == FQ(1):
        instruction.transfer(caller_address, callee_address, call.value, callee_reversion_info)
    # For CALLCODE opcode, if is_success is true, then insufficient_balance must be zero
    if is_callcode == FQ(1) and call.is_success == FQ(1):
        instruction.constrain_zero(insufficient_balance)

    # Verify gas cost.
    gas_cost = call.gas_cost(
        instruction,
        is_warm_access,
        is_call,  # Only CALL opcode could invoke transfer to make empty account into non-empty.
    )
    # Apply EIP 150.
    # Note that sufficient gas_left is checked implicitly by constant_divmod.
    gas_available = instruction.curr.gas_left - gas_cost
    one_64th_gas, _ = instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
    all_but_one_64th_gas = gas_available - one_64th_gas
    callee_gas_left = instruction.select(
        call.is_u64_gas,
        instruction.min(all_but_one_64th_gas, call.gas, N_BYTES_GAS),
        all_but_one_64th_gas,
    )

    # Make sure the state transition to ExecutionState for precompile if and
    # only if the callee address is one of precompile
    is_precompile = instruction.precompile(call.callee_address)
    instruction.constrain_equal(
        is_precompile, FQ(instruction.next.execution_state in precompile_execution_states())
    )

    stack_pointer_delta = 5 + is_call + is_callcode
    no_callee_code = call.is_empty_code_hash + call.callee_not_exists
    # precheck fails or callee has no code
    if is_precheck_ok is False or (no_callee_code == FQ(1) and is_precompile == FQ(0)):
        # Empty return_data
        for field_tag, expected_value in [
            (CallContextFieldTag.LastCalleeId, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )

        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(instruction.rw_counter_offset),
            program_counter=Transition.delta(1),
            stack_pointer=Transition.delta(stack_pointer_delta),
            gas_left=Transition.delta(has_value * GAS_STIPEND_CALL_WITH_VALUE - gas_cost),
            memory_word_size=Transition.to(call.next_memory_size),
            reversible_write_counter=Transition.delta(3),
            # Always stay same
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_hash=Transition.same_word(),
        )
    # precompiles call
    elif is_precheck_ok and is_precompile == FQ.one():
        precompile_input_len: FQ = instruction.curr.aux_data[0]
        precompile_return_length: FQ = instruction.curr.aux_data[1]
        min_rd_copy_size = min(precompile_return_length, call.rd_length.n)

        # precompiles have no code
        instruction.constrain_equal(no_callee_code, FQ.one())
        # precompiles address must be warm
        instruction.constrain_equal(is_warm_access, FQ.one())

        # Setup next call's context.
        for field_tag, expected_value in [
            (CallContextFieldTag.IsSuccess, call.is_success),
            (CallContextFieldTag.CalleeAddress, callee_address_word),
            (CallContextFieldTag.CallerId, instruction.curr.call_id),
            (CallContextFieldTag.CallDataOffset, call.cd_offset),
            (CallContextFieldTag.CallDataLength, call.cd_length),
            (CallContextFieldTag.ReturnDataOffset, call.rd_offset),
            (CallContextFieldTag.ReturnDataLength, call.rd_length),
        ]:
            instruction.constrain_equal_word(
                instruction.call_context_lookup_word(field_tag, RW.Write, callee_call_id),
                WordOrValue(expected_value),
            )

        # Save caller's call state
        for field_tag, expected_value in [
            (CallContextFieldTag.ProgramCounter, instruction.curr.program_counter + 1),
            (
                CallContextFieldTag.StackPointer,
                instruction.curr.stack_pointer + stack_pointer_delta,
            ),
            (CallContextFieldTag.GasLeft, instruction.curr.gas_left - gas_cost - callee_gas_left),
            (CallContextFieldTag.MemorySize, call.next_memory_size),
            (
                CallContextFieldTag.ReversibleWriteCounter,
                instruction.curr.reversible_write_counter + 1,
            ),
            (CallContextFieldTag.LastCalleeId, callee_call_id),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ.zero()),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(precompile_return_length)),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )

        ### copy table lookup here
        ### is to rlc input and output to have an easy way to verify data

        # RLC precompile input from memory
        rw_counter_inc = instruction.rw_counter_offset
        input_copy_rwc_inc = FQ.zero()
        if precompile_input_len != FQ(0):
            input_copy_rwc_inc, _ = instruction.copy_lookup(
                instruction.curr.call_id,
                CopyDataTypeTag.Memory,
                callee_call_id,
                CopyDataTypeTag.RlcAcc,
                call.cd_offset,
                FQ(call.cd_offset + precompile_input_len),
                FQ.zero(),
                FQ(precompile_input_len),
                instruction.curr.rw_counter + rw_counter_inc,
            )
            rw_counter_inc += input_copy_rwc_inc

        # RLC precompile output from memory
        output_copy_rwc_inc = FQ.zero()
        if call.is_success == FQ.one() and precompile_return_length != FQ.zero():
            output_copy_rwc_inc, _ = instruction.copy_lookup(
                callee_call_id,
                CopyDataTypeTag.Memory,
                callee_call_id,
                CopyDataTypeTag.RlcAcc,
                FQ.zero(),
                FQ(precompile_return_length),
                FQ.zero(),
                FQ(precompile_return_length),
                instruction.curr.rw_counter + rw_counter_inc,
            )
            rw_counter_inc += output_copy_rwc_inc

        # Verify data copy from precompiles
        return_copy_rwc_inc = FQ.zero()
        if call.is_success == FQ.one() and precompile_return_length != FQ.zero():
            return_copy_rwc_inc, _ = instruction.copy_lookup(
                callee_call_id,
                CopyDataTypeTag.Memory,
                instruction.curr.call_id,
                CopyDataTypeTag.Memory,
                FQ.zero(),
                FQ(min_rd_copy_size),
                call.rd_offset,
                FQ(min_rd_copy_size),
                instruction.curr.rw_counter + rw_counter_inc,
            )
            rw_counter_inc += return_copy_rwc_inc

        precompile_memory_word_size, _ = instruction.constant_divmod(
            FQ(min_rd_copy_size + 31), FQ(32), N_BYTES_MEMORY_WORD_SIZE
        )

        # Give gas stipend if value is not zero
        callee_gas_left += has_value * GAS_STIPEND_CALL_WITH_VALUE

        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(rw_counter_inc),
            call_id=Transition.to(callee_call_id),
            is_root=Transition.to(False),
            is_create=Transition.to(False),
            code_hash=Transition.to_word(Word(EMPTY_CODE_HASH)),
            gas_left=Transition.to(callee_gas_left),
            reversible_write_counter=Transition.to(2),
            program_counter=Transition.delta(1),
            stack_pointer=Transition.same(),
            memory_word_size=Transition.to(precompile_memory_word_size),
        )

        PrecompileGadget(
            instruction, call.callee_address, FQ(precompile_return_length), call.cd_length
        )
    else:  # precheck is ok and callee has code
        # Save caller's call state
        for field_tag, expected_value in [
            (CallContextFieldTag.ProgramCounter, instruction.curr.program_counter + 1),
            (
                CallContextFieldTag.StackPointer,
                instruction.curr.stack_pointer + stack_pointer_delta,
            ),
            (CallContextFieldTag.GasLeft, instruction.curr.gas_left - gas_cost - callee_gas_left),
            (CallContextFieldTag.MemorySize, call.next_memory_size),
            (
                CallContextFieldTag.ReversibleWriteCounter,
                instruction.curr.reversible_write_counter + 1,
            ),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )

        # Setup next call's context. Note that RwCounterEndOfReversion, IsPersistent
        # have been checked above.
        for field_tag, expected_word_or_value in [
            (CallContextFieldTag.CallerId, instruction.curr.call_id),
            (CallContextFieldTag.TxId, tx_id.expr()),
            (CallContextFieldTag.Depth, depth.expr() + 1),
            (CallContextFieldTag.CallerAddress, caller_address_word),
            (CallContextFieldTag.CalleeAddress, callee_address_word),
            (CallContextFieldTag.CallDataOffset, call.cd_offset),
            (CallContextFieldTag.CallDataLength, call.cd_length),
            (CallContextFieldTag.ReturnDataOffset, call.rd_offset),
            (CallContextFieldTag.ReturnDataLength, call.rd_length),
            (
                CallContextFieldTag.Value,
                instruction.select_word(is_delegatecall, parent_call_value, call.value),
            ),
            (CallContextFieldTag.IsSuccess, call.is_success),
            (CallContextFieldTag.IsStatic, is_static.expr()),
            (CallContextFieldTag.LastCalleeId, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
            (CallContextFieldTag.IsRoot, FQ(False)),
            (CallContextFieldTag.IsCreate, FQ(False)),
            (CallContextFieldTag.CodeHash, call.callee_code_hash),
        ]:
            assert isinstance(expected_word_or_value, FQ) or isinstance(
                expected_word_or_value, Word
            )
            instruction.constrain_equal_word(
                instruction.call_context_lookup_word(field_tag, call_id=callee_call_id),
                WordOrValue(expected_word_or_value),
            )

        # Give gas stipend if value is not zero
        callee_gas_left += has_value * GAS_STIPEND_CALL_WITH_VALUE

        instruction.step_state_transition_to_new_context(
            rw_counter=Transition.delta(instruction.rw_counter_offset),
            call_id=Transition.to(callee_call_id),
            is_root=Transition.to(False),
            is_create=Transition.to(False),
            code_hash=Transition.to_word(call.callee_code_hash),
            gas_left=Transition.to(callee_gas_left),
            reversible_write_counter=Transition.to(2),
            log_id=Transition.same(),
        )
