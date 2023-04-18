from .evm_circuit import Bn256Circuit, Bn256TableRow
from .util import ConstraintSystem


def verify_row(cs: ConstraintSystem, row: Bn256TableRow):
    assert True


def verify_ops(cs: ConstraintSystem, row: Bn256TableRow):
    assert True


def verify_bn256_table(bn256_circuit: Bn256Circuit):
    cs = ConstraintSystem()
    bn256_table = bn256_circuit.table()
    n = len(bn256_table)
    assert n == 1
    for i, row in enumerate(bn256_table):
        verify_row(cs, row)
        verify_ops(cs, row)
