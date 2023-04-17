from zkevm_specs.evm_circuit.util.call_gadget import CallGadget
from zkevm_specs.util.param import N_BYTES_GAS
from ...util import FQ, GAS_STIPEND_CALL_WITH_VALUE, Word, WordOrValue
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, AccountFieldTag
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
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    is_static = instruction.select(
        is_staticcall, FQ(1), instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    )
    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    parent_caller_address, parent_call_value = (
        (
            instruction.call_context_lookup(CallContextFieldTag.CallerAddress),
            instruction.call_context_lookup_word(CallContextFieldTag.Value),
        )
        if is_delegatecall == 1
        else (FQ(0), Word(0))
    )

    # Verify depth is less than 1024
    instruction.range_lookup(depth, 1024)

    call = CallGadget(instruction, FQ(1), is_call, is_callcode, is_delegatecall)
    # For opcode CALLCODE:
    # - callee_address = caller_address
    #
    # For opcode DELEGATECALL:
    # - callee_address = caller_address
    # - caller_address = parent_caller_address
    #
    callee_address = instruction.select(
        is_callcode + is_delegatecall, caller_address, call.callee_address
    )
    caller_address = instruction.select(is_delegatecall, parent_caller_address, caller_address)

    # Add `callee_address` to access list
    is_warm_access = instruction.add_account_to_access_list(
        tx_id, call.callee_address, reversion_info
    )

    # Check not is_static if call has value
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

    if is_call == 1:
        # For CALL opcode, verify transfer, and get caller balance before
        # transfer to constrain it should be greater than or equal to stack
        # `value`.
        (_, caller_balance), _ = instruction.transfer(
            caller_address, callee_address, call.value, callee_reversion_info
        )
    elif is_callcode == 1:
        # For CALLCODE opcode, get caller balance to constrain it should be
        # greater than or equal to stack `value`.
        caller_balance = instruction.account_read_word(caller_address, AccountFieldTag.Balance)

    # For both CALL and CALLCODE opcodes, verify caller balance is greater than
    # or equal to stack `value`.
    if is_call + is_callcode == 1:
        value_lt_caller_balance, value_eq_caller_balance = instruction.compare_word(
            call.value, caller_balance
        )
        instruction.constrain_zero(1 - value_lt_caller_balance - value_eq_caller_balance)

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
    is_precompile = instruction.precompile(callee_address)
    instruction.constrain_equal(
        is_precompile, FQ(instruction.next.execution_state in precompile_execution_states())
    )

    no_callee_code = call.is_empty_code_hash + call.callee_not_exists
    if no_callee_code == FQ(1) and is_precompile == FQ(0):
        # Make sure call is successful
        instruction.constrain_equal(call.is_success, FQ(1))

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

        # For CALL opcode, it has an extra stack pop `value` and two account write for `transfer` call (+3).
        # For CALLCODE opcode, it has an extra stack pop `value` and one account read for caller balance (+2).
        # For DELEGATECALL opcode, it has two extra call context lookups for current caller address and value (+2).
        # No extra lookups for STATICCALL opcode.
        rw_counter_delta = 20 + is_call * 3 + is_callcode * 2 + is_delegatecall * 2
        stack_pointer_delta = 5 + is_call + is_callcode

        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(rw_counter_delta),
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
    else:
        # Similar as above comment.
        rw_counter_delta = 40 + is_call * 3 + is_callcode * 2 + is_delegatecall * 2
        stack_pointer_delta = 5 + is_call + is_callcode

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
            (CallContextFieldTag.CallerAddress, caller_address.expr()),
            (CallContextFieldTag.CalleeAddress, callee_address.expr()),
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
            instruction.constrain_equal_word(
                instruction.call_context_lookup_word(field_tag, call_id=callee_call_id),
                WordOrValue(expected_word_or_value),
            )

        # Give gas stipend if value is not zero
        callee_gas_left += has_value * GAS_STIPEND_CALL_WITH_VALUE

        instruction.step_state_transition_to_new_context(
            rw_counter=Transition.delta(rw_counter_delta),
            call_id=Transition.to(callee_call_id),
            is_root=Transition.to(False),
            is_create=Transition.to(False),
            code_hash=Transition.to_word(call.callee_code_hash),
            gas_left=Transition.to(callee_gas_left),
            reversible_write_counter=Transition.to(2),
            log_id=Transition.same(),
        )
