from ...util import linear_combine, le_to_int, EMPTY_CODE_HASH
from ..common_assert import assert_bool
from ..step import Step
from ..table import FixedTableTag, CallTableTag, RWTableTag, CallStateTag
from ..opcode import Opcode
from .execution_result import ExecutionResult


def call(curr: Step, next: Step, r: int, opcode: Opcode):
    # Verify opcode
    assert opcode == Opcode.CALL

    # Verify depth
    depth = curr.call_lookup(CallTableTag.Depth)
    curr.fixed_lookup(FixedTableTag.Range1024, [depth])

    # Gas needs full decompression due to EIP 150
    bytes_gas = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_callee_address = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_value = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_cd_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_cd_length = curr.decompress(curr.stack_pop_lookup(), 5, r)
    bytes_rd_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_rd_length = curr.decompress(curr.stack_pop_lookup(), 5, r)
    result = curr.stack_push_lookup()
    assert_bool(result)

    callee_address = le_to_int(bytes_callee_address[:20])
    gas = le_to_int(bytes_gas[:8])

    # Verify transfer
    rw_counter_end_of_revert = curr.call_lookup(CallTableTag.RWCounterEndOfRevert)
    caller_address = curr.call_lookup(CallTableTag.CalleeAddress)
    is_persistent = curr.call_lookup(CallTableTag.IsPersistent)
    is_static = curr.call_lookup(CallTableTag.IsStatic)

    has_value = not curr.is_zero(sum(bytes_value))
    if has_value:
        assert is_static == False
    curr.assert_transfer(caller_address, callee_address, bytes_value,
                         is_persistent, rw_counter_end_of_revert, r)

    # Verify memory expansion
    next_memory_size, memory_gas_cost = curr.assert_memory_expansion(
        bytes_cd_offset, bytes_cd_length, bytes_rd_offset, bytes_rd_length)

    # Verify gas cost
    tx_id = curr.call_lookup(CallTableTag.TxId)
    is_cold_access = 1 - curr.w_lookup(RWTableTag.TxAccessListAccount, [tx_id, callee_address, 1],
                                       is_persistent, rw_counter_end_of_revert)[0]
    code_hash = curr.r_lookup(RWTableTag.AccountCodeHash, [callee_address])[0]
    is_empty_code_hash = curr.is_equal(code_hash, linear_combine(EMPTY_CODE_HASH, r))
    callee_nonce = curr.r_lookup(RWTableTag.AccountNonce, [callee_address])[0]
    callee_balance = curr.r_lookup(RWTableTag.AccountBalance, [callee_address])[0]
    is_zero_nonce = curr.is_zero(callee_nonce)
    is_zero_balance = curr.is_zero(callee_balance)
    is_account_empty = is_zero_nonce and is_zero_balance and is_empty_code_hash
    base_gas_cost = 100 \
        + is_cold_access * 2500 \
        + is_account_empty * 25000 \
        + has_value * 9000 \
        + memory_gas_cost

    gas_available = curr.call.gas_left - base_gas_cost
    one_64th_available_gas = le_to_int(curr.allocate_byte(8))
    curr.fixed_lookup(FixedTableTag.Range64, [gas_available - 64 * one_64th_available_gas])

    is_capped = curr.allocate_bool(1)[0]
    is_uint64 = curr.is_zero(sum(bytes_gas[8:]))
    callee_gas_left = gas_available - one_64th_available_gas
    if is_uint64:
        if is_capped:
            curr.bytes_range_lookup(gas - callee_gas_left, 8)
        else:
            curr.bytes_range_lookup(callee_gas_left - gas, 8)
            callee_gas_left = gas
    else:
        assert is_capped

    next_gas_left = curr.call.gas_left - base_gas_cost - callee_gas_left

    # TODO: Handle precompile
    if is_empty_code_hash:
        assert result == 1

        curr.assert_step_transition(
            next,
            rw_counter_diff=curr.rw_counter_diff,
            execution_result_not=ExecutionResult.BEGIN_TX,
            state_write_counter_diff=curr.state_write_counter_diff,
            program_counter_diff=1,
            stack_pointer_diff=curr.stack_pointer_diff,
            gas_left=next_gas_left,
            memory_size=next_memory_size,
        )
    else:
        # Save caller's call state
        for (tag, value) in [
            (CallStateTag.IsRoot, curr.call.is_root),
            (CallStateTag.IsCreate, curr.call.is_create),
            (CallStateTag.OpcodeSource, curr.call.opcode_source),
            (CallStateTag.ProgramCounter, curr.call.program_counter + 1),
            (CallStateTag.StackPointer, curr.call.stack_pointer + curr.stack_pointer_diff),
            (CallStateTag.GasLeft, next_gas_left),
            (CallStateTag.MemorySize, next_memory_size),
            (CallStateTag.StateWriteCounter, curr.call.state_write_counter + curr.state_write_counter_diff),
        ]:
            curr.w_lookup(RWTableTag.CallState, [curr.core.call_id, tag, value])

        # Setup next call's context
        for (tag, value) in [
            (CallTableTag.CallerCallId, curr.core.call_id),
            (CallTableTag.TxId, tx_id),
            (CallTableTag.Depth, depth + 1),
            (CallTableTag.CallerAddress, caller_address),
            (CallTableTag.CalleeAddress, callee_address),
            (CallTableTag.CalldataOffset, le_to_int(bytes_cd_offset[:5])),
            (CallTableTag.CalldataLength, le_to_int(bytes_cd_length)),
            (CallTableTag.ReturndataOffset, le_to_int(bytes_rd_offset[:5])),
            (CallTableTag.ReturndataLength, le_to_int(bytes_rd_length)),
            (CallTableTag.Value, value),
            (CallTableTag.Result, result),
            (CallTableTag.IsPersistent, is_persistent * result),
            (CallTableTag.IsStatic, is_static),
        ]:
            assert curr.call_lookup(tag, next.core.call_id) == value

        callee_rw_counter_end_of_revert = curr.call_lookup(CallTableTag.RWCounterEndOfRevert, next.core.call_id)
        callee_state_write_counter = 0
        # Callee succeed but one of callers reverts at some point
        if result and not is_persistent:
            assert rw_counter_end_of_revert == callee_rw_counter_end_of_revert
            assert callee_state_write_counter == \
                curr.call.state_write_counter + curr.state_write_counter_diff

        curr.assert_step_transition(
            next,
            rw_counter_diff=curr.rw_counter_diff,
            execution_result_not=ExecutionResult.BEGIN_TX,
            call_id=curr.core.rw_counter,
            is_root=False,
            is_create=False,
            opcode_source=code_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=callee_gas_left + (2300 if has_value else 0),
            memory_size=0,
            state_write_counter=callee_state_write_counter,
            last_callee_id=0,
            last_callee_returndata_offset=0,
            last_callee_returndata_length=0,
        )
