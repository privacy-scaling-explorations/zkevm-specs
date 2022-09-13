from enum import IntEnum, auto
from typing import List, Set, Tuple
from .evm import (
    ExpCircuit,
    ExpCircuitRow,
)
from .util import (
    ConstraintSystem,
    FQ,
    mul_add_words,
    word_to_lo_hi,
)


class FixedTableTag(IntEnum):
    Odd = auto()
    Even = auto()


def _gen_fixed_table() -> Set[Tuple[FQ, FQ]]:
    table: List[Tuple[FQ, FQ]] = []
    # odd
    for i in range(1, 256, 2):
        table.append((FQ(FixedTableTag.Odd), FQ(i)))
    # even
    for i in range(0, 256, 2):
        table.append((FQ(FixedTableTag.Even), FQ(i)))
    return set(table)


def verify_step(cs: ConstraintSystem, rows: List[ExpCircuitRow], fixed_table: Set[Tuple[FQ, FQ]]):
    # for every step except the last
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last)) as cs:
        # base is the same across rows.
        cs.constrain_equal(rows[0].base, rows[1].base)
        # multiplication result from the "next" row `d` must be used as
        # the first multiplicand in the "cur" row `a`
        cs.constrain_equal(rows[0].a, rows[1].d)

    # for every step
    with cs.condition(rows[0].q_step) as cs:
        # is_first and is_last are boolean values
        cs.constrain_bool(rows[0].is_first)
        cs.constrain_bool(rows[0].is_last)
        # is_first is followed by is_first == 0
        cs.constrain_zero(rows[0].is_first * rows[1].is_first)
        # if this is an intermediate step (is_first == 0) then is_first does not change.
        cs.constrain_zero((1 - rows[0].is_first) * rows[1].is_first)
        # is_last is followed by padding
        cs.constrain_zero((1 - rows[0].is_last) * rows[1].is_pad)
        # multiplication is assigned correctly
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            rows[0].a, rows[0].b, rows[0].c, rows[0].d
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])
        # the intermediate exponentiation must equal the result of the corresponding multiplication.
        cs.constrain_equal(rows[0].intermediate_exponentiation, rows[0].d)
        # the c in multiply-add (a * b + c == d) should be 0 since we are only multiplying.
        cs.constrain_zero(rows[0].c)
        # is_odd, i.e. odd/even parity is a boolean.
        cs.constrain_bool(rows[0].is_odd)

    # lookup odd/even parity
    if rows[0].is_odd == FQ.one():
        assert (FQ(FixedTableTag.Odd), FQ(rows[0].lsb_intermediate_exponent)) in fixed_table
    else:
        assert (FQ(FixedTableTag.Even), FQ(rows[0].lsb_intermediate_exponent)) in fixed_table

    # for all steps (except the last), where exponent is odd
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * rows[0].is_odd) as cs:
        # intermediate_exponent::next == intermediate_exponent::cur - 1
        cur_lo, cur_hi = word_to_lo_hi(rows[0].intermediate_exponent)
        next_lo, next_hi = word_to_lo_hi(rows[1].intermediate_exponent)
        # lo::next == lo::cur - 1
        cs.constrain_equal(next_lo, cur_lo - 1)
        # hi::next == hi::cur
        cs.constrain_equal(next_hi, cur_hi)
        # b == base
        cs.constrain_equal(rows[0].base, rows[0].b)

    # for all steps (except the last), where exponent is even
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * (1 - rows[0].is_odd)) as cs:
        # intermediate_exponent::next == intermediate_exponent::cur / 2
        cur_lo, cur_hi = word_to_lo_hi(rows[0].intermediate_exponent)
        next_lo, next_hi = word_to_lo_hi(rows[1].intermediate_exponent)
        cs.constrain_equal(next_lo * 2, cur_lo)
        cs.constrain_equal(next_hi * 2, cur_hi)
        # a == b
        cs.constrain_equal(rows[0].a, rows[0].b)

    # for the last step
    with cs.condition(rows[0].is_last) as cs:
        # intermediate exponent == 2
        cs.constrain_equal(rows[0].intermediate_exponent.expr(), FQ(2))
        # a == base
        cs.constrain_equal(rows[0].base, rows[0].a)
        # b == base
        cs.constrain_equal(rows[0].base, rows[0].b)


def verify_exp_circuit(exp_circuit: ExpCircuit):
    cs = ConstraintSystem()
    exp_table = exp_circuit.table()
    n = len(exp_table)
    fixed_table = _gen_fixed_table()
    for i, row in enumerate(exp_table):
        rows = [
            row,
            exp_table[(i + 1) % n],
        ]
        verify_step(cs, rows, fixed_table)
