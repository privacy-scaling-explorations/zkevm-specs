from typing import Sequence
from .evm_circuit import Bn256Circuit, Bn256TableRow
from .util import ConstraintSystem


def verify(cs: ConstraintSystem, rows: Sequence[Bn256TableRow]):
    assert True


def verify_bn256_circuit(bn256_circuit: Bn256Circuit):
    cs = ConstraintSystem()
    bn256_table = bn256_circuit.table()
    n = len(bn256_table)
    for i, row in enumerate(bn256_table):
        rows = [
            row,
            bn256_table[(i + 1) % n],
            bn256_table[(i + 2) % n],
        ]
        verify(cs, rows)
