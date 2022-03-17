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
    tx_msg = rlp.encode([tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, chain_id, 0, 0])
    tx_msg_hash = keccak(tx_msg)
    sig = sk.sign_msg_hash(tx_msg_hash)
    sig_v = sig.v + chain_id * 2 + 35
    sig_r = sig.r
    sig_s = sig.s
    return Transaction(tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, sig_v, sig_r, sig_s)

def verify(
        txs_or_witness: Union[List[Transaction], Witness],
        MAX_TXS: int,
        MAX_CALLDATA_BYTES: int,
        chain_id: U64,
        randomness: FQ,
        success: bool = True):
    witness = txs_or_witness
    if isinstance(txs_or_witness, Witness):
        pass
    else:
        witness = txs2witness(txs_or_witness, chain_id, MAX_TXS, MAX_CALLDATA_BYTES, randomness)
    assert len(witness.rows) == MAX_TXS * Tag.TxSignHash + MAX_CALLDATA_BYTES
    assert len(witness.sign_verifications) == MAX_TXS
    ok = True
    verify_circuit(
            witness.rows,
            witness.sign_verifications,
            witness.keccak_table,
            MAX_TXS,
            MAX_CALLDATA_BYTES,
            chain_id,
            randomness
    )
    # try:
    #     verify_circuit(
    #             witness.rows,
    #             witness.sign_verifications,
    #             witness.keccak_table,
    #             MAX_TXS,
    #             MAX_CALLDATA_BYTES,
    #             chain_id,
    #             randomness
    #     )
    # except AssertionError as e:
    #     if success:
    #         traceback.print_exc()
    #     ok = False
    assert ok == success


def test_tx2rows():
    sk = keys.PrivateKey(b'\x01' * 32)
    pk = sk.public_key
    addr = pk.to_canonical_address()
    # print(f'addr: 0x{addr.hex()}')

    chain_id = 23

    nonce = 543
    gas_price = 1234
    gas = 987654
    to = 0x12345678
    value = 0x1029384756
    data = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99])

    tx = Transaction(nonce, gas_price, gas, to, value, data, 0, 0, 0)
    tx = sign_tx(sk, tx, chain_id)
    # print(f'tx: {tx}')
    keccak_table = KeccakTable()
    rows, sign_verification = tx2witness(0, tx, chain_id, r, keccak_table)
    # print('rows:')
    for row in rows:
        print(row)
        if row.tag == Tag.CallerAddress:
            assert addr == row.value.n.to_bytes(20, "big")

def test_check_tx_row():
    MAX_TXS = 20
    MAX_CALLDATA_BYTES = 300
    NUM_TXS = 1
    chain_id = 1337
    sks = [keys.PrivateKey(bytes([byte+1]) * 32) for byte in range(NUM_TXS)]

    txs: List[Transaction] = []
    keccak_table = KeccakTable()
    for i, sk in enumerate(sks):
        nonce = 300 + i
        gas_price = 1000 + i * 2
        gas = 20000 + i * 3
        to = int.from_bytes(sks[(i+1) % len(sks)].public_key.to_canonical_address(), "big")
        value = 0x30000 + i * 4
        data = bytes([i] * i)

        tx = Transaction(nonce, gas_price, gas, to, value, data, 0, 0, 0)
        tx = sign_tx(sk, tx, chain_id)
        txs.append(tx)
    print(f'addr: {sks[0].public_key.to_canonical_address().hex()}')
    print(f'tx: {tx}')

    witness = txs2witness(txs, chain_id, MAX_TXS, MAX_CALLDATA_BYTES, r)
    verify(witness, MAX_TXS, MAX_CALLDATA_BYTES, chain_id, r)

def test_ecdsa_verify_chip():
    sk = keys.PrivateKey(b'\x02' * 32)
    pk = sk.public_key
    msg_hash = b'\xae' * 32
    sig = sk.sign_msg_hash(msg_hash)

    ecdsa_chip = ECDSAVerifyChip.assign(sig, pk, msg_hash)
    ecdsa_chip.verify(is_enabled=FQ(1), assert_msg="ecdsa verification failed")
