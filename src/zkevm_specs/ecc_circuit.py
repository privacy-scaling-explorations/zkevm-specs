from __future__ import annotations
from typing import List, Sequence, Tuple
from py_ecc.bn128.bn128_curve import is_inf, is_on_curve, b
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
        return value < int(FQ.field_modulus)

    @classmethod
    def assign(
        cls, op_type: EccOpTag, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]
    ):
        if op_type == EccOpTag.Add:
            return cls.assign_add(p0, p1, out)
        elif op_type == EccOpTag.Mul:
            return cls.assign_add(p0, p1, out)
        elif op_type == EccOpTag.Pairing:
            return cls.assign_add(p0, p1, out)
        else:
            raise TypeError(f"Not supported type: {op_type}")

    @classmethod
    def assign_add(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]):
        # 1. verify validity of input points p0 and p1
        precheck_p0x = cls.check_fq(p0[0].int_value())
        precheck_p0y = cls.check_fq(p0[1].int_value())
        precheck_p1x = cls.check_fq(p1[0].int_value())
        precheck_p1y = cls.check_fq(p1[1].int_value())

        point0 = (FQ(p0[0].int_value()), FQ(p0[1].int_value()))
        point1 = (FQ(p1[0].int_value()), FQ(p1[1].int_value()))
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
        self_output_x = out[0].int_value()
        self_output_y = out[1].int_value()

        ecc_chip = ECCVerifyChip.assign(
            p0=(FQ(self_p0_x), FQ(self_p0_y)),
            p1=(FQ(self_p1_x), FQ(self_p1_y)),
            output=(FQ(self_output_x), FQ(self_output_y)),
        )
        ecc_table = EccTableRow(
            FQ(EccOpTag.Add),
            Word(self_p0_x),
            Word(self_p0_y),
            Word(self_p1_x),
            Word(self_p1_y),
            Word(self_output_x),
            Word(self_output_y),
            FQ(is_valid),
        )

        return cls(ecc_table, ecc_chip)

    @classmethod
    def assign_mul(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]):
        raise NotImplementedError("assign_mul is not supported yet")

    @classmethod
    def assign_pairing(cls, p0: Tuple[Word, Word], p1: Tuple[Word, Word], out: Tuple[Word, Word]):
        raise NotImplementedError("assign_pairing is not supported yet")

    def verify(
        self, cs: ConstraintSystem, max_add_ops: int, max_mul_ops: int, max_pairing_ops: int
    ):
        # Copy constraints between EccTable and ECCVerifyChip
        cs.constrain_equal_word(Word(self.ecc_chip.p0[0].n), self.row.px)
        cs.constrain_equal_word(Word(self.ecc_chip.p0[1].n), self.row.py)
        cs.constrain_equal_word(Word(self.ecc_chip.p1[0].n), self.row.qx)
        cs.constrain_equal_word(Word(self.ecc_chip.p1[1].n), self.row.qy)
        cs.constrain_equal_word(Word(self.ecc_chip.output[0].n), self.row.out_x)
        cs.constrain_equal_word(Word(self.ecc_chip.output[1].n), self.row.out_y)

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
            cs.constrain_equal(FQ(self.ecc_chip.verify_add()), self.row.is_valid)

        if is_mul == FQ(1):
            num_mul += 1
            assert (
                num_mul <= max_mul_ops
            ), f"exceeds max number of mul operation, max_mul_ops: {max_mul_ops}"
            cs.constrain_equal(FQ(self.ecc_chip.verify_mul()), self.row.is_valid)

        if is_pairing == FQ(1):
            num_pairing += 1
            assert (
                num_pairing <= max_pairing_ops
            ), f"exceeds max number of pairing operation, max_pairing_ops: {max_pairing_ops}"
            cs.constrain_equal(FQ(self.ecc_chip.verify_pairing()), self.row.is_valid)


class EccCircuit:
    rows: List[EccCircuitRow]
    max_add_ops: int
    max_mul_ops: int
    max_pairing_ops: int

    def __init__(
        self,
        max_add_ops: int,
        max_mul_ops: int,
        max_pairing_ops: int,
    ) -> None:
        self.rows = []
        self.max_add_ops = max_add_ops
        self.max_mul_ops = max_mul_ops
        self.max_pairing_ops = max_pairing_ops

    def table(self) -> Sequence[EccCircuitRow]:
        return self.rows

    def add(self, row: EccCircuitRow) -> EccCircuit:
        self.rows.append(row)
        return self


def verify_circuit(circuit: EccCircuit) -> None:
    """
    Entry level circuit verification function
    """
    cs = ConstraintSystem()
    for row in circuit.table():
        row.verify(cs, circuit.max_add_ops, circuit.max_mul_ops, circuit.max_pairing_ops)
