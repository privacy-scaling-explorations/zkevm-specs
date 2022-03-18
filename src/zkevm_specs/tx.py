from .encoding import U8, is_circuit_code
from typing import NamedTuple, Tuple, List, Sequence, Set
from .util import FQ, RLC, U160, U256, U64
from enum import IntEnum, auto
from eth_keys import KeyAPI # type: ignore
import rlp # type: ignore
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
    CalleeAddress = 7
    IsCreate = 8
    Value = 9
    CallDataLength = 10
    TxSignHash = 11
    CallData = 12
    Pad = 13

class Row():
    """
    Tx circuit row
    """

    tx_id: FQ
    tag: FQ
    index: FQ
    value: FQ

    def __init__(self, tx_id: FQ, tag: FQ, index: FQ, value: FQ):
        self.tx_id = tx_id
        self.tag = tag
        self.index = index
        self.value = value


class KeccakTable():
    # The columns are: (is_enabled, input_rlc, input_len, output_rlc)
    table: Set[Tuple[FQ, FQ, FQ, FQ]]

    def __init__(self):
        self.table = set()
        self.table.add((FQ(0), FQ(0), FQ(0), FQ(0))) # Add all 0s row

    def add(self, input: bytes, randomness: FQ):
        output = keccak(input)
        self.table.add((FQ(1), RLC(input, randomness).value, FQ(len(input)), RLC(output, randomness).value))

    def lookup(self, is_enabled: FQ, input_rlc: FQ, input_len: FQ, output_rlc: FQ, assert_msg: str):
        assert (is_enabled, input_rlc, input_len, output_rlc) in self.table, \
            f'{assert_msg}: {(is_enabled, input_rlc, input_len, output_rlc)} '+ \
            'not found in the lookup table'

class WrongFieldInteger():
    """
    Wrong Field arithmetic Integer, representing the implementation at
    https://github.com/appliedzkp/halo2wrong/blob/master/integer/src/integer.rs
    """
    limbs: bytes # Little-Endian bytes

    def __init__(self, value: int) -> None:
        self.limbs = value.to_bytes(32, "little")

class Secp256k1BaseField(WrongFieldInteger):
    """
    Secp256k1 Base Field.
    """
    def __init__(self, value: int) -> None:
        WrongFieldInteger.__init__(self, value)

class Secp256k1ScalarField(WrongFieldInteger):
    """
    Secp256k1 Scalar Field.
    """
    def __init__(self, value: int) -> None:
        WrongFieldInteger.__init__(self, value)

class ECDSAVerifyChip():
    """
    ECDSA Signature Verification Chip.  This represents an ECDSA signature
    verification Chip as implemented in
    https://github.com/appliedzkp/halo2wrong/blob/master/ecdsa/src/ecdsa.rs
    """

    signature: Tuple[Secp256k1ScalarField, Secp256k1ScalarField]
    pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField]
    msg_hash: Secp256k1ScalarField

    def __init__(
        self,
        signature: Tuple[Secp256k1ScalarField, Secp256k1ScalarField],
        pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField],
        msg_hash: Secp256k1ScalarField,
    ) -> None:
        self.signature = signature
        self.pub_key = pub_key
        self.msg_hash = msg_hash

    @classmethod
    def assign(cls, signature: KeyAPI.Signature, pub_key: KeyAPI.PublicKey, msg_hash: bytes):
        self_signature = (Secp256k1ScalarField(signature.r), Secp256k1ScalarField(signature.s))
        pub_key_bytes = pub_key.to_bytes()
        pub_key_bytes_x, pub_key_bytes_y = pub_key_bytes[:32], pub_key_bytes[32:]
        pub_key_x = int.from_bytes(pub_key_bytes_x, "big")
        pub_key_y = int.from_bytes(pub_key_bytes_y, "big")
        self_pub_key = (Secp256k1BaseField(pub_key_x), Secp256k1BaseField(pub_key_y))
        self_msg_hash = Secp256k1ScalarField(int.from_bytes(msg_hash, "big"))
        return cls(self_signature, self_pub_key, self_msg_hash)

    def verify(self, is_enabled: FQ, assert_msg: str):
        msg_hash = bytes(reversed(self.msg_hash.limbs))
        sig_r = int.from_bytes(self.signature[0].limbs, "little")
        sig_s = int.from_bytes(self.signature[1].limbs, "little")
        signature = KeyAPI.Signature(vrs=[0, sig_r, sig_s])
        public_key = KeyAPI.PublicKey(
            bytes(reversed(self.pub_key[0].limbs)) + bytes(reversed(self.pub_key[1].limbs))
        )
        if is_enabled == 1:
            assert KeyAPI().ecdsa_verify(msg_hash, signature, public_key), \
                f'{assert_msg}: ecdsa_verify failed'


