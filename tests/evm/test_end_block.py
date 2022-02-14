import pytest
from itertools import chain

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    CallContextFieldTag,
    Block,
    Transaction,
)
from zkevm_specs.util import rand_fp

TESTING_DATA = (False, True)


@pytest.mark.parametrize("is_last_step", TESTING_DATA)
def test_end_block(is_last_step: bool):
    randomness = rand_fp()

    tx = Transaction()

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(),
        rw_table=set(
            chain(
                # dummy read/write for counting
                [(i, *7 * [0]) for i in range(22)],
                [
                    (
                        22,
                        RW.Read,
                        RWTableTag.CallContext,
                        1,
                        CallContextFieldTag.TxId,
                        0,
                        tx.id,
                        0,
                        0,
                        0,
                    )
                ]
                if is_last_step
                else [],
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
