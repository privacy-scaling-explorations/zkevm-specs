from typing import List
from .evm import (
    ExpCircuit,
    ExpCircuitRow,
)
from .util import (
    ConstraintSystem,
    FQ,
    RLC,
    mul_add_words,
    word_to_lo_hi,
)


def verify_step(cs: ConstraintSystem, rows: List[ExpCircuitRow]):
    # for every non-padded step except the last
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last) * (1 - rows[0].padding)) as cs:
        # base is the same across rows.
        cs.constrain_equal(rows[0].base, rows[1].base)
        # multiplication result from the "next" row `d` must be used as
        # the first multiplicand in the "cur" row `a`
        cs.constrain_equal(rows[0].a, rows[1].d)
        # identifier does not change over the steps of an exponentiation trace.
        cs.constrain_equal(rows[0].identifier, rows[1].identifier)

    # for every non-padded step
    with cs.condition(rows[0].is_step * (1 - rows[0].padding)) as cs:
        # is_last is boolean.
        cs.constrain_bool(rows[0].is_last)
        # remainder (r), i.e. odd/even parity of exponent is boolean.
        cs.constrain_bool(rows[0].r)
        # multiplication is assigned correctly
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            rows[0].a, rows[0].b, rows[0].c, rows[0].d
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])
        # the exponentiation at this step must equal the result of the corresponding multiplication.
        cs.constrain_equal(rows[0].exponentiation, rows[0].d)
        # the c in multiply-add (a * b + c == d) should be 0 since we are only multiplying.
        cs.constrain_zero(rows[0].c)
        # parity check multiplication is assigned correctly.
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            RLC(2), rows[0].q, rows[0].r, rows[0].exponent
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])

    # for all non-padded steps (except the last), where exponent is odd
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last) * rows[0].r.expr() * (1 - rows[0].padding)) as cs:
        # exponent::next == exponent::cur - 1
        cur_lo, cur_hi = word_to_lo_hi(rows[0].exponent)
        next_lo, next_hi = word_to_lo_hi(rows[1].exponent)
        # lo::next == lo::cur - 1
        cs.constrain_equal(next_lo, cur_lo - 1)
        # hi::next == hi::cur
        cs.constrain_equal(next_hi, cur_hi)
        # b == base
        cs.constrain_equal(rows[0].base, rows[0].b)

    # for all non-padded steps (except the last), where exponent is even
    with cs.condition(rows[0].is_step * (1 - rows[0].is_last) * (1 - rows[0].r.expr()) * (1 - rows[0].padding)) as cs:
        # exponent::next == exponent::cur / 2
        cur_lo, cur_hi = word_to_lo_hi(rows[0].exponent)
        next_lo, next_hi = word_to_lo_hi(rows[1].exponent)
        quotient_lo, quotient_hi = word_to_lo_hi(rows[0].q)
        # exponent::next == exponent::cur // 2 (equate next lo/hi)
        cs.constrain_equal(next_lo, quotient_lo)
        cs.constrain_equal(next_hi, quotient_hi)
        # a == b
        cs.constrain_equal(rows[0].a, rows[0].b)

    # for the last non-padded step
    with cs.condition(rows[0].is_last * (1 - rows[0].padding)) as cs:
        # exponent == 2
        exponent_lo, exponent_hi = word_to_lo_hi(rows[0].exponent)
        cs.constrain_equal(exponent_lo, FQ(2))
        cs.constrain_zero(exponent_hi)
        # a == base
        cs.constrain_equal(rows[0].base, rows[0].a)
        # b == base
        cs.constrain_equal(rows[0].base, rows[0].b)
        # followed by padding
        cs.constrain_equal(rows[1].padding, FQ(1))

    # for padding
    with cs.condition(rows[0].padding * (1 - rows[0].is_final)) as cs:
        # padding::next == padding::cur
        cs.constrain_equal(rows[1].padding, rows[0].padding)
        # is_step == 0
        cs.constrain_zero(rows[0].is_step)
        # is_last == 0
        cs.constrain_zero(rows[0].is_last)
        # base == 0
        cs.constrain_zero(rows[0].base)
        # exponent == 0
        cs.constrain_zero(rows[0].exponent)
        # exponentiation == 0
        cs.constrain_zero(rows[0].exponentiation)
        # a == 0
        cs.constrain_zero(rows[0].a)
        # b == 0
        cs.constrain_zero(rows[0].b)
        # c == 0
        cs.constrain_zero(rows[0].c)
        # d == 0
        cs.constrain_zero(rows[0].d)
        # q == 0
        cs.constrain_zero(rows[0].q)
        # r == 0
        cs.constrain_zero(rows[0].r)



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
