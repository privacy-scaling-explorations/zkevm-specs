import pytest
from zkevm_specs.ecc_circuit import (
    EcAdd,
    EcMul,
    verify_circuit,
    EccCircuit,
)
from zkevm_specs.util import FQ


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
    # q = -p
    p_plus_neg_p = (
        EcAdd(
            p=(1, 2),
            q=(1, 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45),
            out=(0, 0),
        ),
        True,
    )
    infinite_p = (
        EcAdd(
            p=(0, 0),
            q=(1, 2),
            out=(1, 2),
        ),
        True,
    )
    infinite_p_and_q = (
        EcAdd(
            p=(0, 0),
            q=(0, 0),
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
    return [normal, invalid_p, p_plus_neg_p, infinite_p, infinite_p_and_q, incorrect_out]


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


############################
# ec scalar multiplication #
############################

SCALAR_FIELD_MODULUS = FQ.field_modulus


def gen_ecMul_testing_data():
    normal = (
        EcMul(
            p=(1, 2),
            s=7,
            out=(
                0x17072B2ED3BB8D759A5325F477629386CB6FC6ECB801BD76983A6B86ABFFE078,
                0x168ADA6CD130DD52017BB54BFA19377AADFE3BF05D18F41B77809F7F60D4AF9E,
            ),
        ),
        True,
    )
    # scalar is larger than SCALAR_FIELD_MODULUS
    over_field_size_s = (
        EcMul(
            p=(1, 2),
            s=SCALAR_FIELD_MODULUS + 7,
            out=(
                0x17072B2ED3BB8D759A5325F477629386CB6FC6ECB801BD76983A6B86ABFFE078,
                0x168ADA6CD130DD52017BB54BFA19377AADFE3BF05D18F41B77809F7F60D4AF9E,
            ),
        ),
        True,
    )
    # s == SCALAR_FIELD_MODULUS - 1, i.e. P == -R
    negative_s = (
        EcMul(
            p=(1, 2),
            s=SCALAR_FIELD_MODULUS - 1,
            out=(
                1,
                0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
            ),
        ),
        True,
    )
    # zero scalar
    zero_s = (
        EcMul(
            p=(1, 2),
            s=0,
            out=(0, 0),
        ),
        True,
    )
    # p is a infinite point
    infinite_p = (
        EcMul(
            p=(0, 0),
            s=7,
            out=(0, 0),
        ),
        True,
    )
    # p is not on the curve
    invalid_p = (
        EcMul(
            p=(1, 3),
            s=7,
            out=(0, 0),
        ),
        True,
    )
    return [normal, over_field_size_s, negative_s, zero_s, infinite_p, invalid_p]


TESTING_DATA_MUL = gen_ecMul_testing_data()


@pytest.mark.parametrize(
    "ecc_ops, success",
    TESTING_DATA_MUL,
)
def test_ecc_mul(ecc_ops: EcMul, success: bool):
    MAX_ECADD_OPS = 0
    MAX_ECMUL_OPS = 1
    MAX_ECPAIRING_OPS = 0

    circuit = EccCircuit(MAX_ECADD_OPS, MAX_ECMUL_OPS, MAX_ECPAIRING_OPS)
    ecc_ops = gen_ecMul_testing_data()
    for op, success in ecc_ops:
        circuit.append_mul(op)
        verify(circuit, success)
