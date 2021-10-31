from ...util import linear_combine, EMPTY_CODE_HASH
from ..step import Step
from ..table import TxTableTag, RWTableTag, CallContextTag
from .execution_result import ExecutionResult


def begin_tx(curr: Step, next: Step, r: int, is_first_step: bool):
    assert curr.core.call_id == curr.core.rw_counter

    tx_id = curr.call_context_lookup(CallContextTag.TxId)
    depth = curr.call_context_lookup(CallContextTag.Depth)

    if is_first_step:
        assert curr.core.rw_counter == 1
        assert tx_id == 1
        assert depth == 1

    tx_caller_address = curr.tx_lookup(tx_id, TxTableTag.CallerAddress)
    tx_callee_address = curr.tx_lookup(tx_id, TxTableTag.CalleeAddress)
    tx_value = curr.tx_lookup(tx_id, TxTableTag.Value)
    bytes_value = curr.decompress(tx_value, 32, r)
    tx_is_create = curr.tx_lookup(tx_id, TxTableTag.IsCreate)

    # Verify nonce
    tx_nonce = curr.tx_lookup(tx_id, TxTableTag.Nonce)
    nonce_prev = curr.w_lookup(RWTableTag.AccountNonce, [tx_caller_address])[1]
    assert tx_nonce == nonce_prev

    # TODO: Buy gas (EIP 1559)
    tx_gas = curr.tx_lookup(tx_id, TxTableTag.Gas)

    # TODO: Use intrinsic gas (EIP 2028, 2930)
    next_gas_left = tx_gas \
        - (53000 if tx_is_create else 21000)
    curr.bytes_range_lookup(next_gas_left, 8)

    # Prepare access list of caller
    curr.w_lookup(RWTableTag.TxAccessListAccount, [tx_id, tx_caller_address, 1])

    # Verify transfer
    rw_counter_end_of_reversion = curr.call_context_lookup(CallContextTag.RWCounterEndOfReversion)
    is_persistent = curr.call_context_lookup(CallContextTag.IsPersistent)

    curr.assert_transfer(tx_caller_address, tx_callee_address, bytes_value,
                         is_persistent, rw_counter_end_of_reversion, r)

    if tx_is_create:
        # TODO: Verify receiver address
        # TODO: Set next.call.opcode_source to tx_id
        raise NotImplementedError
    else:
        # Prepare access list of callee
        curr.w_lookup(RWTableTag.TxAccessListAccount, [tx_id, tx_callee_address, 1])

        code_hash = curr.r_lookup(RWTableTag.AccountCodeHash, [tx_callee_address])[0]
        is_empty_code_hash = curr.is_equal(code_hash, linear_combine(EMPTY_CODE_HASH, r))

        # TODO: Handle precompile
        if is_empty_code_hash:
            curr.assert_step_transition(
                next,
                rw_counter_diff=curr.rw_counter_diff,
                execution_result=ExecutionResult.BEGIN_TX,
                # We don't need to explicitly constrain next's call_id since we
                # know next step will be BEGIN_TX, which already constrains
                # call_id to be equal to rw_counter
            )
            assert next.peek_allocation(2) == tx_id + 1

            # TODO: Refund caller and tip coinbase
        else:
            # Setup next call's context
            tx_calldata_length = curr.tx_lookup(tx_id, TxTableTag.CalldataLength)

            # Note that:
            # - CallerCallId, ReturndataOffset, ReturndataLength, Result
            #   should never be used in root call, so unnecessary to check
            # - TxId, Depth are already checked above
            # - IsPersistent will only be used in the end of tx
            for (tag, value) in [
                (CallContextTag.CallerAddress, tx_caller_address),
                (CallContextTag.CalleeAddress, tx_callee_address),
                (CallContextTag.CalldataOffset, tx_value),
                (CallContextTag.CalldataLength, 0),
                (CallContextTag.Value, tx_calldata_length),
                (CallContextTag.IsStatic, False),
            ]:
                assert curr.call_context_lookup(tag) == value

            curr.assert_step_transition(
                next,
                rw_counter_diff=curr.rw_counter_diff,
                execution_result_not=ExecutionResult.BEGIN_TX,
                # Constrain next call_id to be equal to current one (asserted
                # implicitly in assert_step_transition)
                is_root=True,
                is_create=tx_is_create,
                opcode_source=code_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=next_gas_left,
                memory_size=0,
                state_write_counter=0,
                last_callee_id=0,
                last_callee_returndata_offset=0,
                last_callee_returndata_length=0,
            )
