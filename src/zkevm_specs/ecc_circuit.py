from __future__ import annotations
from typing import List, NamedTuple, Tuple
from py_ecc.bn128.bn128_curve import is_on_curve, b, b2, multiply
from py_ecc.bn128 import bn128_curve

from zkevm_specs.util.arithmetic import FP, RLC
from .evm_circuit import EccTableRow
from .util import ConstraintSystem, FQ, Word, ECCVerifyChip, ECCPairingVerifyChip
from zkevm_specs.evm_circuit.table import EccOpTag


class EccCircuitRow:
    """
    ECC circuit
    """

    row: EccTableRow

    ecc_chip: ECCVerifyChip

    ecc_pairing_chip: ECCPairingVerifyChip

    def __init__(
        self, row: EccTableRow, ecc_chip: ECCVerifyChip, ecc_pairing_chip: ECCPairingVerifyChip
    ) -> None:
        self.row = row
        self.ecc_chip = ecc_chip
        self.ecc_pairing_chip = ecc_pairing_chip

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
        else:
            raise TypeError(f"Not supported type: {op_type}")

    @classmethod
    def assign_add(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[FP, FP]):
        # 1. verify validity of input points p0 and p1
        precheck_p0x = cls.check_fq(p0[0].int_value())
        precheck_p0y = cls.check_fq(p0[1].int_value())
        precheck_p1x = cls.check_fq(p1[0].int_value())
        precheck_p1y = cls.check_fq(p1[1].int_value())

        # We use (0, 0) to represent an infinite point in the circuit
        # and there is no way to represent as `None` in the circuit
        # (values in Halo2 cell should be a FQ so `None` is impossible).
        # However, `None` represents a infinite point in `is_on_curve`.
        # Therefore, we have the following type conversion.
        point0 = (
            None
            if p0[0].int_value() == 0 and p0[1].int_value() == 0
            else (FP(p0[0].int_value()), FP(p0[1].int_value()))
        )
        point1 = (
            None
            if p1[0].int_value() == 0 and p1[1].int_value() == 0
            else (FP(p1[0].int_value()), FP(p1[1].int_value()))
        )
        is_valid_points = is_on_curve(point0, b) and is_on_curve(point1, b)

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

        return cls(ecc_table, ecc_chip, None)

    @classmethod
    def assign_mul(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]):
        # verify validity of input point
        precheck_px = cls.check_fq(p0[0].int_value())
        precheck_py = cls.check_fq(p0[1].int_value())

        # (0, 0) represents an infinite point
        point0 = (
            None
            if p0[0].int_value() == 0 and p0[1].int_value() == 0
            else (FP(p0[0].int_value()), FP(p0[1].int_value()))
        )
        is_valid_point = is_on_curve(point0, b)

        # Scalar is stored in the first 32 bytes of p1 so the second part of p1 (aka. p[1]) is zero
        # Besides, there is no limit on scalar `s` which means it can be larger than FP.field_modulus
        precheck_s = p1[1].int_value() == 0

        is_valid = is_valid_point and precheck_s and precheck_px and precheck_py

        self_p_x = p0[0].int_value()
        self_p_y = p0[1].int_value()
        self_s = p1[0].int_value()

        ecc_chip = ECCVerifyChip.assign(
            p0=(FP(self_p_x), FP(self_p_y)),
            p1=(FP(self_s), FP.zero()),
            output=out,
        )
        ecc_table = EccTableRow(
            FQ(EccOpTag.Mul),
            Word(self_p_x),
            Word(self_p_y),
            Word(self_s),
            Word(0),
            FQ.zero(),
            out[0],
            out[1],
            FQ(is_valid),
        )

        return cls(ecc_table, ecc_chip, None)

    @classmethod
    def assign_pairing(
        cls, pts: List[Tuple[Word, Word, Word, Word, Word, Word]], out: Word, keccak_randomness: FQ
    ):
        ps_g1 = []
        qs_g2 = []
        is_valid = True
        input_bytes = bytearray(b"")
        num_of_pairings = 0
        for p in pts:
            p_x = p[0].int_value()
            p_y = p[1].int_value()
            q_x1 = p[3].int_value()
            q_x2 = p[2].int_value()
            q_y1 = p[5].int_value()
            q_y2 = p[4].int_value()

            p_g1 = (FP(p_x), FP(p_y))
            q_g2 = (
                bn128_curve.FQ2([q_x1, q_x2]),
                bn128_curve.FQ2([q_y1, q_y2]),
            )
            ps_g1.append(p_g1)
            qs_g2.append(q_g2)

            ### verify validity of input points
            # 1. values of p0, p1 and p2 are within FQ.field_modulus
            precheck_px = cls.check_fq(p_x)
            precheck_py = cls.check_fq(p_y)
            precheck_qx1 = cls.check_fq(q_x1)
            precheck_qx2 = cls.check_fq(q_x2)
            precheck_qy1 = cls.check_fq(q_y1)
            precheck_qy2 = cls.check_fq(q_y2)

            # 2. p0 on G1, and p1 and p2 on G2 are all on the curve
            # (0, 0) represents an infinite point in the circuit
            point1_g1 = None if p_x == 0 and p_y == 0 else p_g1
            point2_g2 = None if q_x1 == 0 and q_x2 == 0 and q_y1 == 0 and q_y2 == 0 else q_g2

            # 3.point * curve order == infinity
            # ref: https://github.com/ethereum/execution-specs/blob/master/src/ethereum/paris/vm/precompiled_contracts/alt_bn128.py#L142-L149
            result = multiply(point1_g1, bn128_curve.curve_order)
            valid_p = True if result is None else False
            result = multiply(point2_g2, bn128_curve.curve_order)
            valid_q = True if result is None else False

            is_valid_points = (
                is_on_curve(point1_g1, b) and is_on_curve(point2_g2, b2) and valid_p and valid_q
            )

            is_valid = is_valid and (
                precheck_px
                and precheck_py
                and precheck_qx1
                and precheck_qx2
                and precheck_qy1
                and precheck_qy2
                and is_valid_points
            )

            # construct input bytes for RLC
            input_bytes.extend(p_x.to_bytes(32, "little"))
            input_bytes.extend(p_y.to_bytes(32, "little"))
            input_bytes.extend(q_x1.to_bytes(32, "little"))
            input_bytes.extend(q_x2.to_bytes(32, "little"))
            input_bytes.extend(q_y1.to_bytes(32, "little"))
            input_bytes.extend(q_y2.to_bytes(32, "little"))
            num_of_pairings += 1

        ecc_pairing_chip = ECCPairingVerifyChip.assign(
            p=ps_g1,
            q=qs_g2,
            output=FQ(is_valid),
        )
        ecc_table = EccTableRow(
            FQ(EccOpTag.Pairing),
            Word(0),
            Word(0),
            Word(0),
            Word(0),
            RLC(
                bytes(reversed(input_bytes)), keccak_randomness, n_bytes=num_of_pairings * 192
            ).expr(),
            out.hi.expr(),
            out.lo.expr(),
            FQ(is_valid),
        )

        return cls(ecc_table, None, ecc_pairing_chip)

    def verify(
        self,
        cs: ConstraintSystem,
        max_add_ops: int,
        max_mul_ops: int,
        max_pairing_ops: int,
        keccak_randomness: FQ,
    ):
        is_add = cs.is_equal(self.row.op_type, FQ(EccOpTag.Add))
        is_mul = cs.is_equal(self.row.op_type, FQ(EccOpTag.Mul))
        is_pairing = cs.is_equal(self.row.op_type, FQ(EccOpTag.Pairing))

        # Must be one of above operations
        cs.constrain_equal(is_add + is_mul + is_pairing, FQ(1))

        # Copy constraints between EccTable and ECCVerifyChip
        if is_add == FQ.one() or is_mul == FQ.one():
            cs.constrain_equal_word(Word(self.ecc_chip.p0[0].n), self.row.px)
            cs.constrain_equal_word(Word(self.ecc_chip.p0[1].n), self.row.py)
            cs.constrain_equal_word(Word(self.ecc_chip.p1[0].n), self.row.qx)
            cs.constrain_equal_word(Word(self.ecc_chip.p1[1].n), self.row.qy)
            cs.constrain_equal(self.ecc_chip.output[0], self.row.out_x)
            cs.constrain_equal(self.ecc_chip.output[1], self.row.out_y)
            # input_rlc is zero bcs it's only used in pairing
            cs.constrain_zero(self.row.input_rlc)
        else:  # if is_pairing is true
            # p and q are all zero. All input points are RLCed and stored in input_rlc
            cs.constrain_zero_word(self.row.px)
            cs.constrain_zero_word(self.row.py)
            cs.constrain_zero_word(self.row.qx)
            cs.constrain_zero_word(self.row.qy)

        cs.constrain_bool(self.row.is_valid)

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
            self.verify_pairing(cs, keccak_randomness)

    def verify_add(self, cs: ConstraintSystem):
        cs.constrain_equal(FQ(self.ecc_chip.verify_add()), self.row.is_valid)

    def verify_mul(self, cs: ConstraintSystem):
        # qy is zero bcs q is scalar in ecMul so we only use qx
        cs.constrain_zero_word(self.row.qy)

        cs.constrain_equal(FQ(self.ecc_chip.verify_mul()), self.row.is_valid)

    def verify_pairing(self, cs: ConstraintSystem, keccak_randomness: FQ):
        # output of pairing is stored in row.outy
        cs.constrain_zero(self.row.out_x)
        cs.constrain_equal(self.ecc_pairing_chip.output, self.row.out_y)

        num_of_pairings = 0
        input_bytes = bytearray(b"")
        for p, q in zip(self.ecc_pairing_chip.p, self.ecc_pairing_chip.q):
            pp = None if p[0].n == 0 and p[1].n == 0 else (p[0], p[1])
            pq = None if q[0].coeffs == (0, 0) and q[1].coeffs == (0, 0) else (q[0], q[1])
            # point * curve order == infinity
            result = multiply(pp, bn128_curve.curve_order)
            valid_p = FQ.one() if result is None else FQ.zero()
            result = multiply(pq, bn128_curve.curve_order)
            valid_q = FQ.one() if result is None else FQ.zero()
            cs.constrain_equal(valid_p + valid_q, FQ(2))

            # concatenate input points for rlc
            input_bytes.extend(p[0].n.to_bytes(32, "little"))
            input_bytes.extend(p[1].n.to_bytes(32, "little"))
            input_bytes.extend(q[0].coeffs[0].n.to_bytes(32, "little"))
            input_bytes.extend(q[0].coeffs[1].n.to_bytes(32, "little"))
            input_bytes.extend(q[1].coeffs[0].n.to_bytes(32, "little"))
            input_bytes.extend(q[1].coeffs[1].n.to_bytes(32, "little"))
            num_of_pairings += 1

        # constrain the value of input_rlc in a row equals the rlc value of cells in ecc_pairing_chip
        inputs_rlc = RLC(
            bytes(reversed(input_bytes)), keccak_randomness, n_bytes=num_of_pairings * 192
        ).expr()
        cs.constrain_equal(self.row.input_rlc, inputs_rlc)

        cs.constrain_equal(FQ(self.ecc_pairing_chip.verify_pairing()), self.row.out_y)


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


def circuit2rows(circuit: EccCircuit, randomness_keccak: FQ) -> List[EccCircuitRow]:
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
        points: List[Tuple[Word, Word, Word, Word, Word, Word]] = []
        for g1_pt, g2_pt in zip(op.g1_pts, op.g2_pts):
            points.append(
                (
                    Word(g1_pt[0]),
                    Word(g1_pt[1]),
                    Word(g2_pt[0]),
                    Word(g2_pt[1]),
                    Word(g2_pt[2]),
                    Word(g2_pt[3]),
                )
            )
        row = EccCircuitRow.assign_pairing(points, Word(op.out), randomness_keccak)
        rows.append(row)

    return rows


def verify_circuit(circuit: EccCircuit, randomness_keccak: FQ) -> None:
    """
    Entry level circuit verification function
    """
    cs = ConstraintSystem()
    rows = circuit2rows(circuit, randomness_keccak)
    for row in rows:
        row.verify(
            cs, circuit.max_add_ops, circuit.max_mul_ops, circuit.max_pairing_ops, randomness_keccak
        )
