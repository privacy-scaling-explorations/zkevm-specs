import pytest
from itertools import chain

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RWTableRow,
    RW,
    CallContextFieldTag,
    TxContextFieldTag,
    TxTableRow,
    Block,
    Transaction,
)
from zkevm_specs.util import rand_fq, FQ

TESTING_DATA = (False, True)

MAX_TXS = 2
MAX_CALLDATA_BYTES = 0

MAX_RWS = 64


@pytest.mark.parametrize("is_last_step", TESTING_DATA)
def test_end_block(is_last_step: bool):
    randomness = rand_fq()

    tx = Transaction()

    # dummy read/write for counting
    rw_rows = [RWTableRow(FQ(i), *9 * [FQ(0)]) for i in range(22)]
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
    rw_padding = [
        RWTableRow(FQ(i + 1), FQ(0), FQ(RWTableTag.Start)) for i in range(MAX_RWS - len(rw_rows))
    ]

    num_txs = 1
    tx_padding = [
        TxTableRow(FQ(i + 1), FQ(TxContextFieldTag.Pad), FQ(0), FQ(0))
        for i in range((MAX_TXS - num_txs) * TxContextFieldTag.CallData)
    ]

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx_padding + list(tx.table_assignments(randomness))),
        bytecode_table=set(),
        rw_table=set(rw_padding + rw_rows),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EndBlock,
                rw_counter=22,
                call_id=1,
            ),
            StepState(
                execution_state=ExecutionState.EndBlock,
                rw_counter=22,
                call_id=1,
            ),
        ],
        end_with_last_step=is_last_step,
    )
