from ...util import (
    EMPTY_CODE_HASH,
    FQ,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    RLC,
)
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, AccountFieldTag
from ..precompiled import PrecompiledAddress


def call_staticcall(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    is_call, _ = instruction.pair_select(opcode, Opcode.CALL, Opcode.STATICCALL)
    instruction.responsible_opcode_lookup(opcode)

    callee_call_id = instruction.curr.rw_counter

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    reversion_info = instruction.reversion_info()
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)

    # Verify is_static == 0 for opcode CALL, and is_static == 1 for opcode STATICCALL.
    instruction.constrain_equal(is_call + is_static, FQ(1))

    # Verify depth is less than 1024
    instruction.range_lookup(depth, 1024)

    # Lookup values from stack
    gas_rlc = instruction.stack_pop()
    callee_address_rlc = instruction.stack_pop()
    # The third argument `value` of opcode CALL is not present for opcode STATICCALL.
    value = instruction.stack_pop() if is_call == 1 else RLC(0)
    cd_offset_rlc = instruction.stack_pop()
    cd_length_rlc = instruction.stack_pop()
    rd_offset_rlc = instruction.stack_pop()
    rd_length_rlc = instruction.stack_pop()
    is_success = instruction.stack_push()

    # Verify is_success is a bool
    instruction.constrain_bool(is_success)

    # Recomposition of random linear combination to integer
    callee_address = instruction.rlc_to_fq(callee_address_rlc, N_BYTES_ACCOUNT_ADDRESS)
    gas = instruction.rlc_to_fq(gas_rlc, N_BYTES_GAS)
    gas_is_u64 = instruction.is_zero(instruction.sum(gas_rlc.le_bytes[N_BYTES_GAS:]))
    cd_offset, cd_length = instruction.memory_offset_and_length(cd_offset_rlc, cd_length_rlc)
    rd_offset, rd_length = instruction.memory_offset_and_length(rd_offset_rlc, rd_length_rlc)

    # Verify memory expansion
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        cd_offset,
        cd_length,
        rd_offset,
        rd_length,
    )

    # Add callee to access list
    is_warm_access = instruction.add_account_to_access_list(tx_id, callee_address, reversion_info)

    # Propagate rw_counter_end_of_reversion and is_persistent
    callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)
    instruction.constrain_equal(
        callee_reversion_info.is_persistent, reversion_info.is_persistent * is_success.expr()
    )
    is_reverted_by_caller = is_success.expr() == FQ(1) and reversion_info.is_persistent == FQ(0)
    if is_reverted_by_caller:
        # Propagate rw_counter_end_of_reversion when callee succeeds but one of callers revert at some point.
        # Note that we subtract it with current caller's reversible_write_counter as callee's endpoint, where caller's
        # reversible_write_counter here is added by 1 due to adding callee to access list
        instruction.constrain_equal(
            callee_reversion_info.rw_counter_end_of_reversion,
            reversion_info.rw_counter_of_reversion(),
        )

    # Check not is_static if call has value
    has_value = 1 - instruction.is_zero(value)
    instruction.constrain_zero(has_value * is_static)

    # Constrain value == 0 for opcode STATICCALL.
    instruction.constrain_zero(has_value * (1 - is_call))

    # Verify transfer
    _, (_, callee_balance_prev) = instruction.transfer(
        caller_address, callee_address, value, callee_reversion_info
    )

    # Verify gas cost
    callee_nonce = instruction.account_read(callee_address, AccountFieldTag.Nonce)
    callee_code_hash = instruction.account_read(callee_address, AccountFieldTag.CodeHash)
    is_empty_code_hash = instruction.is_equal(
        callee_code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32)
    )
    is_account_empty = (
        instruction.is_zero(callee_nonce)
        * instruction.is_zero(callee_balance_prev)
        * is_empty_code_hash
    )
    gas_cost = (
        instruction.select(
            is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
        )
        + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_NEW_ACCOUNT)
        + memory_expansion_gas_cost
    )

    # Apply EIP 150.
    # Note that sufficient gas_left is checked implicitly by constant_divmod.
    gas_available = instruction.curr.gas_left - gas_cost
    one_64th_gas, _ = instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
    all_but_one_64th_gas = gas_available - one_64th_gas
    callee_gas_left = instruction.select(
        gas_is_u64,
        instruction.min(all_but_one_64th_gas, gas, N_BYTES_GAS),
        all_but_one_64th_gas,
    )

    if callee_address in list(PrecompiledAddress):
        # TODO: Handle precompile
        raise NotImplementedError
    elif is_empty_code_hash == FQ(1):
        # Make sure call is successful
        instruction.constrain_equal(is_success, FQ(1))

        # Empty return_data
        for (field_tag, expected_value) in [
            (CallContextFieldTag.LastCalleeId, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
        ]:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, RW.Write),
                expected_value,
            )

        if is_call == 1:
            rw_counter_delta, stack_pointer_delta = 24, 6
        else:
            rw_counter_delta, stack_pointer_delta = 23, 5

        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(rw_counter_delta),
            program_counter=Transition.delta(1),
            stack_pointer=Transition.delta(stack_pointer_delta),
            gas_left=Transition.delta(has_value * GAS_STIPEND_CALL_WITH_VALUE - gas_cost),
            memory_size=Transition.to(next_memory_size),
            reversible_write_counter=Transition.delta(3),
            # Always stay same
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_hash=Transition.same(),
        )
    else:
        if is_call == 1:
            rw_counter_delta, stack_pointer_delta = 44, 6
        else:
            rw_counter_delta, stack_pointer_delta = 42, 5

        # Save caller's call state
        for (field_tag, expected_value) in [
            (CallContextFieldTag.ProgramCounter, instruction.curr.program_counter + 1),
            (
                CallContextFieldTag.StackPointer,
                instruction.curr.stack_pointer + stack_pointer_delta,
            ),
            (CallContextFieldTag.GasLeft, instruction.curr.gas_left - gas_cost - callee_gas_left),
            (CallContextFieldTag.MemorySize, next_memory_size),
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
        call_context_lookups = [
            (CallContextFieldTag.CallerId, instruction.curr.call_id),
            (CallContextFieldTag.TxId, tx_id.expr()),
            (CallContextFieldTag.Depth, depth.expr() + 1),
            (CallContextFieldTag.CallerAddress, caller_address.expr()),
            (CallContextFieldTag.CalleeAddress, callee_address),
            (CallContextFieldTag.CallDataOffset, cd_offset),
            (CallContextFieldTag.CallDataLength, cd_length),
            (CallContextFieldTag.ReturnDataOffset, rd_offset),
            (CallContextFieldTag.ReturnDataLength, rd_length),
        ]
        # Value is not used for opcode STATICCALL.
        if is_call == 1:
            call_context_lookups.append((CallContextFieldTag.Value, value.expr()))
        call_context_lookups += [
            (CallContextFieldTag.IsSuccess, is_success.expr()),
            (CallContextFieldTag.IsStatic, is_static.expr()),
            (CallContextFieldTag.LastCalleeId, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
            (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
            (CallContextFieldTag.IsRoot, FQ(False)),
            (CallContextFieldTag.IsCreate, FQ(False)),
            (CallContextFieldTag.CodeHash, callee_code_hash.expr()),
        ]
        for (field_tag, expected_value) in call_context_lookups:
            instruction.constrain_equal(
                instruction.call_context_lookup(field_tag, call_id=callee_call_id),
                expected_value,
            )

        # Give gas stipend if value is not zero
        callee_gas_left += has_value * GAS_STIPEND_CALL_WITH_VALUE

        instruction.step_state_transition_to_new_context(
            rw_counter=Transition.delta(rw_counter_delta),
            call_id=Transition.to(callee_call_id),
            is_root=Transition.to(False),
            is_create=Transition.to(False),
            code_hash=Transition.to(callee_code_hash),
            gas_left=Transition.to(callee_gas_left),
            reversible_write_counter=Transition.to(2),
            log_id=Transition.same(),
        )
