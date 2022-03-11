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
    Block,
    Transaction,
)
from zkevm_specs.util import rand_fq, FQ

TESTING_DATA = (False, True)


@pytest.mark.parametrize("is_last_step", TESTING_DATA)
def test_end_block(is_last_step: bool):
    randomness = rand_fq()

    tx = Transaction()

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(),
        rw_table=set(
            chain(
                # dummy read/write for counting
                [RWTableRow(FQ(i), *9 * [FQ(0)]) for i in range(22)],
                [RWTableRow(FQ(22), FQ(RW.Read), FQ(RWTableTag.CallContext), FQ(1), FQ(CallContextFieldTag.TxId), value=FQ(tx.id))]  # fmt: skip
                if is_last_step else [],
            )
        ),
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
