from .encoding import U8, is_circuit_code
from typing import NamedTuple, Tuple, List, Sequence
from .util import FQ, RLC, U160, U256, U64
from enum import IntEnum, auto
from eth_keys import KeyAPI
import rlp
from eth_utils import keccak

class Tag(IntEnum):
    """
    Tag used as second key in the Tx Circuit Rows to "select" the transaction field target.
    Can be encoded in 4 bits.
    """

    Nonce = 1
    Gas = 2
    GasPrice = 3
    GasTipCap = 4
    GasFeeCap = 5
    CallerAddress = 6
    TxSignHash = 7
    CalleeAddress = 8
    IsCreate = 9
    Value = 10
    CallDataLength = 11
    CallData = 12
    Pad = 13

class Row(NamedTuple):
    """
    Tx circuit row
    """

    tx_id: FQ
    tag: FQ
    index: FQ
    value: FQ

@is_circuit_code
def check_tx_row(row: Row, row_prev: Row, chain_id: U64, randomness: FQ):

    # This constraint is enabled at fixed offsets `(int(Tag.TxSignHash)-1) * k`
    # where `k` is between 1 and `MAX_TXS`.
    if row.tag == Tag.TxSignHash:
        tx_msg_hash = row.value
        address = row_prev.value

class WrongFieldInteger():
    limbs: bytes # Little-Endian bytes

    def __init__(self, value: int) -> None:
        self.limbs = value.to_bytes(32, "little")

class ECDSAVerifyGadget(NamedTuple):
    """
    ECDSA Signature Verification Gadget
    """

    signature: [WrongFieldInteger, WrongFieldInteger]
    pub_key: [WrongFieldInteger, WrongFieldInteger]
    msg_hash: WrongFieldInteger

    def __init__(self, signature: KeyAPI.Signature, pub_key: KeyAPI.PublicKey, msg_hash: bytes) -> None:
        self.signature = 
        self.pub_key =
        self.msg_hash = 

    def verify(self):
        msg_hash = self.msg_hash.limbs
        signature = bytes([0]) + self.signature[0].limbs + self.signature[1].limbs
        public_key = self.pub_key[0].limbs + self.pub_key[1].limbs
        assert KeyAPI.ecdsa_verify(msg_hash, signature, public_key)

class Transaction(NamedTuple):
    """
    Ethereum Transaction
    """

    nonce: U64
    gas_price: U256
    gas: U64
    to: U160
    value: U256
    data: bytes
    sig_v: U64
    sig_r: U256
    sig_s: U256

def tx2rows(index: int, tx: Transaction, chain_id: U64, randomness: FQ) -> List[Row]:

    tx_msg = rlp.encode([tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, chain_id, 0, 0])
    tx_msg_hash = keccak(tx_msg)

    sig_parity = tx.sig_v - 35 - chain_id * 2
    sig = KeyAPI.Signature(vrs=(sig_parity, tx.sig_r, tx.sig_s))

    pk = sig.recover_public_key_from_msg_hash(tx_msg_hash)
    addr = keccak(pk.to_bytes())[-20:]

    tx_id = index+1
    rows: List[Row] = []
    rows.append(Row(tx_id, Tag.Nonce, 0, FQ(tx.nonce)))
    rows.append(Row(tx_id, Tag.Gas, 0, FQ(tx.gas)))
    rows.append(Row(tx_id, Tag.GasPrice, 0, RLC(tx.gas_price, randomness.n)))
    rows.append(Row(tx_id, Tag.GasTipCap, 0, 0))
    rows.append(Row(tx_id, Tag.GasFeeCap, 0, 0))
    rows.append(Row(tx_id, Tag.CallerAddress, 0, FQ(int.from_bytes(addr, "big"))))
    rows.append(Row(tx_id, Tag.CalleeAddress, 0, tx.to))
    rows.append(Row(tx_id, Tag.IsCreate, 0, 1 if tx.to == 0 else 0))
    rows.append(Row(tx_id, Tag.Value, 0, RLC(tx.value, randomness.n)))
    rows.append(Row(tx_id, Tag.CallDataLength, 0, len(tx.data)))
    for byte_index, byte in enumerate(tx.data):
        rows.append(Row(tx_id, Tag.CallData, byte_index, byte))
    rows.append(Row(tx_id, Tag.TxSignHash, 0, RLC(tx_msg_hash, randomness.n)))

    return rows

def txs2rows(txs: List[Transaction], chain_id: U64, randomness: FQ) -> List[Row]:
    tx_fixed_rows: List[Row] = [] # Accumulate fixed rows of each tx
    tx_dyn_rows: List[Row] = [] # Accumulate CallData rows of each tx
    for index, tx in enumerate(txs):
        tx_rows = tx2rows(index, tx, chain_id, randomness)
        for row in tx_rows:
            if row.tag == Tag.CallData:
                tx_dyn_rows.append(row)
            else:
                tx_fixed_rows.append(row)

    return tx_fixed_rows + tx_dyn_rows
