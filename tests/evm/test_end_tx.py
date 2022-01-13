import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    AccountFieldTag,
    CallContextFieldTag,
    Block,
    Transaction,
)
from zkevm_specs.util import rand_fp, RLC, EMPTY_CODE_HASH, MAX_REFUND_QUOTIENT_OF_GAS_USED

CALLEE_ADDRESS = 0xFF

TESTING_DATA = (
    # Tx with non-capped refund
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=27000, gas_price=int(2e9)),
        994,
        4800,
        False,
    ),
    # Tx with capped refund
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=65000, gas_price=int(2e9)),
        3952,
        38400,
        False,
    ),
    # Last tx
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, gas=21000, gas_price=int(2e9)),
        0,
        0,
        True,
    ),
)


@pytest.mark.parametrize("tx, gas_left, refund, is_last_tx", TESTING_DATA)
def test_end_tx(tx: Transaction, gas_left: int, refund: int, is_last_tx: bool):
    randomness = rand_fp()

    block = Block()
    effective_refund = min(refund, (tx.gas - gas_left) // MAX_REFUND_QUOTIENT_OF_GAS_USED)
    caller_balance_prev = int(1e18) - (tx.value + tx.gas * tx.gas_price)
    caller_balance = caller_balance_prev + (gas_left + effective_refund) * tx.gas_price
    coinbase_balance_prev = 0
    coinbase_balance = coinbase_balance_prev + (tx.gas - gas_left) * (tx.gas_price - block.base_fee)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(),
        rw_table=set(
            [
                (17, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, tx.id, 0, 0),
                (18, RW.Read, RWTableTag.TxRefund, tx.id, refund, refund, 0, 0),
                (
                    19,
                    RW.Write,
                    RWTableTag.Account,
                    tx.caller_address,
                    AccountFieldTag.Balance,
                    RLC(caller_balance, randomness),
                    RLC(caller_balance_prev, randomness),
                    0,
                ),
                (
                    20,
                    RW.Write,
                    RWTableTag.Account,
                    block.coinbase,
                    AccountFieldTag.Balance,
                    RLC(coinbase_balance, randomness),
                    RLC(coinbase_balance_prev, randomness),
                    0,
                ),
            ]
            + (
                []
                if is_last_tx
                else [(21, RW.Read, RWTableTag.CallContext, 22, CallContextFieldTag.TxId, tx.id + 1, 0, 0)]
            )
        ),
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
                code_source=RLC(EMPTY_CODE_HASH, randomness),
                program_counter=0,
                stack_pointer=1024,
                gas_left=gas_left,
                state_write_counter=2,
            ),
            StepState(
                execution_state=ExecutionState.EndBlock if is_last_tx else ExecutionState.BeginTx,
                rw_counter=22 - is_last_tx,
            ),
        ],
    )
