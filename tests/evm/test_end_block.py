import pytest

from zkevm_specs.evm_circuit import (
    AccountFieldTag,
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Target,
    RWTableRow,
    RW,
    CallContextFieldTag,
    TxReceiptFieldTag,
    Block,
    Transaction,
    Withdrawal,
)
from zkevm_specs.util import FQ, Word, WordOrValue


TESTING_DATA = (
    # (is_last_step, empty_block, max_txs, max_withdrawals, cumulative_gas, success)
    (False, False, 2, 5, 0, True),
    (True, False, 2, 5, 0, True),
    (True, False, 1, 2, 0, True),
    (True, True, 1, 5, 0, True),
    (True, False, 1, 5, int(15e6), True),
    (True, False, 1, 2, int(15e6) + 1, False),
)

MAX_CALLDATA_BYTES = 0
MAX_RWS = 32


@pytest.mark.parametrize(
    "is_last_step, empty_block, max_txs, max_withdrawals, cumulative_gas, success", TESTING_DATA
)
def test_end_block(
    is_last_step: bool,
    empty_block: bool,
    max_txs: int,
    max_withdrawals: int,
    cumulative_gas: int,
    success: bool,
):
    tx = Transaction()
    wd1 = Withdrawal(0, 99, 3, int(1e9))
    wd2 = Withdrawal(1, 999, 4, int(1.4e9))

    rw_rows = []
    rw_counter = 1
    if not empty_block:
        # dummy read/write for counting
        rw_rows += [RWTableRow(FQ(i + 1), *2 * [FQ(0)]) for i in range(21)]
        rw_counter += 21

        # insert 2 balance updates for withdrawals
        rw_rows.append(
            RWTableRow(
                FQ(22),
                FQ(RW.Write),
                key0=FQ(Target.Account),
                address=FQ(wd1.address),
                field_tag=FQ(AccountFieldTag.Balance),
                value=Word(int(5e18)),  # balance
                value_prev=Word(int(4e18)),  # balance_prev
            )
        )
        rw_rows.append(
            RWTableRow(
                FQ(23),
                FQ(RW.Write),
                key0=FQ(Target.Account),
                address=FQ(wd2.address),
                field_tag=FQ(AccountFieldTag.Balance),
                value=Word(int(5.5e18)),  # balance
                value_prev=Word(int(4.1e18)),  # balance_prev
            )
        )

        if is_last_step:
            rw_rows.append(
                RWTableRow(
                    FQ(24),
                    FQ(RW.Read),
                    key0=FQ(Target.CallContext),
                    id=FQ(1),
                    address=FQ(3),
                    field_tag=FQ(CallContextFieldTag.TxId),
                    value=WordOrValue(FQ(tx.id)),
                )
            )
            # append CumulativeGasUsed
            rw_rows.append(
                RWTableRow(
                    FQ(25),
                    FQ(RW.Read),
                    key0=FQ(Target.TxReceipt),
                    id=FQ(tx.id),
                    address=FQ(0),
                    field_tag=FQ(TxReceiptFieldTag.CumulativeGasUsed),
                    storage_key=Word(0),
                    value=WordOrValue(FQ(cumulative_gas)),
                )
            )

    rw_padding = [
        RWTableRow(FQ(i + 1), FQ(0), FQ(Target.Start)) for i in range(MAX_RWS - len(rw_rows))
    ]

    num_txs = 0 if empty_block else 1
    tx_padding = []
    for i in range(num_txs, max_txs):
        tx_padding += Transaction.padding(id=i + 1).table_fixed()

    tx_table = tx_padding
    if not empty_block:
        tx_table = list(tx.table_assignments())

    num_wds = 0 if empty_block else 2
    wd_padding = []
    for i in range(num_wds, max_withdrawals):
        wd_padding += Withdrawal.padding(id=i).table_assignments()

    wd_table = []
    if not empty_block:
        wd_table = list(wd1.table_assignments())
        wd_table += list(wd2.table_assignments())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx_table),
        withdrawal_table=set(wd_padding + wd_table),
        bytecode_table=set(),
        rw_table=set(rw_padding + rw_rows),
    )

    verify_steps(
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
