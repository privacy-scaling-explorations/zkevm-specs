from typing import List
from .evm import (
    ExpCircuit,
    ExpCircuitRow,
)
from .util import (
    ConstraintSystem,
    FQ,
    lo_hi_to_64s,
)


def verify_step(cs: ConstraintSystem, rows: List[ExpCircuitRow]):
    # for every step except the last
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last)) as cs:
        # base limbs are the same across rows.
        cs.constrain_equal(rows[0].base_limb0, rows[1].base_limb0)
        cs.constrain_equal(rows[0].base_limb1, rows[1].base_limb1)
        cs.constrain_equal(rows[0].base_limb2, rows[1].base_limb2)
        cs.constrain_equal(rows[0].base_limb3, rows[1].base_limb3)
        # multiplication result from the "next" row `d` must be used as
        # the first multiplicand in the "cur" row `a`
        d_next_limbs = lo_hi_to_64s((rows[1].d_lo, rows[1].d_hi))
        cs.constrain_equal(rows[0].a_limb0, d_next_limbs[0])
        cs.constrain_equal(rows[0].a_limb1, d_next_limbs[1])
        cs.constrain_equal(rows[0].a_limb2, d_next_limbs[2])
        cs.constrain_equal(rows[0].a_limb3, d_next_limbs[3])

    # for the last row, we have: base * base == base^2
    with cs.condition(rows[0].q_step * rows[0].is_last) as cs:
        # a == base (all limbs)
        cs.constrain_equal(rows[0].base_limb0, rows[0].a_limb0)
        cs.constrain_equal(rows[0].base_limb1, rows[0].a_limb1)
        cs.constrain_equal(rows[0].base_limb2, rows[0].a_limb2)
        cs.constrain_equal(rows[0].base_limb3, rows[0].a_limb3)
        # b == base (all limbs)
        cs.constrain_equal(rows[0].base_limb0, rows[0].b_limb0)
        cs.constrain_equal(rows[0].base_limb1, rows[0].b_limb1)
        cs.constrain_equal(rows[0].base_limb2, rows[0].b_limb2)
        cs.constrain_equal(rows[0].base_limb3, rows[0].b_limb3)

    # for every step
    with cs.condition(rows[0].q_step) as cs:
        # the intermediate exponentiation must equal the result of the corresponding multiplication.
        cs.constrain_equal(rows[0].intermediate_exponentiation_lo, rows[0].d_lo)
        cs.constrain_equal(rows[0].intermediate_exponentiation_hi, rows[0].d_hi)
        # the c in multiply-add (a * b + c == d) should be 0 since we are only multiplying.
        cs.constrain_zero(rows[0].c_lo)
        cs.constrain_zero(rows[0].c_lo)
        # remainder is a boolean.
        cs.constrain_bool(rows[0].remainder)
        # TODO(rohit): remainder is correct, i.e. remainder == intermediate_exponent % 2

    # for all rows (except the last), where remainder == 1 (intermediate exponent -> odd)
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * rows[0].remainder) as cs:
        # intermediate_exponent::next == intermediate_exponent::cur - 1
        # 1. lo::next == lo::cur - 1
        cs.constrain_equal(rows[1].intermediate_exponent_lo, rows[0].intermediate_exponent_lo - 1)
        # 2. hi::next == hi::cur
        cs.constrain_equal(rows[1].intermediate_exponent_hi, rows[0].intermediate_exponent_hi)

    # for all rows (except the last), where remainder == 0 (intermediate exponent -> even)
    with cs.condition(rows[0].q_step * (1 - rows[0].is_last) * (1 - rows[0].remainder)) as cs:
        # intermediate_exponent::next == intermediate_exponent::cur / 2
        cs.constrain_equal(rows[1].intermediate_exponent_lo * 2, rows[0].intermediate_exponent_lo)
        cs.constrain_equal(rows[1].intermediate_exponent_hi * 2, rows[0].intermediate_exponent_hi)

    # for the last step, intermediate exponent == 2
    with cs.condition(rows[0].q_step * rows[0].is_last) as cs:
        cs.constrain_equal(rows[0].intermediate_exponent_lo, FQ(2))
        cs.constrain_zero(rows[0].intermediate_exponent_hi)


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