class SignVerifyGadget():
    """
    Auxiliary Gadget to verify a that a message hash is signed by the public
    key corresponding to an Ethereum Address.
    """

    pub_key_hash: RLC
    address: FQ
    msg_hash_rlc: FQ # Set to 0 to disable verification check
    ecdsa_chip: ECDSAVerifyChip

    def __init__(
        self,
        pub_key_hash: RLC,
        address: FQ,
        msg_hash_rlc: FQ,
        ecdsa_chip: ECDSAVerifyChip,
    ) -> None:
        self.pub_key_hash = pub_key_hash
        self.address = address
        self.msg_hash_rlc = msg_hash_rlc
        self.ecdsa_chip = ecdsa_chip

    @classmethod
    def assign(cls, signature: KeyAPI.Signature, pub_key: KeyAPI.PublicKey, msg_hash: bytes, randomness: FQ):
        pub_key_hash = keccak(pub_key.to_bytes())
        self_pub_key_hash = RLC(pub_key_hash, randomness)
        self_address = FQ(int.from_bytes(pub_key_hash[-20:], "big"))
        self_msg_hash_rlc = RLC(int.from_bytes(msg_hash, "big"), randomness).value
        self_ecdsa_chip = ECDSAVerifyChip.assign(signature, pub_key, msg_hash)
        return cls(self_pub_key_hash, self_address, self_msg_hash_rlc, self_ecdsa_chip)

    def verify(self, keccak_table: KeccakTable, randomness: FQ, assert_msg: str):
        is_enabled = FQ(1 - (self.msg_hash_rlc == 0)) # 1 - is_zero(self.msg_hash_rlc)

        # 0. Verify that the first 20 bytes of the pub_key_hash equal the address
        addr_expr = FQ.linear_combine(list(reversed(self.pub_key_hash.le_bytes[-20:])), FQ(2**8))
        assert addr_expr == self.address, \
            f'{assert_msg}: {hex(addr_expr.n)} != {hex(self.address.n)}'

        # 1. Verify that keccak(pub_key_bytes) = pub_key_hash by keccak table
        # lookup, where pub_key_bytes is built from the pub_key in the
        # ecdsa_chip
        pub_key_bytes = bytes(reversed(self.ecdsa_chip.pub_key[0].limbs)) + \
                bytes(reversed(self.ecdsa_chip.pub_key[1].limbs))
        keccak_table.lookup(is_enabled, RLC(pub_key_bytes, randomness).value, FQ(64) * is_enabled,
                self.pub_key_hash.value, assert_msg)

        # 2. Verify that the signed message in the ecdsa_chip with RLC encoding
        # corresponds to msg_hash_rlc
        msg_hash_rlc_expr = FQ.linear_combine(self.ecdsa_chip.msg_hash.limbs, randomness)
        assert msg_hash_rlc_expr == self.msg_hash_rlc, \
            f'{assert_msg}: {hex(msg_hash_rlc_expr.n)} != {hex(self.msg_hash_rlc.n)}'

        # Verify the ECDSA signature
        self.ecdsa_chip.verify(is_enabled, assert_msg)

@is_circuit_code
def verify_circuit(
        rows: List[Row],
        sign_verifications: List[SignVerifyGadget],
        keccak_table: KeccakTable,
        MAX_TXS: int,
        MAX_CALLDATA_BYTES: int,
        chain_id: U64,
        randomness: FQ) -> None:
    """
    Entry level circuit verification function
    """

    for tx_index in range(MAX_TXS):
        assert_msg = f"Constraints failed for tx_index = {tx_index}"
        tx_row_index = tx_index * Tag.TxSignHash
        caller_addr_index = tx_row_index + Tag.CallerAddress - 1
        tx_msg_hash_index = tx_row_index + Tag.TxSignHash - 1

        # SignVerifyGadget constraint verification.  Padding txs rows contain
        # 0 in all values.  The SignVerifyGadget skips the verification when
        # the msg_hash_rlc == 0.
        sign_verifications[tx_index].verify(keccak_table, randomness, assert_msg)

        # 0. Copy constraints using fixed offsets between the tx rows and the SignVerifyGadget
        assert rows[caller_addr_index].value == sign_verifications[tx_index].address, \
            f'{assert_msg}: {hex(rows[caller_addr_index].value.n)} != ' + \
            f'{hex(sign_verifications[tx_index].address.n)}'
        assert rows[tx_msg_hash_index].value == sign_verifications[tx_index].msg_hash_rlc, \
            f'{assert_msg}: {hex(rows[tx_msg_hash_index].value.n)} != ' + \
            f'{hex(sign_verifications[tx_index].msg_hash_rlc.n)}'

    # Remaining rows contain CallData.  Those rows don't have any circuit constraint.


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

