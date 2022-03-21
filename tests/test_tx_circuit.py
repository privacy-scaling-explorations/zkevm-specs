import traceback
from typing import Union, List
from eth_keys import keys
from eth_utils import keccak
import rlp
from zkevm_specs.tx import *
from zkevm_specs.util import rand_fq, FQ, RLC, U64

randomness = rand_fq()
r = randomness


def sign_tx(sk: keys.PrivateKey, tx: Transaction, chain_id: U64) -> Transaction:
    """
    Return a copy of the transaction signed by sk
    """
    tx_sign_data = rlp.encode(
        [tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, chain_id, 0, 0]
    )
    tx_sign_hash = keccak(tx_sign_data)
    sig = sk.sign_msg_hash(tx_sign_hash)
    sig_v = sig.v + chain_id * 2 + 35
    sig_r = sig.r
    sig_s = sig.s
    return Transaction(
        tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, sig_v, sig_r, sig_s
    )


def verify(
    txs_or_witness: Union[List[Transaction], Witness],
    MAX_TXS: int,
    MAX_CALLDATA_BYTES: int,
    chain_id: U64,
    randomness: FQ,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness (or the witness calculated
    from the transactions).  If `success` is False, expect the verification to
    fail.
    """
    witness = txs_or_witness
    if isinstance(txs_or_witness, Witness):
        pass
    else:
        witness = txs2witness(txs_or_witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES, randomness)
    assert len(witness.rows) == MAX_TXS * Tag.TxSignHash + MAX_CALLDATA_BYTES
    assert len(witness.sign_verifications) == MAX_TXS
    ok = True
    if success:
        verify_circuit(
            witness.rows,
            witness.sign_verifications,
            witness.keccak_table,
            MAX_TXS,
            MAX_CALLDATA_BYTES,
            randomness,
        )
    else:
        try:
            verify_circuit(
                witness.rows,
                witness.sign_verifications,
                witness.keccak_table,
                MAX_TXS,
                MAX_CALLDATA_BYTES,
                randomness,
            )
        except AssertionError as e:
            ok = False
    assert ok == success


def test_ecdsa_verify_chip():
    sk = keys.PrivateKey(b"\x02" * 32)
    pk = sk.public_key
    msg_hash = b"\xae" * 32
    sig = sk.sign_msg_hash(msg_hash)

    ecdsa_chip = ECDSAVerifyChip.assign(sig, pk, msg_hash)
    ecdsa_chip.verify(is_enabled=FQ(1), assert_msg="ecdsa verification failed")


def test_tx2witness():
    sk = keys.PrivateKey(b"\x01" * 32)
    pk = sk.public_key
    addr = pk.to_canonical_address()

    chain_id = 23

    nonce = 543
    gas_price = 1234
    gas = 987654
    to = 0x12345678
    value = 0x1029384756
    data = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99])

    tx = Transaction(nonce, gas_price, gas, to, value, data, 0, 0, 0)
    tx = sign_tx(sk, tx, chain_id)
    keccak_table = KeccakTable()
    rows, sign_verification = tx2witness(0, tx, chain_id, r, keccak_table)
    for row in rows:
        print(row)
        if row.tag == Tag.CallerAddress:
            assert addr == row.value.n.to_bytes(20, "big")


def gen_tx(i: int, sk: keys.PrivateKey, to: int, chain_id) -> Transaction:
    nonce = 300 + i
    gas_price = 1000 + i * 2
    gas = 20000 + i * 3
    value = 0x30000 + i * 4
    data = bytes([i] * i)

    tx = Transaction(nonce, gas_price, gas, to, value, data, 0, 0, 0)
    tx = sign_tx(sk, tx, chain_id)
    return tx


def test_verify():
    MAX_TXS = 20
    MAX_CALLDATA_BYTES = 300
    NUM_TXS = 16
    chain_id = 1337
    sks = [keys.PrivateKey(bytes([byte + 1]) * 32) for byte in range(NUM_TXS)]

    txs: List[Transaction] = []
    keccak_table = KeccakTable()
    for i, sk in enumerate(sks):
        to = int.from_bytes(sks[(i + 1) % len(sks)].public_key.to_canonical_address(), "big")
        tx = gen_tx(i, sk, to, chain_id)
        txs.append(tx)

    witness = txs2witness(txs, chain_id, MAX_TXS, MAX_CALLDATA_BYTES, r)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r)


def gen_valid_witness() -> Tuple[Witness, U64, int, int]:
    MAX_TXS = 5
    MAX_CALLDATA_BYTES = 16
    NUM_TXS = 3
    chain_id = 1337

    sks = [keys.PrivateKey(bytes([byte + 1]) * 32) for byte in range(NUM_TXS)]

    txs: List[Transaction] = []
    keccak_table = KeccakTable()
    for i, sk in enumerate(sks):
        to = int.from_bytes(sks[(i + 1) % len(sks)].public_key.to_canonical_address(), "big")
        tx = gen_tx(i, sk, to, chain_id)
        txs.append(tx)

    witness = txs2witness(txs, chain_id, MAX_TXS, MAX_CALLDATA_BYTES, r)
    return witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES


def test_bad_keccak():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    # Set empty keccak lookup table
    witness = Witness(witness.rows, KeccakTable(), witness.sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


def test_bad_signature():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    sign_verifications = witness.sign_verifications
    sign_verifications[0].ecdsa_chip.signature = (Secp256k1ScalarField(1), Secp256k1ScalarField(2))
    witness = Witness(witness.rows, witness.keccak_table, sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


def test_bad_address():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    sign_verifications = witness.sign_verifications
    sign_verifications[0].address = FQ(1234)
    witness = Witness(witness.rows, witness.keccak_table, sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


def test_bad_msg_hash():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    sign_verifications = witness.sign_verifications
    sign_verifications[0].msg_hash_rlc = FQ(4567)
    witness = Witness(witness.rows, witness.keccak_table, sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


def test_bad_addr_copy():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    rows = witness.rows
    row_addr_offset = 0 * Tag.TxSignHash + Tag.CallerAddress - 1
    rows[row_addr_offset].value = FQ(1213)
    witness = Witness(rows, witness.keccak_table, witness.sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


def test_bad_sign_hash_copy():
    witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES = gen_valid_witness()
    rows = witness.rows
    row_hash_offset = 0 * Tag.TxSignHash + Tag.TxSignHash - 1
    rows[row_hash_offset].value = FQ(2324)
    witness = Witness(rows, witness.keccak_table, witness.sign_verifications)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r, success=False)
