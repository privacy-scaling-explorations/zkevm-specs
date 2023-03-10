from typing import List
from .evm import (
    ExpCircuit,
    ExpCircuitRow,
)
from .util import (
    ConstraintSystem,
    FQ,
    Word,
    mul_add_words,
)


def verify_step(cs: ConstraintSystem, rows: List[ExpCircuitRow]):
    # for every step except the last
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last)) as cs:
        # base is the same across rows.
        cs.constrain_equal_word(rows[0].base, rows[1].base)
        # multiplication result from the "next" row `d` must be used as
        # the first multiplicand in the "cur" row `a`
        cs.constrain_equal_word(rows[0].a, rows[1].d)
        # identifier does not change over the steps of an exponentiation trace.
        cs.constrain_equal(rows[0].identifier, rows[1].identifier)

    # for every step
    with cs.condition(rows[0].is_step) as cs:
        # is_last is boolean.
        cs.constrain_bool(rows[0].is_last)
        # remainder (r), i.e. odd/even parity of exponent is boolean.
        cs.constrain_bool(rows[0].r)
        # is_last == 1 is followed by unusable row.
        # is_last == 0 is following by usable row.
        cs.constrain_equal(rows[0].is_last, (1 - rows[1].q_usable))
        # multiplication is assigned correctly
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            rows[0].a, rows[0].b, rows[0].c, rows[0].d
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])
        # the exponentiation at this step must equal the result of the corresponding multiplication.
        cs.constrain_equal_word(rows[0].exponentiation, rows[0].d)
        # the c in multiply-add (a * b + c == d) should be 0 since we are only multiplying.
        cs.constrain_zero_word(rows[0].c)
        # parity check multiplication is assigned correctly.
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            Word(2), rows[0].q, Word((rows[0].r, FQ(0))), rows[0].exponent
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])

    # for all steps (except the last), where exponent is odd
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last) * rows[0].r.expr()) as cs:
        # exponent::next == exponent::cur - 1
        cur_lo, cur_hi = rows[0].exponent.lo.expr(), rows[0].exponent.hi.expr()
        next_lo, next_hi = rows[1].exponent.lo.expr(), rows[1].exponent.hi.expr()
        # lo::next == lo::cur - 1
        cs.constrain_equal(next_lo, cur_lo - 1)
        # hi::next == hi::cur
        cs.constrain_equal(next_hi, cur_hi)
        # b == base
        cs.constrain_equal_word(rows[0].base, rows[0].b)

    # for all steps (except the last), where exponent is even
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last) * (1 - rows[0].r.expr())) as cs:
        # exponent::next == exponent::cur / 2
        cur_lo, cur_hi = rows[0].exponent.lo.expr(), rows[0].exponent.hi.expr()
        next_lo, next_hi = rows[1].exponent.lo.expr(), rows[1].exponent.hi.expr()
        quotient_lo, quotient_hi = rows[0].q.lo.expr(), rows[0].q.hi.expr()
        # exponent::next == exponent::cur // 2 (equate next lo/hi)
        cs.constrain_equal(next_lo, quotient_lo)
        cs.constrain_equal(next_hi, quotient_hi)
        # a == b
        cs.constrain_equal_word(rows[0].a, rows[0].b)

    # for the last step
    with cs.condition(rows[0].is_last) as cs:
        # exponent == 2
        exponent_lo, exponent_hi = rows[0].exponent.lo.expr(), rows[0].exponent.hi.expr()
        cs.constrain_equal(exponent_lo, FQ(2))
        cs.constrain_zero(exponent_hi)
        # a == base
        cs.constrain_equal_word(rows[0].base, rows[0].a)
        # b == base
        cs.constrain_equal_word(rows[0].base, rows[0].b)


def verify_exp_circuit(exp_circuit: ExpCircuit):
    cs = ConstraintSystem()
    exp_table = exp_circuit.table()
    n = len(exp_table)
    for i, row in enumerate(exp_table):
        rows = [
            row,
            exp_table[(i + 1) % n],
        ]
        verify_step(cs, rows)
