from __future__ import annotations
from typing import List, NamedTuple, Tuple
from py_ecc.bn128.bn128_curve import is_inf, is_on_curve, b

from zkevm_specs.util.arithmetic import FP
from .evm_circuit import EccTableRow
from .util import ConstraintSystem, FQ, Word, ECCVerifyChip
from zkevm_specs.evm_circuit.table import EccOpTag


class EccCircuitRow:
    """
    ECC circuit
    """

    row: EccTableRow

    ecc_chip: ECCVerifyChip

    def __init__(self, row: EccTableRow, ecc_chip: ECCVerifyChip) -> None:
        self.row = row
        self.ecc_chip = ecc_chip

    @classmethod
    def check_fq(cls, value: int) -> bool:
        return value < int(FP.field_modulus)

    @classmethod
    def assign(
        cls,
        op_type: EccOpTag,
        p: List[Tuple[Word, Word]],
        out: Tuple[FP, FP],
    ):
        if op_type == EccOpTag.Add:
            return cls.assign_add(p[0], p[1], out)
        elif op_type == EccOpTag.Mul:
            return cls.assign_mul(p[0], p[1], out)
        elif op_type == EccOpTag.Pairing:
            return cls.assign_pairing(p, out)
        else:
            raise TypeError(f"Not supported type: {op_type}")

    @classmethod
    def assign_add(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[FP, FP]):
        # 1. verify validity of input points p0 and p1
        precheck_p0x = cls.check_fq(p0[0].int_value())
        precheck_p0y = cls.check_fq(p0[1].int_value())
        precheck_p1x = cls.check_fq(p1[0].int_value())
        precheck_p1y = cls.check_fq(p1[1].int_value())

        point0 = (FP(p0[0].int_value()), FP(p0[1].int_value()))
        point1 = (FP(p1[0].int_value()), FP(p1[1].int_value()))
        is_valid_p0 = is_on_curve(point0, b)
        is_valid_p1 = is_on_curve(point1, b)
        is_infinite_p0 = is_inf(point0)
        is_infinite_p1 = is_inf(point1)
        is_valid_points = (is_valid_p0 or is_infinite_p0) and (is_valid_p1 or is_infinite_p1)

        is_valid = (
            precheck_p0x and precheck_p0y and precheck_p1x and precheck_p1y and is_valid_points
        )

        self_p0_x = p0[0].int_value()
        self_p0_y = p0[1].int_value()
        self_p1_x = p1[0].int_value()
        self_p1_y = p1[1].int_value()

        ecc_chip = ECCVerifyChip.assign(
            p0=(FP(self_p0_x), FP(self_p0_y)),
            p1=(FP(self_p1_x), FP(self_p1_y)),
            output=out,
        )
        ecc_table = EccTableRow(
            FQ(EccOpTag.Add),
            Word(self_p0_x),
            Word(self_p0_y),
            Word(self_p1_x),
            Word(self_p1_y),
            FQ.zero(),
            out[0],
            out[1],
            FQ(is_valid),
        )

        return cls(ecc_table, ecc_chip)

    @classmethod
    def assign_mul(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]):
        raise NotImplementedError("assign_mul is not supported yet")

    @classmethod
    def assign_pairing(cls, p: List[Tuple[Word, Word]], out: Tuple[Word, Word]):
        raise NotImplementedError("assign_pairing is not supported yet")

    def verify(
        self, cs: ConstraintSystem, max_add_ops: int, max_mul_ops: int, max_pairing_ops: int
    ):
        # Copy constraints between EccTable and ECCVerifyChip
        cs.constrain_equal_word(Word(self.ecc_chip.p0[0].n), self.row.px)
        cs.constrain_equal_word(Word(self.ecc_chip.p0[1].n), self.row.py)
        cs.constrain_equal_word(Word(self.ecc_chip.p1[0].n), self.row.qx)
        cs.constrain_equal_word(Word(self.ecc_chip.p1[1].n), self.row.qy)
        cs.constrain_equal(self.ecc_chip.output[0], self.row.out_x)
        cs.constrain_equal(self.ecc_chip.output[1], self.row.out_y)

        is_add = cs.is_equal(self.row.op_type, FQ(EccOpTag.Add))
        is_mul = cs.is_equal(self.row.op_type, FQ(EccOpTag.Mul))
        is_pairing = cs.is_equal(self.row.op_type, FQ(EccOpTag.Pairing))
        # Must be one of above operations
        cs.constrain_equal(is_add + is_mul + is_pairing, FQ(1))

        num_add = 0
        num_mul = 0
        num_pairing = 0
        if is_add == FQ(1):
            num_add += 1
            assert (
                num_add <= max_add_ops
            ), f"exceeds max number of add operation, max_add_ops: {max_add_ops}"
            self.verify_add(cs)

        if is_mul == FQ(1):
            num_mul += 1
            assert (
                num_mul <= max_mul_ops
            ), f"exceeds max number of mul operation, max_mul_ops: {max_mul_ops}"
            self.verify_mul(cs)

        if is_pairing == FQ(1):
            num_pairing += 1
            assert (
                num_pairing <= max_pairing_ops
            ), f"exceeds max number of pairing operation, max_pairing_ops: {max_pairing_ops}"
            self.verify_pairing(cs)

    def verify_add(self, cs: ConstraintSystem):
        # input_rlc is zero bcs it's only used in pairing
        cs.constrain_zero(self.row.input_rlc)

        cs.constrain_equal(FQ(self.ecc_chip.verify_add()), self.row.is_valid)

    def verify_mul(self, cs: ConstraintSystem):
        # input_rlc is zero bcs it's only used in pairing
        cs.constrain_zero(self.row.input_rlc)
        # qy is zero bcs q is scalar in ecMul so we only use qx
        cs.constrain_zero(self.row.qy)

        cs.constrain_equal(FQ(self.ecc_chip.verify_mul()), self.row.is_valid)

    def verify_pairing(self, cs: ConstraintSystem):
        # p and q are all zero. All input points are RLCed and stored in input_rlc
        cs.constrain_zero(self.row.px)
        cs.constrain_zero(self.row.py)
        cs.constrain_zero(self.row.qx)
        cs.constrain_zero(self.row.qy)
        # output of pairing is either 0 or 1 and stored in the lower part
        cs.constrain_zero(self.row.out_x)
        cs.constrain_bool(self.row.out_y)
        cs.constrain_equal(self.row.out_y, self.row.is_valid)

        cs.constrain_equal(FQ(self.ecc_chip.verify_pairing()), self.row.is_valid)


