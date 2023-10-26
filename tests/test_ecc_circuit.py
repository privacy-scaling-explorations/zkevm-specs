import pytest
from typing import Tuple, NamedTuple
from zkevm_specs.ecc_circuit import EccCircuitRow, verify_circuit, EccCircuit
from zkevm_specs.evm_circuit.table import EccOpTag
from zkevm_specs.util import Word


class EccOps(NamedTuple):
    op_type: EccOpTag
    p: Tuple[int, int]
    q: Tuple[int, int]
    out: Tuple[int, int]


def verify(
    circuit: EccCircuit,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness.
    If `success` is False, expect the verification to fail.
    """

    exception = None
    try:
        verify_circuit(circuit)
    except Exception as e:
        exception = e
    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


def gen_ecAdd_testing_data():
    op = EccOpTag.Add

    normal = (
        EccOps(
            op,
            p=(1, 2),
            q=(1, 2),
            out=(
                0x030644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,
                0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,
            ),
        ),
        True,
    )
    # p is not on the curve
    invalid_p = (
        EccOps(
            op,
            p=(2, 3),
            q=(1, 2),
            out=(0, 0),
        ),
        True,
    )
    incorrect_out = (
        EccOps(
            op,
            p=(1, 2),
            q=(1, 2),
            out=(
                0x030644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD0,
                0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,
            ),
        ),
        False,
    )
    # q = -p
    # py_ecc doesn't support this case, it returns (0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45, 1)
    # p_plus_neg_p = (
    #     EccOps(
    #         op,
    #         p=(1, 2),
    #         q=(1, 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45),
    #         out=(0, 0),
    #     ),
    #     True,
    # )
    return [normal, invalid_p, incorrect_out]


TESTING_DATA = gen_ecAdd_testing_data()


@pytest.mark.parametrize(
    "ecc_ops, success",
    TESTING_DATA,
)
def test_ecc_add(ecc_ops: EccOps, success: bool):
    MAX_ECADD_OPS = 5
    MAX_ECMUL_OPS = 0
    MAX_ECPAIRING_OPS = 0

    circuit = EccCircuit(MAX_ECADD_OPS, MAX_ECMUL_OPS, MAX_ECPAIRING_OPS)
    ecc_ops = gen_ecAdd_testing_data()
    for ec_op, success in ecc_ops:
        row = EccCircuitRow.assign(
            ec_op.op_type,
            (Word(ec_op.p[0]), Word(ec_op.p[1])),
            (Word(ec_op.q[0]), Word(ec_op.q[1])),
            (Word(ec_op.out[0]), Word(ec_op.out[1])),
        )
        circuit.add(row)
        verify(circuit, success)
