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


# TODO: replace this costly comparator with a simple comparator that detects when the address equals the max address, and stays 1 from that point on. Or by a counter provided by the caller.
def lt(lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
    assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
    assert lhs.expr().n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
    assert rhs.expr().n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"
    return FQ(lhs.expr().n < rhs.expr().n)


def select(condition: Expression, when_true: Expression, when_false: Expression) -> Expression:
    return condition.expr() * when_true.expr() + (1 - condition.expr()) * when_false.expr()


# The WordIterator gadget guarantees that a word is processed in full. If the iterator is seen enabled at *any* step within a word,
# then it must be enabled for a full block of 32 steps. There are markers for the start and the end of a word.
class WordIterator:
    LENGTH = 32

    is_enabled: Expression
    position_in_word: FQ
    is_word_start: FQ
    is_word_end: FQ

    def __init__(self, row: CopyCircuitRow):
        self.is_enabled = row.is_memory + row.is_tx_log
        self.position_in_word = row.position_in_word
        self.is_word_start = row.is_word_start
        self.is_word_end = row.is_word_end


# Verify the transition between two steps within a word.
# Return an expression of whether the transition happen (i.e. `curr` and `next` are both inside of the same word).
def verify_step_word_iterator(cs: ConstraintSystem, curr: WordIterator, next: WordIterator) -> Expression:

    # The gadget is enabled when the position_in_word is not zero.
    cs.constrain_equal(curr.is_enabled.expr(), 1 - cs.is_zero(curr.position_in_word))

    # Detect the first and last byte of the word.
    cs.constrain_equal(curr.is_word_start, cs.is_equal(curr.position_in_word, FQ(1)))
    cs.constrain_equal(curr.is_word_end, cs.is_equal(curr.position_in_word, FQ(WordIterator.LENGTH)))
    # TODO: is_word_start and is_word_end can be the same column with a rotation of 31.
    # TODO: maybe not necessary to be a witnessed boolean.

    # The state machine goes forward and backward. The transition between this row and the next
    # is enforced if:
    # - this row is enabled but it is not the last row (forwards),
    # - or the next row is enabled but it is not the first row (backwards).
    word_continue = curr.is_enabled.expr() * (1 - curr.is_word_end) + next.is_enabled.expr() * (1 - next.is_word_start)

    # Enforce the transition.
    with cs.condition(word_continue):
        cs.constrain_equal(next.position_in_word, curr.position_in_word + 1)

    return word_continue


class WordRlcGadget:
    word_iter: WordIterator
    rlc_acc: FQ

    def __init__(self, word_iter: WordIterator, rlc_acc: FQ):
        self.word_iter = word_iter
        self.rlc_acc = rlc_acc
    
    # Return the final RLC value for the word. Only valid when is_word_start=1.
    def get_final_rlc(self, rand: FQ) -> FQ:
        # Shift the result of the reversed Horner’s rule, which has computed negative powers of rand (from -31 to 0), into the final result with normal powers (from 0 to 31).
        # At the final step (i=31), having processed all 32 bytes, `final_rlc = rand**31 * final_acc`.
        return rand**(WordIterator.LENGTH - 1) * self.rlc_acc


# Verify that the accumulator `curr` includes the current input byte.
# `curr` is either the start of a word, or a continuation after `prev`.
def verify_step_word_rlc(cs: ConstraintSystem, rand: FQ, prev: WordRlcGadget, curr: WordRlcGadget, curr_byte: Expression):
    # The accumulator starts at 0 at the start of a word, or is copied from the previous row.
    prev_acc = select(curr.word_iter.is_word_start, FQ(0), prev.rlc_acc).expr()
    
    # This is Horner’s rule, but in reverse. This accumulates the values in order of increasing powers of rand, from negative power -31 to power 0.
    #
    # We want to compute, for i in [0, 32):
    #   final_rlc = ∑ byte[i] * rand**i
    #
    # Rewrite it in terms of the accumulator that we actually compute:
    #   final_rlc = rand**31 * final_acc
    #   final_acc = ∑ byte[i] * rand**(i - 31)
    #
    # Reverse the processing order, that is rewrite with `X = rand**-1` and `j = 31 - i`:
    #   final_acc = ∑ byte[i] * X**j
    #
    # Then apply Horner’s rule, going from the highest power (j=31, i=0) to the lowest power (j=0, i=31):
    #   acc[-1] = 0
    #   acc[i] = acc[i-1] * X + byte[i]
    #   (acc[i] - byte[i]) * rand = acc[i-1]
    cs.constrain_equal((curr.rlc_acc - curr_byte.expr()) * rand, prev_acc)


# The CopyRangeGadget tracks whether the current row is within the copy range.
# By contrast, outside of the copy range, no copy happens, but memory words may still be processed up to their boundaries.
class CopyRangeGadget:
    # Whether this row is within the copy range.
    is_copy_range: FQ
    # Mark the first step of the copy range.
    is_first: FQ
    # Mark the last step of the copy range.
    is_last: FQ
    # Mark a step, which is a reader row (1) followed by a writer row (0).
    q_step: FQ

    def __init__(self, row: CopyCircuitRow):
        self.is_copy_range = FQ(1) # TODO: implement
        self.is_first = row.is_first
        self.is_last = row.is_last
        self.q_step = row.q_step


def verify_row_copy_range(cs: ConstraintSystem, curr: CopyRangeGadget, next: CopyRangeGadget) -> Expression:
    cs.constrain_bool(curr.is_first)
    cs.constrain_bool(curr.is_last)
    # A writer row cannot be first:  is_first == 0 when q_step == 0
    cs.constrain_zero((1 - curr.q_step) * curr.is_first)
    # A reader row cannot be last:  is_last == 0 when q_step == 1
    cs.constrain_zero(curr.q_step * curr.is_last)

    # A row is copying iif it is the first row, or the previous row was copying and not the last of an event.
    #
    # is_copy_range[i+1] =
    #     is_first[i+1] OR
    #     is_copy_range[i] AND NOT is_last[i]
    cs.constrain_equal(next.is_copy_range, 
                       next.is_first +
                       (1 - next.is_first) * curr.is_copy_range * (1 - curr.is_last))


# The RWC_Gadget tracks the current RW counter, and how many RW operations are left to count.
class RWC_Gadget:
    rw_counter: Expression
    rwc_inc_left: Expression

    def __init__(self, row: CopyCircuitRow):
        self.rw_counter = row.rw_counter
        self.rwc_inc_left = row.rwc_inc_left


def verify_row_rw_counter(cs: ConstraintSystem, rg_0: RWC_Gadget, rg_1: RWC_Gadget, rwc_diff_0: Expression):
    # After applying the current RW operation (rwc_diff_0), if there are still RW operations to count, then the counter is propagated to the next row.
    # TODO: rather use is_last_row_of_event?
    left_1 = rg_0.rwc_inc_left - rwc_diff_0
    with cs.condition(left_1):
        cs.constrain_equal(rg_1.rw_counter, rg_0.rw_counter + rwc_diff_0)
        cs.constrain_equal(rg_1.rwc_inc_left, left_1)

    # TODO: constrain rwc_inc_left to non-zero when used, and zero when not used?


# Decode the tag into boolean indicators for each data type.
def verify_tag_decoding(cs: ConstraintSystem, row: CopyCircuitRow):
    cs.constrain_equal(row.is_memory, cs.is_zero(row.tag - CopyDataTypeTag.Memory))
    cs.constrain_equal(row.is_bytecode, cs.is_zero(row.tag - CopyDataTypeTag.Bytecode))
    cs.constrain_equal(row.is_tx_calldata, cs.is_zero(row.tag - CopyDataTypeTag.TxCalldata))
    cs.constrain_equal(row.is_tx_log, cs.is_zero(row.tag - CopyDataTypeTag.TxLog))
    cs.constrain_equal(row.is_rlc_acc, cs.is_zero(row.tag - CopyDataTypeTag.RlcAcc))
    # TODO: constrain read-only and write-only data types?


def verify_row(cs: ConstraintSystem, tables: Tables, rows: Sequence[CopyCircuitRow], rand: FQ):
    # Decode the tag into boolean indicators for each data type.
    verify_tag_decoding(cs, rows[0])

    # Copy Range detector.
    copy_range_0 = CopyRangeGadget(rows[0])
    copy_range_1 = CopyRangeGadget(rows[1])
    copy_range_2 = CopyRangeGadget(rows[2])
    # Verify the transition from one row to the next.
    verify_row_copy_range(cs, copy_range_0, copy_range_1)

    # Word iterator.
    word_iter_0 = WordIterator(rows[0])
    word_iter_1 = WordIterator(rows[1])
    word_iter_2 = WordIterator(rows[2])
    word_continue_0 = verify_step_word_iterator(cs, word_iter_0, word_iter_2)

    # Verify the propagation of parameters between two copy steps. This happens inside of the copy range (not padding), except at the last step (not last two rows), and also outside of the copy range if a word is still being processed (word_continue_0 = 1). 
    # TODO: and not Padding
    last_step = rows[0].is_last + rows[1].is_last
    not_last_step = 1 - last_step
    with cs.condition(not_last_step + word_continue_0.expr()) as cs:
        # ID, tag, and src_addr_end are constant within a copy event.
        cs.constrain_equal(rows[0].id.value(), rows[2].id.value())
        cs.constrain_equal(rows[0].tag, rows[2].tag)
        cs.constrain_equal(rows[0].src_addr_end, rows[2].src_addr_end)
        # The address increments by 1 from a step to the next.
        cs.constrain_equal(rows[0].addr + 1, rows[2].addr)

    # Word RLC accumulators that read memory. This applies to both reader and writer rows.
    rlc_reader_0 = WordRlcGadget(word_iter_0, rows[0].rlc_acc)
    rlc_reader_2 = WordRlcGadget(word_iter_2, rows[2].rlc_acc)
    # The RLC of a step (at rows[2]) must include the byte of that step, on top of the previous accumulator value (at rows[0]).
    read_byte_2 = rows[2].value
    verify_step_word_rlc(cs, rand, rlc_reader_0, rlc_reader_2, read_byte_2)

    # What is the updated byte on rows[2]?
    # On a writer row inside of the copy range, copy a byte from the source ([1]) to the destination ([2]).
    # On a reader row, or on a writer row outside of the copy range, the updated and read bytes are the same.
    is_source_to_dest_2 = copy_range_2.is_copy_range * (1 - rows[2].q_step)
    source_byte_1 = rows[1].value
    updated_byte_2 = select(is_source_to_dest_2, source_byte_1, read_byte_2)

    # The word RLC accumulator that updates memory.
    rlc_updater_0 = WordRlcGadget(word_iter_0, rows[0].rlc_acc_update)
    rlc_updater_2 = WordRlcGadget(word_iter_2, rows[2].rlc_acc_update)
    # The RLC of a step (at rows[2]) must include the byte of that step, on top of the previous accumulator value (at rows[0]).
    verify_step_word_rlc(cs, rand, rlc_updater_0, rlc_updater_2, updated_byte_2)

    # Whether an RW operation is performed on this row 0.
    rw_diff_0 = word_iter_0.is_word_end

    # Maintain the RW counter, from one row to the next.
    rg_0 = RWC_Gadget(rows[0])
    rg_1 = RWC_Gadget(rows[1])
    verify_row_rw_counter(cs, rg_0, rg_1, rw_diff_0)
    
    # Do the RW operation.
    with cs.condition(rw_diff_0):
        is_write = 1 - rows[0].q_step
        tag = select(rows[0].is_memory, FQ(RWTableTag.Memory), FQ(RWTableTag.TxLog))
        slot_addr = rows[0].addr - 31
        tables.rw_lookup(
            rw_counter=rg_0.rw_counter,
            rw=is_write,
            tag=tag,
            id=rows[0].id,
            address=slot_addr,
            value=rlc_updater_0.get_final_rlc(rand),
            value_prev=rlc_reader_0.get_final_rlc(rand),
        )

    # Check the end condition that the counter of RW operations is fully consumed, that is rwc_inc_left goes to zero.
    # We look at whether rows[1] is marked with is_last=1, meaning rows[1] is the last writer row, and rows[0] is the last reader row.
    with cs.condition(rows[1].is_last) as cs:
        # We look at the counter at the row before last. There can be 0, 1, or 2 RW operations left to happen from the reader, the writer, or both.
        # If a word is being processed on a row, then an RW operation will happen at the end of the word, which is either
        # that same row or a subsequent one.
        # TODO: handle padding of out-of-bounds reads.
        rw_to_finish_0 = word_iter_0.is_enabled + word_iter_1.is_enabled
        cs.constrain_equal(rows[0].rwc_inc_left, rw_to_finish_0)

    # for RlcAcc type, value == rlc_acc at the last row
    with cs.condition(rows[1].is_last * rows[1].is_rlc_acc) as cs:
        cs.constrain_equal(rows[1].rlc_acc, rows[1].value)


# Whether the RW counter should be maintained from a row to the next.
def continue_rwc(word_iter_0: WordIterator, word_iter_1: WordIterator) -> Expression:
    # A word is running if it is enabled and not at the end.
    return word_iter.is_enabled.expr() * (1 - word_iter.is_word_end.expr())


# TODO: maybe not needed.
def is_last_row_of_event(copy_range_1: CopyRangeGadget, word_iter_0: WordIterator, word_iter_1: WordIterator) -> Expression:

    # a: if in the copy range and not the end of it, then this is not the last row.
    # b: if word iterator 0 is running and not at the end, then this is not the last row.
    # c: if word iterator 1 is running and not at the end, then this is not the last row.
    # Otherwise, this is the last row.
    # is_last_row_of_event = !a AND !b AND !c
    # TODO: make sure all variables are booleans.
    a = copy_range_1.is_copy_range.expr() * (1 - copy_range_1.is_last.expr())
    b = word_iter_0.is_enabled.expr() * (1 - word_iter_0.is_word_end.expr())
    c = word_iter_1.is_enabled.expr() * (1 - word_iter_1.is_word_end.expr())
    return (1 - a) * (1 - b) * (1 - c)


def verify_step(cs: ConstraintSystem, rows: Sequence[CopyCircuitRow], r: FQ):
    with cs.condition(rows[0].q_step):
        # bytes_left == 1 for last step
        cs.constrain_zero(rows[1].is_last * (1 - rows[0].bytes_left))
        # bytes_left == bytes_left_next + 1 for non-last step
        # TODO: and not Padding
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
        verify_row(cs, tables, rows, r)
        verify_step(cs, rows, r)

        # lookup into tables
        if row.is_memory == 1 and row.is_pad == 0:
            pass # Done in verify_row
        if row.is_bytecode == 1 and row.is_pad == 0:
            val = tables.bytecode_lookup(
                row.id, FQ(BytecodeFieldTag.Byte), row.addr, row.is_code
            ).value
            cs.constrain_equal(cast_expr(val, FQ), row.value)
        if row.is_tx_calldata == 1 and row.is_pad == 0:
            val = tables.tx_lookup(row.id, FQ(TxContextFieldTag.CallData), row.addr).value
            cs.constrain_equal(val, row.value)
        if row.is_tx_log == 1:
            pass # Done in verify_row
