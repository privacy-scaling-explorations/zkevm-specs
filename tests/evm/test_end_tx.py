import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    AccountFieldTag,
    CallContextFieldTag,
    TxReceiptFieldTag,
    Block,
    Transaction,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC, EMPTY_CODE_HASH, MAX_REFUND_QUOTIENT_OF_GAS_USED

CALLEE_ADDRESS = 0xFF

TESTING_DATA = (
    # Tx with non-capped refund
    (
        Transaction(
            id=1, caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=27000, gas_price=int(2e9)
        ),
        994,
        4800,
        False,
        0,
        True,
    ),
    # Tx with capped refund
    (
        Transaction(
            id=2, caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=65000, gas_price=int(2e9)
        ),
        3952,
        38400,
        False,
        100,
        True,
    ),
    # Last tx
    (
        Transaction(
            id=3, caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=21000, gas_price=int(2e9)
        ),
        0,  # gas_left
        0,  # refund
        True,  # is_last_tx
        20000,  # current_cumulative_gas_used
        True,  # success
    ),
    # Tx invalid
    (
        Transaction(
            id=1,
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=60000,
            gas_price=int(2e9),
            invalid_tx=1,
        ),
        60000,
        0,
        False,
        0,
        True,  # success
    ),
    # Last Tx invalid
    (
        Transaction(
            id=2,
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=65000,
            gas_price=int(2e9),
            invalid_tx=1,
        ),
        65000,
        0,
        True,
        21000,
        True,  # success
    ),
)


@pytest.mark.parametrize(
    "tx, gas_left, refund, is_last_tx, current_cumulative_gas_used, success", TESTING_DATA
)
def test_end_tx(
    tx: Transaction,
    gas_left: int,
    refund: int,
    is_last_tx: bool,
    current_cumulative_gas_used: int,
    success: bool,
):
    randomness = rand_fq()

    block = Block()
    effective_refund = min(refund, (tx.gas - gas_left) // MAX_REFUND_QUOTIENT_OF_GAS_USED)
    caller_balance_prev = int(1e18) - (tx.value + tx.gas * tx.gas_price)
    caller_balance = caller_balance_prev + (gas_left + effective_refund) * tx.gas_price
    coinbase_balance_prev = 0
    coinbase_balance = coinbase_balance_prev + (tx.gas - gas_left) * (tx.gas_price - block.base_fee)

    rw_dictionary = (
        # fmt: off
        RWDictionary(17)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .call_context_read(1, CallContextFieldTag.IsPersistent, 1)
            .tx_refund_read(tx.id, refund)
            .account_write(tx.caller_address, AccountFieldTag.Balance, RLC(caller_balance, randomness), RLC(caller_balance_prev, randomness))
            .account_write(block.coinbase, AccountFieldTag.Balance, RLC(coinbase_balance, randomness), RLC(coinbase_balance_prev, randomness))
            .tx_receipt_write(tx.id, TxReceiptFieldTag.PostStateOrStatus, 1 - tx.invalid_tx)
            .tx_receipt_write(tx.id, TxReceiptFieldTag.LogLength, 0)
        # fmt: on
    )

    # check it is first tx
    is_first_tx = tx.id == 1
    if is_first_tx:
        assert current_cumulative_gas_used == 0
        rw_dictionary.tx_receipt_write(
            tx.id, TxReceiptFieldTag.CumulativeGasUsed, tx.gas - gas_left
        )
    else:
        rw_dictionary.tx_receipt_read(
            tx.id - 1, TxReceiptFieldTag.CumulativeGasUsed, current_cumulative_gas_used
        )
        rw_dictionary.tx_receipt_write(
            tx.id,
            TxReceiptFieldTag.CumulativeGasUsed,
            tx.gas - gas_left + current_cumulative_gas_used,
        )

    if not is_last_tx:
        rw_dictionary.call_context_read(27 - is_first_tx, CallContextFieldTag.TxId, tx.id + 1)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=17,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=RLC(EMPTY_CODE_HASH, randomness),
                program_counter=0,
                stack_pointer=1024,
                gas_left=gas_left,
                reversible_write_counter=2,
            ),
            StepState(
                execution_state=ExecutionState.EndBlock if is_last_tx else ExecutionState.BeginTx,
                rw_counter=27 - is_first_tx - is_last_tx,
                call_id=1 if is_last_tx else 0,
            ),
        ],
        success=success,
    )
