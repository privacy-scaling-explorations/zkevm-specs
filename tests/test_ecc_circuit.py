import pytest
from common import rand_fq
from zkevm_specs.ecc_circuit import (
    EcAdd,
    EcPairing,
    EcMul,
    verify_circuit,
    EccCircuit,
)
from zkevm_specs.util import FQ

randomness_keccak = rand_fq()


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
        verify_circuit(circuit, randomness_keccak)
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


#
# ec scalar multiplication
#

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


#
# ec pairing
#
def gen_ecPairing_testing_data():
    normal = (
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    1,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=1,
        ),
        True,
    )
    infinity_q = (
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
            ],
            g2_pts=[(0, 0, 0, 0)],
            out=1,
        ),
        True,
    )
    infinity_p = (
        EcPairing(
            g1_pts=[(0, 0)],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
            ],
            out=1,
        ),
        True,
    )
    infinity_pnq = (
        EcPairing(
            g1_pts=[(0, 0)],
            g2_pts=[(0, 0, 0, 0)],
            out=1,
        ),
        True,
    )
    # p is not on the curve
    invalid_p = (
        EcPairing(
            g1_pts=[
                (
                    2,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    1,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=0,
        ),
        False,
    )
    # q is not on the curve
    invalid_q = (
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    1,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,
                ),
            ],
            g2_pts=[
                (
                    1,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=0,
        ),
        False,
    )
    # p and q are valid points but p[0] == p[1] which causes e(p[0], g2[0]) != e(p[0], g2[1])
    failed_pairing_with_valid_pnq = (
        EcPairing(
            g1_pts=[
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
                (
                    0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                    0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
                ),
            ],
            g2_pts=[
                (
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
                (
                    0x1971FF0471B09FA93CAAF13CBF443C1AEDE09CC4328F5A62AAD45F40EC133EB4,
                    0x091058A3141822985733CBDDDFED0FD8D6C104E9E9EFF40BF5ABFEF9AB163BC7,
                    0x2A23AF9A5CE2BA2796C1F4E453A370EB0AF8C212D9DC9ACD8FC02C2E907BAEA2,
                    0x23A8EB0B0996252CB548A4487DA97B02422EBC0E834613F954DE6C7E0AFDC1FC,
                ),
            ],
            out=1,
        ),
        False,
    )
    return [
        normal,
        infinity_p,
        infinity_q,
        infinity_pnq,
        invalid_p,
        invalid_q,
        failed_pairing_with_valid_pnq,
    ]


TESTING_DATA = gen_ecPairing_testing_data()


@pytest.mark.parametrize(
    "ecc_ops, success",
    TESTING_DATA,
)
def test_ecc_pairing(ecc_ops: EcPairing, success: bool):
    MAX_ECADD_OPS = 0
    MAX_ECMUL_OPS = 0
    MAX_ECPAIRING_OPS = 1

    circuit = EccCircuit(MAX_ECADD_OPS, MAX_ECMUL_OPS, MAX_ECPAIRING_OPS)
    ecc_ops = gen_ecPairing_testing_data()
    for op, success in ecc_ops:
        circuit.append_pairing(op)
        verify(circuit, success)
