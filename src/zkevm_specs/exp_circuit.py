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
        # remainder is a boolean.
        cs.constrain_bool(rows[0].remainder)
        # remainder is correct, i.e. quotient * 2 + remainder == intermediate_exponent
        _overflow, carry_lo_hi, additional_constraints = mul_add_words(
            rows[0].quotient,
            RLC(2, n_bytes=32),
            RLC(rows[0].remainder.n, n_bytes=32),
            rows[0].intermediate_exponent,
        )
        cs.range_check(carry_lo_hi[0], 9)
        cs.range_check(carry_lo_hi[1], 9)
        cs.constrain_equal(additional_constraints[0][0], additional_constraints[0][1])
        cs.constrain_equal(additional_constraints[1][0], additional_constraints[1][1])

    # for all steps (except the last), where remainder == 1 (intermediate exponent -> odd)
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * rows[0].remainder) as cs:
        # intermediate_exponent::next == intermediate_exponent::cur - 1
        cur_lo, cur_hi = word_to_lo_hi(rows[0].intermediate_exponent)
        next_lo, next_hi = word_to_lo_hi(rows[1].intermediate_exponent)
        # lo::next == lo::cur - 1
        cs.constrain_equal(next_lo, cur_lo - 1)
        # hi::next == hi::cur
        cs.constrain_equal(next_hi, cur_hi)
        # b == base
        cs.constrain_equal(rows[0].base, rows[0].b)

    # for all steps (except the last), where remainder == 0 (intermediate exponent -> even)
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * (1 - rows[0].remainder)) as cs:
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
    for i, row in enumerate(exp_table):
        rows = [
            row,
            exp_table[(i + 1) % n],
        ]
        verify_step(cs, rows)
