from typing import List
from .evm import (
    ExpCircuit,
    ExpCircuitRow,
)
from .util import (
    ConstraintSystem,
)


def verify_step(cs: ConstraintSystem, rows: List[ExpCircuitRow]):
    # TODO(rohit): implement
    print("hello")


def verify_exp_circuit(exp_circuit: ExpCircuit):
    cs = ConstraintSystem()
    exp_table = exp_circuit.table()
    n = len(exp_table)
    for i, row in enumerate(exp_table):
        rows = [
            # 7 rows from q_step == 1
            row,
            exp_table[(i + 1) % n],
            exp_table[(i + 2) % n],
            exp_table[(i + 3) % n],
            exp_table[(i + 4) % n],
            exp_table[(i + 5) % n],
            exp_table[(i + 6) % n],
            # 4 rows from the next q_step == 1
            exp_table[(i + 7) % n],
            exp_table[(i + 8) % n],
            exp_table[(i + 9) % n],
            exp_table[(i + 10) % n],
        ]
        verify_step(cs, rows)