def tx2witness(
        index: int,
        tx: Transaction,
        chain_id: U64,
        randomness: FQ,
        keccak_table: KeccakTable
    ) -> Tuple[List[Row], SignVerifyGadget]:
    """
    Generate the witness data for a single transaction: generate the tx table
    rows, insert the pub_key_bytes entry in the keccak_table and assign the
    SignVerifyGadget.
    """

    tx_msg = rlp.encode([tx.nonce, tx.gas_price, tx.gas, tx.to, tx.value, tx.data, chain_id, 0, 0])
    tx_msg_hash = keccak(tx_msg)

    sig_parity = tx.sig_v - 35 - chain_id * 2
    sig = KeyAPI.Signature(vrs=(sig_parity, tx.sig_r, tx.sig_s))

    pk = sig.recover_public_key_from_msg_hash(tx_msg_hash)
    pk_bytes = pk.to_bytes()
    keccak_table.add(pk_bytes, randomness)
    pk_hash = keccak(pk.to_bytes())
    addr = pk_hash[-20:]

    sign_verification = SignVerifyGadget.assign(sig, pk, tx_msg_hash, randomness)

    tx_id = FQ(index+1)
    rows: List[Row] = []
    rows.append(Row(tx_id, FQ(Tag.Nonce), FQ(0), FQ(tx.nonce)))
    rows.append(Row(tx_id, FQ(Tag.Gas), FQ(0), FQ(tx.gas)))
    rows.append(Row(tx_id, FQ(Tag.GasPrice), FQ(0), RLC(tx.gas_price, randomness).value))
    rows.append(Row(tx_id, FQ(Tag.GasTipCap), FQ(0), FQ(0)))
    rows.append(Row(tx_id, FQ(Tag.GasFeeCap), FQ(0), FQ(0)))
    rows.append(Row(tx_id, FQ(Tag.CallerAddress), FQ(0), FQ(int.from_bytes(addr, "big"))))
    rows.append(Row(tx_id, FQ(Tag.CalleeAddress), FQ(0), FQ(tx.to)))
    rows.append(Row(tx_id, FQ(Tag.IsCreate), FQ(0), FQ(1) if tx.to == FQ(0) else FQ(0)))
    rows.append(Row(tx_id, FQ(Tag.Value), FQ(0), RLC(tx.value, randomness).value))
    rows.append(Row(tx_id, FQ(Tag.CallDataLength), FQ(0), FQ(len(tx.data))))
    rows.append(Row(tx_id, FQ(Tag.TxSignHash), FQ(0), RLC(int.from_bytes(tx_msg_hash, "big"), randomness).value))
    for byte_index, byte in enumerate(tx.data):
        rows.append(Row(tx_id, FQ(Tag.CallData), FQ(byte_index), FQ(byte)))

    return (rows, sign_verification)

class Witness(NamedTuple):
    rows: List[Row] # Transaction table rows
    keccak_table: KeccakTable
    sign_verifications: List[SignVerifyGadget]

def txs2witness(txs: List[Transaction], chain_id: U64, MAX_TXS: int, MAX_CALLDATA_BYTES: int, randomness: FQ) -> Witness:
    """
    Generate the complete witness of the transactions for a fixed size circuit.
    """
    assert len(txs) <= MAX_TXS

    keccak_table = KeccakTable()
    sign_verifications: List[SignVerifyGadget] = []
    tx_fixed_rows: List[Row] = [] # Accumulate fixed rows of each tx
    tx_dyn_rows: List[Row] = [] # Accumulate CallData rows of each tx
    for index, tx in enumerate(txs):
        tx_rows, sign_verification = tx2witness(index, tx, chain_id, randomness, keccak_table)
        sign_verifications.append(sign_verification)
        for row in tx_rows:
            if row.tag == Tag.CallData:
                tx_dyn_rows.append(row)
            else:
                tx_fixed_rows.append(row)

    assert len(tx_dyn_rows) <= MAX_CALLDATA_BYTES

    # Fill all the rows in the fixed region to reach MAX_TXS * Tag.TxSignHash
    # with pad rows.  And fill all the rows in the dynamic region to reach
    # MAX_CALLDATA_BYTES with pad rows.
    rows = tx_fixed_rows + \
        [Row(FQ(0), FQ(Tag.Pad), FQ(0), FQ(0))] * (MAX_TXS - len(txs)) * Tag.TxSignHash + \
        tx_dyn_rows + \
        [Row(FQ(0), FQ(Tag.Pad), FQ(0), FQ(0))] * (MAX_CALLDATA_BYTES - len(tx_dyn_rows))

    empty_ecdsa_chip = ECDSAVerifyChip(
        (Secp256k1ScalarField(0), Secp256k1ScalarField(0)),
        (Secp256k1BaseField(0), Secp256k1BaseField(0)),
        Secp256k1ScalarField(0),
    )
    empty_sign_verification = SignVerifyGadget(
        RLC(0, randomness),
        FQ(0),
        FQ(0),
        empty_ecdsa_chip,
    )
    # Fill the rest of sign_verifications with the witnessess assigned to 0 to
    # disable the verification.
    sign_verifications = sign_verifications + \
            [empty_sign_verification] * (MAX_TXS - len(txs))

    return Witness(rows, keccak_table, sign_verifications)
