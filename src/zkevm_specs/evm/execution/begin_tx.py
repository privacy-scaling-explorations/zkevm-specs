from ...util import GAS_COST_TX, GAS_COST_CREATION_TX, EMPTY_CODE_HASH, FQ, RLC, cast_expr
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..precompiled import PrecompiledAddress
from ..table import CallContextFieldTag, TxContextFieldTag, AccountFieldTag


def begin_tx(instruction: Instruction):
    call_id = instruction.curr.rw_counter

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId, call_id=call_id)
    reversion_info = instruction.reversion_info(call_id=call_id)
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.IsSuccess, call_id=call_id),
        reversion_info.is_persistent,
    )

    if instruction.is_first_step:
        instruction.constrain_equal(tx_id, FQ(1))

    tx_caller_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallerAddress)
    tx_callee_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CalleeAddress)
    tx_is_create = instruction.tx_context_lookup(tx_id, TxContextFieldTag.IsCreate)
    tx_value = cast_expr(instruction.tx_context_lookup(tx_id, TxContextFieldTag.Value), RLC)
    tx_call_data_length = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataLength)

    # CallerAddress != 0 (not a padding tx)
    instruction.constrain_not_zero(tx_caller_address)

    # Verify nonce
    is_tx_invalid = instruction.tx_context_lookup(tx_id, TxContextFieldTag.TxInvalid)
    tx_nonce = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Nonce)
    nonce, nonce_prev = instruction.account_write(tx_caller_address, AccountFieldTag.Nonce)
    is_nonce_valid = instruction.is_zero(tx_nonce.expr() - nonce_prev.expr())
    # bump the account nonce if the tx is valid
    instruction.constrain_equal(nonce, nonce_prev.expr() + 1 - is_tx_invalid.expr())

    # TODO: Implement EIP 1559 (currently it supports legacy transaction format)
    # Calculate gas fee
    tx_gas = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Gas)
    tx_gas_price = instruction.tx_gas_price(tx_id)
    gas_fee, carry = instruction.mul_word_by_u64(tx_gas_price, tx_gas)
    instruction.constrain_zero(carry)

    # intrinsic gas
    # G_0 = sum([G_txdatazero if CallData[i] == 0 else G_txdatanonzero for i in len(CallData)]) +
    #       (G_txcreate if tx_to == 0 or 0) +
    #       G_transaction +
    #       sum([G_accesslistaddress + G_accessliststorage * len(TA[j]) for j in len(TA)])
    tx_calldata_gas_cost = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallDataGasCost)
    tx_cost_gas = GAS_COST_CREATION_TX if tx_is_create == 1 else GAS_COST_TX
    # TODO: Handle gas cost of tx level access list (EIP 2930)
    tx_accesslist_gas = instruction.tx_context_lookup(tx_id, TxContextFieldTag.AccessListGasCost)
    tx_intrinsic_gas = tx_calldata_gas_cost.expr() + tx_cost_gas + tx_accesslist_gas.expr()

    # check instrinsic gas
    MAX_N_BYTES = 31 
    gas_not_enough, _ = instruction.compare(tx_gas, tx_intrinsic_gas, MAX_N_BYTES)
    gas_left = tx_gas.expr() if gas_not_enough else tx_gas.expr() - tx_intrinsic_gas

    # Prepare access list of caller and callee
    instruction.constrain_zero(instruction.add_account_to_access_list(tx_id, tx_caller_address))
    instruction.constrain_zero(instruction.add_account_to_access_list(tx_id, tx_callee_address))

    # Verify transfer
    sender_balance_pair, _ = instruction.transfer_with_gas_fee(
        tx_caller_address,
        tx_callee_address,
        (1 - is_tx_invalid) * tx_value,
        (1 - is_tx_invalid) * gas_fee,
        reversion_info,
    )
    sender_balance_prev = sender_balance_pair[1]
    balance_not_enough, _ = instruction.compare(
      instruction.rlc_to_fq(sender_balance_prev, MAX_N_BYTES),
      instruction.rlc_to_fq(tx_value, MAX_N_BYTES) + instruction.rlc_to_fq(gas_fee, MAX_N_BYTES),
      MAX_N_BYTES,
    )
    invalid_tx = 1 - (1 - balance_not_enough) * (1 - gas_not_enough) * (is_nonce_valid)
    # prover should not give incorrect is_tx_invalid flag.
    instruction.constrain_equal(is_tx_invalid, invalid_tx)

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

        if is_empty_code_hash == FQ(1) or is_tx_invalid == FQ(1):
            # Make sure tx is persistent
            instruction.constrain_equal(reversion_info.is_persistent, FQ(1))

            # Do step state transition
            instruction.constrain_equal(instruction.next.execution_state, ExecutionState.EndTx)
            instruction.constrain_step_state_transition(
                rw_counter=Transition.delta(10), call_id=Transition.to(call_id)
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
                rw_counter=Transition.delta(23),
                call_id=Transition.to(call_id),
                is_root=Transition.to(True),
                is_create=Transition.to(False),
                code_hash=Transition.to(code_hash),
                gas_left=Transition.to(gas_left),
                reversible_write_counter=Transition.to(2),
                log_id=Transition.to(0),
            )
