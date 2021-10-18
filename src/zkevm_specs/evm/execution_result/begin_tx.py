from ...util import linear_combine, EMPTY_CODE_HASH
from ..step import Step
from ..table import TxTableTag, CallTableTag, RWTableTag
from .execution_result import ExecutionResult


def begin_tx(curr: Step, next: Step, r: int, is_first_step: bool):
    tx_id = curr.call_lookup(CallTableTag.TxId)
    depth = curr.call_lookup(CallTableTag.Depth)

    if is_first_step:
        assert curr.rw_counter == 1
        assert curr.call_state.call_id == 1
        assert tx_id == 1
        assert depth == 1

    tx_caller_address = curr.tx_lookup(TxTableTag.CallerAddress, tx_id)
    tx_callee_address = curr.tx_lookup(TxTableTag.CalleeAddress, tx_id)
    tx_value = curr.tx_lookup(TxTableTag.Value, tx_id)
    bytes_value = curr.bytes_range_lookup(tx_value, 32)
    tx_is_create = curr.tx_lookup(TxTableTag.IsCreate, tx_id)

    # Verify nonce
    tx_nonce = curr.tx_lookup(TxTableTag.Nonce, tx_id)
    assert curr.w_lookup(RWTableTag.AccountNonce, [tx_caller_address, tx_nonce])

    # TODO: Buy intrinsic gas (EIP 2930)
    tx_gas = curr.tx_lookup(TxTableTag.Gas, tx_id)
    curr.bytes_range_lookup(tx_gas, 8)

    # Verify transfer
    rw_counter_end_of_revert = curr.call_lookup(CallTableTag.RWCounterEndOfRevert)
    is_persistent = curr.call_lookup(CallTableTag.IsPersistent)

    curr.assert_transfer(tx_caller_address, tx_callee_address, bytes_value, r,
                         None if is_persistent else rw_counter_end_of_revert)

    if tx_is_create:
        # TODO: Verify receiver address
        # TODO: Set next.call_state.opcode_source to tx_id
        raise NotImplementedError
    else:
        code_hash = curr.r_lookup(RWTableTag.AccountCodeHash, [tx_callee_address])
        is_empty_code_hash = curr.is_equal(code_hash, linear_combine(EMPTY_CODE_HASH, r))

        # TODO: Handle precompile
        if is_empty_code_hash:
            curr.assert_step_transition(
                next,
                rw_counter_diff=curr.rw_counter_diff,
                execution_result=ExecutionResult.BEGIN_TX,
                call_id=next.rw_counter,
            )
            assert next.peek_allocation(2) == tx_id + 1

            # TODO: Refund caller and tip coinbase
        else:
            # Setup next call's context
            tx_calldata_length = curr.tx_lookup(TxTableTag.CalldataLength, tx_id)

            [
                caller_address,
                callee_address,
                calldata_offset,
                calldata_length,
                value,
                is_static,
            ] = [
                curr.call_lookup(tag, next.call_state.call_id) for tag in [
                    CallTableTag.CallerAddress,
                    CallTableTag.CalleeAddress,
                    CallTableTag.CalldataOffset,
                    CallTableTag.CalldataLength,
                    CallTableTag.Value,
                    CallTableTag.IsStatic,
                ]
            ]

            assert caller_address == tx_caller_address
            assert callee_address == tx_callee_address
            assert value == tx_value
            assert calldata_offset == 0
            assert calldata_length == tx_calldata_length
            assert is_static == False

            curr.assert_step_transition(
                next,
                rw_counter_diff=curr.rw_counter_diff,
                execution_result_not=ExecutionResult.BEGIN_TX,
                is_root=True,
                is_create=tx_is_create,
                opcode_source=code_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=tx_gas,
                memory_size=0,
                state_write_counter=0,
                last_callee_id=0,
                last_callee_returndata_offset=0,
                last_callee_returndata_length=0,
            )
