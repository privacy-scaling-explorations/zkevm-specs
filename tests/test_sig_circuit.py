from typing import NamedTuple, List
from eth_keys import keys  # type: ignore
from eth_utils import keccak
from zkevm_specs.sig_circuit import *
from zkevm_specs.util import FQ
from common import rand_fq
from zkevm_specs.util import (
    FQ,
    Word,
    U160,
    U256,
)

keccak_randomness = rand_fq()
r = keccak_randomness


class SignedData(NamedTuple):
    msg_hash: bytes
    sig_v: U256
    sig_r: U256
    sig_s: U256
    addr: U160
    is_valid: bool


def sign_msg(sk: keys.PrivateKey, msg: bytes, valid: bool = True) -> SignedData:
    """
    Return a copy of the signed data
    """

    msg_hash = keccak(msg)
    sig = sk.sign_msg_hash(msg_hash)
    sig_v = sig.v
    sig_r = sig.r if valid else U256(1)
    sig_s = sig.s if valid else U256(1)
    return SignedData(msg_hash, sig_v, sig_r, sig_s, int(sk.public_key.to_address(), 16), valid)


def signedData2witness(
    signed_data: List[SignedData],
    keccak_randomness: FQ,
) -> Witness:
    """
    Generate the complete witness of a list of signed data.
    """

    rows: List[Row] = []
    keccak_table = KeccakTable()
    for i, data in enumerate(signed_data):
        sig = KeyAPI.Signature(vrs=(data.sig_v, data.sig_r, data.sig_s))
        pk = sig.recover_public_key_from_msg_hash(data.msg_hash)
        ecdsa_chip = ECDSAVerifyChip.assign(sig, pk, data.msg_hash)

        pk_bytes = pk.to_bytes()
        keccak_table.add(pk_bytes, keccak_randomness)
        pk_hash = keccak(pk_bytes)
        rows.append(
            Row(
                pk_hash,
                FQ(data.addr),
                Word(data.msg_hash),
                ecdsa_chip,
            )
        )

    return Witness(rows, keccak_table)


def gen_witness(num: int = 10, valid: bool = True) -> Witness:
    sks = [keys.PrivateKey(bytes([byte + 1]) * 32) for byte in range(num)]

    list: List[SignedData] = []
    for sk in sks:
        signed_msg = sign_msg(sk, bytes("Message", "utf-8"), valid)
        list.append(signed_msg)

    witness = signedData2witness(list, r)
    return witness


def verify(
    witness: Witness,
    keccak_randomness: FQ,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness (or the witness calculated
    from the transactions).  If `success` is False, expect the verification to
    fail.
    """

    exception = None
    try:
        verify_circuit(
            witness,
            keccak_randomness,
        )
    except AssertionError as e:
        exception = e

    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


def test_ecdsa_verify_chip():
    sk = keys.PrivateKey(b"\x02" * 32)
    pk = sk.public_key
    msg_hash = b"\xae" * 32
    sig = sk.sign_msg_hash(msg_hash)

    ecdsa_chip = ECDSAVerifyChip.assign(sig, pk, msg_hash)
    assert ecdsa_chip.verify() == True


def test_sig_verify():
    witness = gen_witness()
    verify(witness, r)


def test_sig_bad_keccak():
    witness = gen_witness()
    # Set empty keccak lookup table
    witness = Witness(witness.rows, KeccakTable())
    verify(witness, r, success=False)


def test_sig_bad_signature():
    witness = gen_witness(10, False)
    verify(witness, r, success=False)


def test_sig_bad_msg_hash():
    witness = gen_witness(1)
    witness.rows[0].msg_hash = Word(1)
    verify(witness, r, success=False)


def test_sig_bad_address():
    witness = gen_witness(1)
    witness.rows[0].recovered_addr = FQ(1)
    verify(witness, r, success=False)
