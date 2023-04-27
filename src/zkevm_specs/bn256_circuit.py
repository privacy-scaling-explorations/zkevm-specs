from typing import Final, Dict
from .util import (
    ConstraintSystem,
    FQ,
    G1,
    CurvePoint,
    point_add,
    N_BYTES_WORD,
    gfp_to_fq,
    fq_to_gfp,
)
from .evm_circuit import Bn256Circuit, Bn256TableRow, Bn256OperationTag, lt_word


def verify_row(cs: ConstraintSystem, row: Bn256TableRow):
    # tag is in range
    cs.range_check(FQ(row.tag), 3)
    # for BN256ADD operation
    with cs.condition(1 - (row.tag - Bn256OperationTag.BN256ADD)) as cs:
        field_modulus = FQ(FQ.field_modulus - 1)
        cs.constrain_equal(FQ(1), lt_word(row.input0, field_modulus, N_BYTES_WORD))
        cs.constrain_equal(FQ(1), lt_word(row.input1, field_modulus, N_BYTES_WORD))
        cs.constrain_equal(FQ(1), lt_word(row.input2, field_modulus, N_BYTES_WORD))
        cs.constrain_equal(FQ(1), lt_word(row.input3, field_modulus, N_BYTES_WORD))
        cs.constrain_equal(FQ(1), lt_word(row.output0, field_modulus, N_BYTES_WORD))
        cs.constrain_equal(FQ(1), lt_word(row.output1, field_modulus, N_BYTES_WORD))


def verify_ops(cs: ConstraintSystem, row: Bn256TableRow):
    # for BN256ADD operation
    with cs.condition(1 - (row.tag - Bn256OperationTag.BN256ADD)) as cs:
        point_a = point_b = G1(CurvePoint())
        point_a.p.x = fq_to_gfp(row.input0)
        point_a.p.y = fq_to_gfp(row.input1)
        point_a.p.x = fq_to_gfp(row.input2)
        point_a.p.y = fq_to_gfp(row.input3)
        # perform bn256 addition
        point_c = point_add(point_a, point_b)
        x = gfp_to_fq(point_c.p.x)
        y = gfp_to_fq(point_c.p.y)
        cs.constrain_equal(row.output0, x)
        cs.constrain_equal(row.output1, y)


def verify_bn256_table(bn256_circuit: Bn256Circuit):
    cs = ConstraintSystem()
    bn256_table = bn256_circuit.table()
    n = len(bn256_table)
    assert n == 1
    for i, row in enumerate(bn256_table):
        verify_row(cs, row)
        verify_ops(cs, row)


class Bn256OperationInfo:
    """
    Bn256 operation information.
    """

    input_length: int
    output_length: int
    is_input_dynamic: bool

    def __init__(
        self, input_length: int, output_length: int, is_input_dynamic: bool = False
    ) -> None:
        self.input_length = input_length
        self.output_length = output_length
        self.is_input_dynamic = is_input_dynamic


BN256_INFO_MAP: Final[Dict[Bn256OperationTag, Bn256OperationInfo]] = dict(
    {
        Bn256OperationTag.ECRECOVER: Bn256OperationInfo(4, 1),
        Bn256OperationTag.BN256ADD: Bn256OperationInfo(4, 2),
        Bn256OperationTag.BN256SCALARMUL: Bn256OperationInfo(3, 1),
        Bn256OperationTag.BN256PAIRING: Bn256OperationInfo(4, 1, True),
    }
)
