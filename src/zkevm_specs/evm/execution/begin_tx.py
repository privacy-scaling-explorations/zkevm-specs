from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxContextFieldTag, RW, AccountFieldTag
from ..precompiled import PrecompiledAddress


def begin_tx(instruction: Instruction, is_first_step: bool = False):
    instruction.constrain_equal(instruction.curr.call_id, instruction.curr.rw_counter)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RWCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)

    if is_first_step:
        instruction.constrain_equal(instruction.curr.rw_counter, 1)
        instruction.constrain_equal(tx_id, 1)

    tx_caller_address = instruction.tx_lookup(tx_id, TxContextFieldTag.CallerAddress)
    tx_callee_address = instruction.tx_lookup(tx_id, TxContextFieldTag.CalleeAddress)
    tx_is_create = instruction.tx_lookup(tx_id, TxContextFieldTag.IsCreate)
    tx_value = instruction.tx_lookup(tx_id, TxContextFieldTag.Value)
    tx_calldata_length = instruction.tx_lookup(tx_id, TxContextFieldTag.CalldataLength)

    # Verify nonce
    tx_nonce = instruction.tx_lookup(tx_id, TxContextFieldTag.Nonce)
    nonce, nonce_prev = instruction.account_write(tx_caller_address, AccountFieldTag.Nonce)
    instruction.constrain_equal(tx_nonce, nonce_prev)
    instruction.constrain_equal(nonce, nonce_prev + 1)

    # TODO: Implement EIP 1559 (currently this assumes gas_fee_cap <= basefee + gas_tip_cap)
    # Calculate gas fee
    tx_gas = instruction.tx_lookup(tx_id, TxContextFieldTag.Gas)
    tx_gas_fee_cap = instruction.tx_lookup(tx_id, TxContextFieldTag.GasFeeCap)
    gas_fee, carry = instruction.mul_word_by_u64(tx_gas_fee_cap, tx_gas)
    instruction.constrain_zero(carry)

    # TODO: Use intrinsic gas (EIP 2028, 2930)
    gas_left = tx_gas - (53000 if tx_is_create else 21000)
    instruction.int_to_bytes(gas_left, 8)

    # Prepare access list of caller and callee
    instruction.constrain_equal(instruction.add_account_to_access_list(tx_id, tx_caller_address), 1)
    instruction.constrain_equal(instruction.add_account_to_access_list(tx_id, tx_callee_address), 1)

    # Verify transfer
    instruction.constrain_transfer(
        tx_caller_address,
        tx_callee_address,
        tx_value,
        gas_fee=gas_fee,
        is_persistent=is_persistent,
        rw_counter_end_of_reversion=rw_counter_end_of_reversion,
    )

    if tx_is_create:
        # TODO: Verify receiver address
        # TODO: Set opcode_source to tx_id
        raise NotImplementedError
    elif tx_callee_address in list(PrecompiledAddress):
        # TODO: Handle precompile
        raise NotImplementedError
    else:
        code_hash, _ = instruction.account_read(tx_callee_address, AccountFieldTag.CodeHash)

        # Setup next call's context
        # Note that:
        # - CallerCallId, ReturndataOffset, ReturndataLength, Result
        #   should never be used in root call, so unnecessary to check
        # - TxId is propagated from previous step or constraint to 1 if is_first_step
        # - IsPersistent will be verified in the end of tx
        for (tag, value) in [
            (CallContextFieldTag.Depth, 1),
            (CallContextFieldTag.CallerAddress, tx_caller_address),
            (CallContextFieldTag.CalleeAddress, tx_callee_address),
            (CallContextFieldTag.CalldataOffset, 0),
            (CallContextFieldTag.CalldataLength, tx_calldata_length),
            (CallContextFieldTag.Value, tx_value),
            (CallContextFieldTag.IsStatic, False),
        ]:
            instruction.constrain_equal(instruction.call_context_lookup(tag), value)

        instruction.constrain_new_context_state_transition(
            rw_counter=Transition.delta(16),
            call_id=Transition.persistent(),
            is_root=Transition.to(True),
            is_create=Transition.to(False),
            opcode_source=Transition.to(code_hash),
            gas_left=Transition.to(gas_left),
            state_write_counter=Transition.to(0),
        )
