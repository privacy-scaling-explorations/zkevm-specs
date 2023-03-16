from typing import Sequence

from .util import FQ, Expression, ConstraintSystem, cast_expr, MAX_N_BYTES, N_BYTES_MEMORY_ADDRESS
from .evm_circuit import (
    Tables,
    CopyDataTypeTag,
    CopyCircuitRow,
    RW,
    RWTableTag,
    CopyCircuit,
    TxContextFieldTag,
    BytecodeFieldTag,
)


def lt(lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
    assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
    assert lhs.expr().n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
    assert rhs.expr().n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"
    return FQ(lhs.expr().n < rhs.expr().n)


def verify_row(cs: ConstraintSystem, rows: Sequence[CopyCircuitRow]):
    cs.constrain_bool(rows[0].is_first)
    cs.constrain_bool(rows[0].is_last)
    # is_first == 0 when q_step == 0
    cs.constrain_zero((1 - rows[0].q_step) * rows[0].is_first)
    # is_last == 0 when q_step == 1
    cs.constrain_zero(rows[0].q_step * rows[0].is_last)
    cs.constrain_equal(rows[0].is_memory, cs.is_zero(rows[0].tag - CopyDataTypeTag.Memory))
    cs.constrain_equal(rows[0].is_bytecode, cs.is_zero(rows[0].tag - CopyDataTypeTag.Bytecode))
    cs.constrain_equal(rows[0].is_tx_calldata, cs.is_zero(rows[0].tag - CopyDataTypeTag.TxCalldata))
    cs.constrain_equal(rows[0].is_tx_log, cs.is_zero(rows[0].tag - CopyDataTypeTag.TxLog))
    cs.constrain_equal(rows[0].is_rlc_acc, cs.is_zero(rows[0].tag - CopyDataTypeTag.RlcAcc))

    # constrain the transition between two copy steps
    is_last_two_rows = rows[0].is_last + rows[1].is_last
    with cs.condition(1 - is_last_two_rows) as cs:
        # not last two rows
        cs.constrain_equal(rows[0].id, rows[2].id)
        cs.constrain_equal(rows[0].tag, rows[2].tag)
        cs.constrain_equal(rows[0].addr + 1, rows[2].addr)
        cs.constrain_equal(rows[0].src_addr_end, rows[2].src_addr_end)

    # contrain the transition for `rw_counter` and `rwc_inc_left`
    rw_diff = (1 - rows[0].is_pad) * (rows[0].is_memory + rows[0].is_tx_log)
    with cs.condition(1 - rows[0].is_last) as cs:
        # not last row
        cs.constrain_equal(rows[0].rw_counter + rw_diff, rows[1].rw_counter)
        cs.constrain_equal(rows[0].rwc_inc_left - rw_diff, rows[1].rwc_inc_left)
        # rlc_acc is the same over all rows
        cs.constrain_equal(rows[0].rlc_acc, rows[1].rlc_acc)
    # rwc_inc_left == rw_diff for last row in the copy slot
    with cs.condition(rows[0].is_last) as cs:
        cs.constrain_equal(rows[0].rwc_inc_left, rw_diff)

    # for RlcAcc type, value == rlc_acc at the last row
    with cs.condition(rows[0].is_last * rows[0].is_rlc_acc) as cs:
        cs.constrain_equal(rows[0].rlc_acc, rows[0].value)


def verify_step(cs: ConstraintSystem, rows: Sequence[CopyCircuitRow], r: FQ):
    with cs.condition(rows[0].q_step):
        # bytes_left == 1 for last step
        cs.constrain_zero(rows[1].is_last * (1 - rows[0].bytes_left))
        # bytes_left == bytes_left_next + 1 for non-last step
        cs.constrain_zero((1 - rows[1].is_last) * (rows[0].bytes_left - rows[2].bytes_left - 1))
        # value == 0 when is_pad == 1 for read
        cs.constrain_zero(rows[0].is_pad * rows[0].value)
        # is_pad == 1 - (src_addr < src_addr_end) for read row
        # We skip tx_log because:
        # 1. It can only ever be a write row, so q_step == 0 and the constraint will be satisfied.
        # 2. Since `lt(..)` will still be computed, it's excepted to throw an exception since
        #    dst addr is a very large number: addr += (int(TxLogFieldTag.Data) << 32) + (log_id << 48)
        if rows[0].is_tx_log == FQ.zero():
            cs.constrain_equal(
                1 - lt(rows[0].addr, rows[0].src_addr_end, N_BYTES_MEMORY_ADDRESS), rows[0].is_pad
            )
        # is_pad == 0 for write row
        cs.constrain_zero(rows[1].is_pad)
    # write value == read value if not rlc accumulator
    with cs.condition(rows[0].q_step * (1 - rows[1].is_rlc_acc)):
        cs.constrain_equal(rows[0].value, rows[1].value)
    # read value == write value for the first step (always)
    with cs.condition(rows[0].q_step * rows[0].is_first):
        cs.constrain_equal(rows[0].value, rows[1].value)
    # next_write_value == (write_value * r) + next_read_value if rlc accumulator
    with cs.condition((1 - rows[0].q_step) * (1 - rows[0].is_last) * rows[0].is_rlc_acc):
        cs.constrain_equal(rows[2].value, rows[0].value * r + rows[1].value)


def verify_copy_table(copy_circuit: CopyCircuit, tables: Tables, r: FQ):
    cs = ConstraintSystem()
    copy_table = copy_circuit.table()
    n = len(copy_table)
    for i, row in enumerate(copy_table):
        rows = [
            row,
            copy_table[(i + 1) % n],
            copy_table[(i + 2) % n],
        ]
        # constrain on each row and step
        verify_row(cs, rows)
        verify_step(cs, rows, r)

        # lookup into tables
        if row.is_memory == 1 and row.is_pad == 0:
            val = tables.rw_lookup(
                row.rw_counter, 1 - row.q_step, FQ(RWTableTag.Memory), row.id, row.addr
            ).value
            cs.constrain_equal(cast_expr(val, FQ), row.value)
        if row.is_bytecode == 1 and row.is_pad == 0:
            val = tables.bytecode_lookup(
                row.id, FQ(BytecodeFieldTag.Byte), row.addr, row.is_code
            ).value
            cs.constrain_equal(cast_expr(val, FQ), row.value)
        if row.is_tx_calldata == 1 and row.is_pad == 0:
            val = tables.tx_lookup(row.id, FQ(TxContextFieldTag.CallData), row.addr).value
            cs.constrain_equal(val, row.value)
        if row.is_tx_log == 1:
            val = tables.rw_lookup(
                row.rw_counter,
                FQ(RW.Write),
                FQ(RWTableTag.TxLog),
                row.id,  # tx_id
                row.addr,
            ).value
            cs.constrain_equal(cast_expr(val, FQ), row.value)
