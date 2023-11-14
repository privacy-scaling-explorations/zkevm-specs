import pytest
from zkevm_specs.ecc_circuit import (
    EcAdd,
    verify_circuit,
    EccCircuit,
)


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
    normal = (
        EcAdd(
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
        EcAdd(
            p=(2, 3),
            q=(1, 2),
            out=(0, 0),
        ),
        True,
    )
    incorrect_out = (
        EcAdd(
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
    p_plus_neg_p = (
        EcAdd(
            p=(1, 2),
            q=(1, 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45),
            out=(0, 0),
        ),
        True,
    )
    return [normal, invalid_p, p_plus_neg_p, incorrect_out]


TESTING_DATA = gen_ecAdd_testing_data()


@pytest.mark.parametrize(
    "ecc_ops, success",
    TESTING_DATA,
)
def test_ecc_add(ecc_ops: EcAdd, success: bool):
    MAX_ECADD_OPS = 1
    MAX_ECMUL_OPS = 0
    MAX_ECPAIRING_OPS = 0

    circuit = EccCircuit(MAX_ECADD_OPS, MAX_ECMUL_OPS, MAX_ECPAIRING_OPS)
    ecc_ops = gen_ecAdd_testing_data()
    for op, success in ecc_ops:
        circuit.append_add(op)
        verify(circuit, success)
