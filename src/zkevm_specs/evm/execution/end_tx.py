from ...util import N_BYTES_GAS, MAX_REFUND_QUOTIENT_OF_GAS_USED, FQ, RLC, cast_expr
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..table import BlockContextFieldTag, CallContextFieldTag, TxContextFieldTag, TxReceiptFieldTag


def end_tx(instruction: Instruction):
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_tx_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)

    # Handle gas refund (refund is capped to gas_used // MAX_REFUND_QUOTIENT_OF_GAS_USED in EIP 3529)
    tx_gas = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Gas)
    gas_used = tx_gas - instruction.curr.gas_left
    max_refund, _ = instruction.constant_divmod(
        gas_used, FQ(MAX_REFUND_QUOTIENT_OF_GAS_USED), N_BYTES_GAS
    )
    refund = instruction.tx_refund_read(tx_id)
    effective_refund = instruction.min(max_refund, refund, 8)

    # Add effective_refund * gas_price back to caller's balance
    tx_gas_price = instruction.tx_gas_price(tx_id)
    value, carry = instruction.mul_word_by_u64(
        tx_gas_price, instruction.curr.gas_left + effective_refund
    )
    instruction.constrain_zero(carry)
    tx_caller_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallerAddress)
    instruction.add_balance(tx_caller_address, [value])

    # Add gas_used * effective_tip to coinbase's balance
    base_fee = cast_expr(instruction.block_context_lookup(BlockContextFieldTag.BaseFee), RLC)
    effective_tip, _ = instruction.sub_word(tx_gas_price, base_fee)
    reward, carry = instruction.mul_word_by_u64(effective_tip, gas_used)
    instruction.constrain_zero(carry)
    coinbase = instruction.block_context_lookup(BlockContextFieldTag.Coinbase)
    instruction.add_balance(coinbase, [reward])

    # constrain log id matches with `LogLength` of TxReceipt tag in RW
    log_id = instruction.tx_receipt_lookup(tx_id, TxReceiptFieldTag.LogLength)
    instruction.constrain_equal(log_id, instruction.curr.log_id)

    # constrain tx status matches with `PostStateOrStatus` of TxReceipt tag in RW
    instruction.constrain_equal(
        is_tx_persistent, instruction.tx_receipt_lookup(tx_id, TxReceiptFieldTag.PostStateOrStatus)
    )

    # constrain `CumulativeGasUsed` of TxReceipt tag in RW
    pre_tx_gas_cumulate = instruction.tx_receipt_lookup(
        tx_id - FQ(1), TxReceiptFieldTag.CumulativeGasUsed
    )
    instruction.constrain_equal(
        pre_tx_gas_cumulate + gas_used,
        instruction.tx_receipt_lookup(tx_id, TxReceiptFieldTag.CumulativeGasUsed),
    )

    # When to next transaction
    if instruction.next.execution_state == ExecutionState.BeginTx:
        # Check next tx_id is increased by 1
        instruction.constrain_equal(
            instruction.call_context_lookup(
                CallContextFieldTag.TxId, call_id=instruction.next.rw_counter
            ),
            tx_id.expr() + 1,
        )
        # Do step state transition for rw_counter
        instruction.constrain_step_state_transition(rw_counter=Transition.delta(5))

    # When to end of block
    if instruction.next.execution_state == ExecutionState.EndBlock:
        # Do step state transition for rw_counter and call_id
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(4), call_id=Transition.same()
        )
