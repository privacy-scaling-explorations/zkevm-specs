from ...util import GAS_COST_TX, GAS_COST_CREATION_TX, EMPTY_CODE_HASH, FQ, RLC, cast_expr
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..precompiled import PrecompiledAddress
from ..table import CallContextFieldTag, TxContextFieldTag, AccountFieldTag


def begin_tx(instruction: Instruction):
    call_id = instruction.curr.rw_counter

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, call_id=call_id)
    reversion_info = instruction.reversion_info(call_id=call_id)

    if instruction.is_first_step:
        instruction.constrain_equal(instruction.curr.rw_counter, FQ(1))
        instruction.constrain_equal(tx_id, FQ(1))

    tx_caller_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallerAddress)
    tx_callee_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CalleeAddress)
    tx_is_create = instruction.tx_context_lookup(tx_id, TxContextFieldTag.IsCreate)
    tx_value = cast_expr(instruction.tx_context_lookup(tx_id, TxContextFieldTag.Value), RLC)
    tx_call_data_length = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)

    # Verify nonce
    tx_nonce = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Nonce)
    nonce, nonce_prev = instruction.account_write(tx_caller_address, AccountFieldTag.Nonce)
    instruction.constrain_equal(tx_nonce, nonce_prev)
    instruction.constrain_equal(nonce, nonce_prev.expr() + 1)

    # TODO: Implement EIP 1559 (currently it supports legacy transaction format)
    # Calculate gas fee
    tx_gas = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Gas)
    tx_gas_price = instruction.tx_gas_price(tx_id)
    gas_fee, carry = instruction.mul_word_by_u64(tx_gas_price, tx_gas)
    instruction.constrain_zero(carry)

    # TODO: Handle gas cost of tx level access list (EIP 2930)
    tx_call_data_gas_cost = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataGasCost)
    gas_left = (
        tx_gas.expr()
        - (GAS_COST_CREATION_TX if tx_is_create == 1 else GAS_COST_TX)
        - tx_call_data_gas_cost.expr()
    )
    instruction.constrain_gas_left_not_underflow(gas_left)

    # Prepare access list of caller and callee
    instruction.constrain_zero(instruction.add_account_to_access_list(tx_id, tx_caller_address))
    instruction.constrain_zero(instruction.add_account_to_access_list(tx_id, tx_callee_address))

    # Verify transfer
    instruction.transfer_with_gas_fee(
        tx_caller_address,
        tx_callee_address,
        tx_value,
        gas_fee,
        reversion_info,
    )

    if tx_is_create == 1:
        # TODO: Verify created address
        # code_hash represents the contract creation code
        # 1. In the case of root call, code_hash is the hash of the tx calldata.
        # 2. In the case of internal call, code_hash is the hash of the chunk of
        #    caller memory corresponding to the contract init code.
        raise NotImplementedError
    elif tx_callee_address in list(PrecompiledAddress):
        # TODO: Handle precompile
        raise NotImplementedError
    else:
        code_hash = instruction.account_read(tx_callee_address, AccountFieldTag.CodeHash)
        is_empty_code_hash = instruction.is_equal(
            code_hash, RLC(EMPTY_CODE_HASH, instruction.randomness)
        )

        if is_empty_code_hash == FQ(1):
            # Make sure tx is persistent
            instruction.constrain_equal(reversion_info.is_persistent, FQ(1))

            # Do step state transition
            instruction.constrain_equal(instruction.next.execution_state, ExecutionState.EndTx)
            instruction.constrain_step_state_transition(
                rw_counter=Transition.delta(9), call_id=Transition.to(call_id)
            )
        else:

            # Setup next call's context
            # Note that:
            # - CallerId, ReturnDataOffset, ReturnDataLength
            #   should never be used in root call, so unnecessary to be checked
            # - TxId is checked from previous step or constraint to 1 if is_first_step
            # - IsSuccess, IsPersistent will be verified in the end of tx
            for (tag, value) in [
                (CallContextFieldTag.Depth, FQ(1)),
                (CallContextFieldTag.CallerAddress, tx_caller_address),
                (CallContextFieldTag.CalleeAddress, tx_callee_address),
                (CallContextFieldTag.CallDataOffset, FQ(0)),
                (CallContextFieldTag.CallDataLength, tx_call_data_length),
                (CallContextFieldTag.Value, tx_value),
                (CallContextFieldTag.IsStatic, FQ(False)),
                (CallContextFieldTag.LastCalleeId, FQ(0)),
                (CallContextFieldTag.LastCalleeReturnDataOffset, FQ(0)),
                (CallContextFieldTag.LastCalleeReturnDataLength, FQ(0)),
                (CallContextFieldTag.IsRoot, FQ(True)),
                (CallContextFieldTag.IsCreate, FQ(False)),
                (CallContextFieldTag.CodeHash, code_hash),
            ]:
                instruction.constrain_equal(
                    instruction.call_context_lookup(tag, call_id=call_id), value
                )

            instruction.step_state_transition_to_new_context(
                rw_counter=Transition.delta(22),
                call_id=Transition.to(call_id),
                is_root=Transition.to(True),
                is_create=Transition.to(False),
                code_hash=Transition.to(code_hash),
                gas_left=Transition.to(gas_left),
                reversible_write_counter=Transition.to(2),
                log_id=Transition.to(0),
            )
