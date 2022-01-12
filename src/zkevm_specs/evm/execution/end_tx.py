from ...util import N_BYTES_GAS
from ..execution_state import ExecutionState
from ..instruction import Instruction
from ..table import BlockContextFieldTag, CallContextFieldTag, TxContextFieldTag


def end_tx(instruction: Instruction):
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    # Handle gas refund (refund is capped to gas_used // 2 in EIP 3529)
    tx_gas = instruction.tx_context_lookup(tx_id, TxContextFieldTag.Gas)
    gas_used = tx_gas - instruction.curr.gas_left
    capped_refund, _ = instruction.constant_divmod(gas_used, 2, N_BYTES_GAS)
    accumulated_refund = instruction.tx_refund_read(tx_id)
    refund = instruction.min(capped_refund, accumulated_refund, 8)

    # Add refund * gas_price back to caller's balance
    tx_gas_price = instruction.tx_gas_price(tx_id)
    value, carry = instruction.mul_word_by_u64(tx_gas_price, refund)
    instruction.constrain_zero(carry)
    tx_caller_address = instruction.tx_context_lookup(tx_id, TxContextFieldTag.CallerAddress)
    instruction.add_balance(tx_caller_address, [value])

    # Add gas_used * effective_tip to coinbase's balance
    base_fee = instruction.block_context_lookup(BlockContextFieldTag.BaseFee)
    effective_tip, _ = instruction.sub_word(tx_gas_price, base_fee)
    reward, carry = instruction.mul_word_by_u64(effective_tip, gas_used)
    instruction.constrain_zero(carry)
    coinbase = instruction.block_context_lookup(BlockContextFieldTag.Coinbase)
    instruction.add_balance(coinbase, [reward])

    # Do step state transition for rw_counter
    instruction.constrain_equal(instruction.next.rw_counter, instruction.curr.rw_counter + 7)

    # Go to next transaction
    if instruction.next.execution_state == ExecutionState.BeginTx:
        # Check next tx_id is increased by 1
        instruction.constrain_equal(
            instruction.call_context_lookup(CallContextFieldTag.TxId, call_id=instruction.next.rw_counter),
            tx_id + 1,
        )

    # Or to ExecutionState.EndBlock