class EcAdd(NamedTuple):
    p: Tuple[int, int]
    q: Tuple[int, int]
    out: Tuple[int, int]


class EcMul(NamedTuple):
    p: Tuple[int, int]
    s: int
    out: Tuple[int, int]


class EcPairing(NamedTuple):
    g1_pts: List[Tuple[int, int]]
    g2_pts: List[Tuple[int, int, int, int]]
    out: int


class EccCircuit:
    add_ops: List[EcAdd]
    mul_ops: List[EcMul]
    pairing_ops: List[EcPairing]

    max_add_ops: int
    max_mul_ops: int
    max_pairing_ops: int

    def __init__(
        self,
        max_add_ops: int,
        max_mul_ops: int,
        max_pairing_ops: int,
    ) -> None:
        self.add_ops = []
        self.mul_ops = []
        self.pairing_ops = []
        self.max_add_ops = max_add_ops
        self.max_mul_ops = max_mul_ops
        self.max_pairing_ops = max_pairing_ops

    def append_add(self, op: EcAdd):
        self.add_ops.append(op)

    def append_mul(self, op: EcMul):
        self.mul_ops.append(op)

    def append_pairing(self, op: EcPairing):
        self.pairing_ops.append(op)


def circuit2rows(circuit: EccCircuit) -> List[EccCircuitRow]:
    rows: List[EccCircuitRow] = []
    for op in circuit.add_ops:
        row = EccCircuitRow.assign(
            EccOpTag.Add,
            [
                (Word(op.p[0]), Word(op.p[1])),
                (Word(op.q[0]), Word(op.q[1])),
            ],
            (FP(op.out[0]), FP(op.out[1])),
        )
        rows.append(row)
    for op in circuit.mul_ops:
        row = EccCircuitRow.assign(
            EccOpTag.Mul,
            [(Word(op.p[0]), Word(op.p[1])), (Word(op.s), Word(0))],
            (FP(op.out[0]), FP(op.out[1])),
        )
        rows.append(row)
    for op in circuit.pairing_ops:
        points: List[Word] = []
        for i, g1_pt in enumerate(op.g1_pts):
            points.append(g1_pt[0])
            points.append(g1_pt[1])
            points.append(op.g2_pts[i][0])
            points.append(op.g2_pts[i][1])
            points.append(op.g2_pts[i][2])
            points.append(op.g2_pts[i][3])

        row = EccCircuitRow.assign(
            EccOpTag.Pairing,
            points,
            (FP(0), FP(op.out)),
        )
        rows.append(row)

    return rows


def verify_circuit(circuit: EccCircuit) -> None:
    """
    Entry level circuit verification function
    """
    cs = ConstraintSystem()
    rows = circuit2rows(circuit)
    for row in rows:
        row.verify(cs, circuit.max_add_ops, circuit.max_mul_ops, circuit.max_pairing_ops)
