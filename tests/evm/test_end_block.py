import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RWTableRow,
    RW,
    CallContextFieldTag,
    TxReceiptFieldTag,
    Block,
    Transaction,
)
from zkevm_specs.util import rand_fq, FQ

TESTING_DATA = (
    # (is_last_step, empty_block, max_txs, cumulative_gas, success)
    (False, False, 2, 0, True),
    (True, False, 2, 0, True),
    (True, False, 1, 0, True),
    (True, True, 1, 0, True),
    (True, False, 1, int(15e6), True),
    (True, False, 1, int(15e6) + 1, False),
)

MAX_CALLDATA_BYTES = 0
MAX_RWS = 32


@pytest.mark.parametrize(
    "is_last_step, empty_block, max_txs, cumulative_gas, success", TESTING_DATA
)
def test_end_block(
    is_last_step: bool, empty_block: bool, max_txs: int, cumulative_gas: int, success: bool
):
    randomness = rand_fq()

    tx = Transaction()

    rw_rows = []
    rw_counter = 1
    if not empty_block:
        # dummy read/write for counting
        rw_rows += [RWTableRow(FQ(i + 1), *9 * [FQ(0)]) for i in range(21)]
        rw_counter += 21
        if is_last_step:
            rw_rows.append(
                RWTableRow(
                    FQ(22),
                    FQ(RW.Read),
                    FQ(RWTableTag.CallContext),
                    FQ(1),
                    FQ(CallContextFieldTag.TxId),
                    value=FQ(tx.id),
                )
            )
            # append CumlativeGasUsed
            rw_rows.append(
                RWTableRow(
                    FQ(23),
                    FQ(RW.Read),
                    key0=FQ(RWTableTag.TxReceipt),
                    key1=FQ(tx.id),
                    key2=FQ(0),
                    key3=FQ(TxReceiptFieldTag.CumulativeGasUsed),
                    key4=FQ(0),
                    value=FQ(cumulative_gas),
                )
            )

    rw_padding = [
        RWTableRow(FQ(i + 1), FQ(0), FQ(RWTableTag.Start)) for i in range(MAX_RWS - len(rw_rows))
    ]

    num_txs = 0 if empty_block else 1
    tx_padding = []
    for i in range(num_txs, max_txs):
        tx_padding += Transaction.padding(id=i + 1).table_fixed(randomness)

    tx_table = tx_padding
    if not empty_block:
        tx_table = list(tx.table_assignments(randomness))

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx_table),
        bytecode_table=set(),
        rw_table=set(rw_padding + rw_rows),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EndBlock,
                rw_counter=rw_counter,
                call_id=1,
            ),
            StepState(
                execution_state=ExecutionState.EndBlock,
                rw_counter=rw_counter,
                call_id=1,
            ),
        ],
        end_with_last_step=is_last_step,
        success=success,
    )
