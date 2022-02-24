import traceback
from typing import Union, List
from eth_keys import keys
from eth_utils import keccak
import rlp
from zkevm_specs.tx import *
from zkevm_specs.util import rand_fp, FQ, RLC, U64

randomness = rand_fp()
r = randomness

def sign_tx(sk: keys.PrivateKey, tx: Transaction, chain_id: U64) -> Transaction:
    tx_msg = rlp.encode([tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, chain_id, 0, 0])
    tx_msg_hash = keccak(tx_msg)
    sig = sk.sign_msg_hash(tx_msg_hash)
    sig_v = sig.v + chain_id * 2 + 35
    sig_r = sig.r
    sig_s = sig.s
    return Transaction(tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, sig_v, sig_r, sig_s)

def verify(txs_or_rows: Union[List[Transaction], List[Row]], chain_id: U64, randomness: FQ, success: bool = True):
    rows = txs_or_rows
    if isinstance(txs_or_rows[0], Transaction):
        rows = txs2rows(txs_or_rows, chain_id, randomness)
    ok = True
    for (idx, row) in enumerate(rows):
        row_prev = rows[(idx - 1) % len(rows)]
        try:
            check_tx_row(row, row_prev, chain_id, randomness)
        except AssertionError as e:
            if success:
                traceback.print_exc()
            print(f"row[{(idx-1) % len(rows)}]: {row_prev}")
            print(f"row[{idx}]: {row}")
            ok = False
            break
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
    rows = tx2rows(0, tx, chain_id, r)
    # print('rows:')
    for row in rows:
        print(row)
        if row.tag == Tag.CallerAddress:
            assert addr == row.value.n.to_bytes(20, "big")

def test_check_tx_row():
    chain_id = 1337
    sks = [keys.PrivateKey(bytes([byte+1]) * 32) for byte in range(16)]

    txs: List[Transaction] = []
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

    rows = txs2rows(txs, chain_id, r)
    verify(rows, chain_id, r)
