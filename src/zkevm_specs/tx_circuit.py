from .encoding import is_circuit_code
from typing import NamedTuple, Tuple, List, Set, Union
from .util import (
    FQ,
    RLC,
    Word,
    WordOrValue,
    U160,
    U256,
    U64,
    linear_combine_bytes,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
)
from eth_keys import KeyAPI  # type: ignore
import rlp  # type: ignore
from eth_utils import keccak
from .evm_circuit import TxContextFieldTag as Tag


class Row:
    """
    Tx circuit row
    """

    tx_id: FQ
    tag: FQ
    index: FQ
    value: WordOrValue

    def __init__(self, tx_id: FQ, tag: FQ, index: FQ, value: Union[FQ, Word]):
        self.tx_id = tx_id
        self.tag = tag
        self.index = index
        self.value = WordOrValue(value)


class KeccakTable:
    # The columns are: (is_enabled, input_rlc, input_len, output)
    table: Set[Tuple[FQ, FQ, FQ, Word]]

    def __init__(self):
        self.table = set()
        self.table.add((FQ(0), FQ(0), FQ(0), Word(0)))  # Add all 0s row

    def add(self, input: bytes, keccak_randomness: FQ):
        output = keccak(input)
        self.table.add(
            (
                FQ(1),
                RLC(bytes(reversed(input)), keccak_randomness, n_bytes=64).expr(),
                FQ(len(input)),
                Word(output),
            )
        )

    def lookup(self, is_enabled: FQ, input_rlc: FQ, input_len: FQ, output: Word, assert_msg: str):
        assert (is_enabled, input_rlc, input_len, output) in self.table, (
            f"{assert_msg}: {(is_enabled, input_rlc, input_len, output)} "
            + "not found in the lookup table"
        )


class WrongFieldInteger:
    """
    Wrong Field arithmetic Integer, representing the implementation at
    https://github.com/privacy-scaling-explorations/halo2wrong/blob/master/integer/src/integer.rs
    """

    limbs: Tuple[FQ, FQ, FQ, FQ]  # Little-Endian limbs of [72, 72, 72, 40] bits
    le_bytes: bytes  # Little-Endian bytes

    def __init__(self, value: int) -> None:
        mask = (1 << 72) - 1
        l0 = (value >> 0 * 72) & mask
        l1 = (value >> 1 * 72) & mask
        l2 = (value >> 2 * 72) & mask
        l3 = (value >> 3 * 72) & mask
        self.limbs = (FQ(l0), FQ(l1), FQ(l2), FQ(l3))
        self.le_bytes = value.to_bytes(32, "little")

    def to_le_bytes(self) -> bytes:
        (l0, l1, l2, l3) = self.limbs
        val = l0.n + (l1.n << 1 * 72) + (l2.n << 2 * 72) + (l3.n << 3 * 72)
        return val.to_bytes(32, "little")


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


class ECDSAVerifyChip:
    """
    ECDSA Signature Verification Chip.  This represents an ECDSA signature
    verification Chip as implemented in
    https://github.com/privacy-scaling-explorations/halo2wrong/blob/master/ecdsa/src/ecdsa.rs
    """

    signature: Tuple[Secp256k1ScalarField, Secp256k1ScalarField]
    pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField]
    pub_key_x_bytes: bytes
    pub_key_y_bytes: bytes
    msg_hash: Secp256k1ScalarField
    msg_hash_bytes: bytes

    def __init__(
        self,
        signature: Tuple[Secp256k1ScalarField, Secp256k1ScalarField],
        pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField],
        msg_hash: Secp256k1ScalarField,
    ) -> None:
        self.signature = signature
        self.pub_key = pub_key
        self.msg_hash = msg_hash
        self.pub_key_x_bytes = pub_key[0].to_le_bytes()
        self.pub_key_y_bytes = pub_key[1].to_le_bytes()
        self.msg_hash_bytes = msg_hash.to_le_bytes()
        # NOTE: The circuit must constrain that all elements in the `*_bytes`
        # parameters  are in range 0..255 and that they represent the same
        # value as their corresponding WrongFieldInteger limbs.

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

    def verify(self, assert_msg: str):
        msg_hash = bytes(reversed(self.msg_hash.to_le_bytes()))
        sig_r = int.from_bytes(self.signature[0].to_le_bytes(), "little")
        sig_s = int.from_bytes(self.signature[1].to_le_bytes(), "little")
        signature = KeyAPI.Signature(vrs=[0, sig_r, sig_s])
        public_key = KeyAPI.PublicKey(
            bytes(reversed(self.pub_key[0].to_le_bytes()))
            + bytes(reversed(self.pub_key[1].to_le_bytes()))
        )
        assert KeyAPI().ecdsa_verify(
            msg_hash, signature, public_key
        ), f"{assert_msg}: ecdsa_verify failed"


class SignVerifyChip:
    """
    Auxiliary Chip to verify a that a message hash is signed by the public
    key corresponding to an Ethereum Address.
    """

    pub_key_hash: bytes
    address: FQ  # Set to 0 to disable verification check
    msg_hash: Word
    ecdsa_chip: ECDSAVerifyChip
    pub_key_x_bytes: bytes
    pub_key_y_bytes: bytes
    msg_hash_bytes: bytes

    def __init__(
        self,
        pub_key_hash: bytes,
        address: FQ,
        msg_hash: Word,
        ecdsa_chip: ECDSAVerifyChip,
    ) -> None:
        self.pub_key_hash = pub_key_hash
        self.address = address
        self.msg_hash = msg_hash
        self.ecdsa_chip = ecdsa_chip
        self.pub_key_x_bytes = ecdsa_chip.pub_key_x_bytes
        self.pub_key_y_bytes = ecdsa_chip.pub_key_y_bytes
        self.msg_hash_bytes = ecdsa_chip.msg_hash_bytes

    @classmethod
    def assign(
        cls,
        signature: KeyAPI.Signature,
        pub_key: KeyAPI.PublicKey,
        msg_hash: bytes,
        keccak_randomness: FQ,
    ):
        pub_key_hash = keccak(pub_key.to_bytes())
        self_pub_key_hash = pub_key_hash
        self_address = FQ(int.from_bytes(pub_key_hash[-20:], "big"))
        self_msg_hash = Word(int.from_bytes(msg_hash, "big"))
        self_ecdsa_chip = ECDSAVerifyChip.assign(signature, pub_key, msg_hash)
        return cls(self_pub_key_hash, self_address, self_msg_hash, self_ecdsa_chip)

    def verify(self, keccak_table: KeccakTable, keccak_randomness: FQ, assert_msg: str):
        is_not_padding = FQ(1 - (self.address == 0))  # 1 - is_zero(self.address)

        # 0. Copy constraints between pub_key and msg_hash bytes of this chip
        # and the ECDSA chip
        assert self.pub_key_x_bytes == self.ecdsa_chip.pub_key_x_bytes
        assert self.pub_key_y_bytes == self.ecdsa_chip.pub_key_y_bytes
        assert self.msg_hash_bytes == self.ecdsa_chip.msg_hash_bytes

        # 1. Verify that keccak(pub_key_bytes) = pub_key_hash by keccak table
        # lookup, where pub_key_bytes is built from the pub_key in the
        # ecdsa_chip
        pub_key_bytes = bytes(reversed(self.pub_key_x_bytes)) + bytes(
            reversed(self.pub_key_y_bytes)
        )
        keccak_table.lookup(
            is_not_padding,
            is_not_padding
            * RLC(bytes(reversed(pub_key_bytes)), keccak_randomness, n_bytes=64).expr(),
            is_not_padding * FQ(64),
            Word(self.pub_key_hash).select(is_not_padding),
            assert_msg,
        )

        # 2. Verify that the first 20 bytes of the pub_key_hash equal the address
        addr_expr = linear_combine_bytes(list(reversed(self.pub_key_hash[-20:])), FQ(2**8))
        assert (
            addr_expr == self.address
        ), f"{assert_msg}: {hex(addr_expr.n)} != {hex(self.address.n)}"

        # 3. Verify that the signed message in the ecdsa_chip with RLC encoding
        # corresponds to msg_hash
        msg_hash = Word(self.msg_hash_bytes)
        assert (
            msg_hash.select(is_not_padding) == self.msg_hash
        ), f"{assert_msg}: {hex(msg_hash.int_value())} != {hex(self.msg_hash.int_value())}"

        # 4. Verify the ECDSA signature
        self.ecdsa_chip.verify(assert_msg)


class Witness(NamedTuple):
    rows: List[Row]  # Transaction table rows
    keccak_table: KeccakTable
    sign_verifications: List[SignVerifyChip]


@is_circuit_code
def verify_circuit(
    witness: Witness,
    MAX_TXS: int,
    MAX_CALLDATA_BYTES: int,
    keccak_randomness: FQ,
) -> None:
    """
    Entry level circuit verification function
    """

    rows = witness.rows
    sign_verifications = witness.sign_verifications
    keccak_table = witness.keccak_table
    for tx_index in range(MAX_TXS):
        assert_msg = f"Constraints failed for tx_index = {tx_index}"
        tx_row_index = tx_index * Tag.TxSignHash
        caller_addr_index = tx_row_index + Tag.CallerAddress - 1
        tx_sign_hash_index = tx_row_index + Tag.TxSignHash - 1

        # SignVerifyChip constraint verification.  Padding txs rows contain
        # 0 in all values.  The SignVerifyChip skips the verification when
        # the caller_address == 0.
        sign_verifications[tx_index].verify(keccak_table, keccak_randomness, assert_msg)

        # 0. Copy constraints using fixed offsets between the tx rows and the SignVerifyChip
        assert rows[caller_addr_index].value.value() == sign_verifications[tx_index].address, (
            f"{assert_msg}: {rows[caller_addr_index].value.value()} != "
            + f"{sign_verifications[tx_index].address}"
        )
        assert rows[tx_sign_hash_index].value.lo == sign_verifications[tx_index].msg_hash.lo, (
            f"{assert_msg}: {rows[tx_sign_hash_index].value.lo} != "
            + f"{sign_verifications[tx_index].msg_hash.lo}"
        )
        assert rows[tx_sign_hash_index].value.hi == sign_verifications[tx_index].msg_hash.hi, (
            f"{assert_msg}: {rows[tx_sign_hash_index].value.hi} != "
            + f"{sign_verifications[tx_index].msg_hash.hi}"
        )

    # Remaining rows contain CallData.  Those rows don't have any circuit constraint.


class Transaction(NamedTuple):
    """
    Ethereum Transaction
    """

    nonce: U64
    gas_price: U256
    gas: U64
    to: Union[None, U160]
    value: U256
    data: bytes
    sig_v: U64
    sig_r: U256
    sig_s: U256

    def encode_to(self):
        if self.to is None:
            return bytes(0)
        return self.to.to_bytes(20, "big")


def padding_tx(tx_id: int) -> List[Row]:
    return [
        Row(FQ(tx_id), FQ(Tag.Nonce), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.Gas), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.GasPrice), FQ(0), Word(0)),
        Row(FQ(tx_id), FQ(Tag.CallerAddress), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.CalleeAddress), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.IsCreate), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.Value), FQ(0), Word(0)),
        Row(FQ(tx_id), FQ(Tag.CallDataLength), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.CallDataGasCost), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.TxInvalid), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.AccessListGasCost), FQ(0), FQ(0)),
        Row(FQ(tx_id), FQ(Tag.TxSignHash), FQ(0), FQ(0)),
    ]


def tx2witness(
    index: int, tx: Transaction, chain_id: U64, keccak_randomness: FQ, keccak_table: KeccakTable
) -> Tuple[List[Row], SignVerifyChip]:
    """
    Generate the witness data for a single transaction: generate the tx table
    rows, insert the pub_key_bytes entry in the keccak_table and assign the
    SignVerifyChip.
    """

    tx_sign_data = rlp.encode(
        [tx.nonce, tx.gas_price, tx.gas, tx.encode_to(), tx.value, tx.data, chain_id, 0, 0]
    )
    tx_sign_hash = keccak(tx_sign_data)

    sig_parity = tx.sig_v - 35 - chain_id * 2
    sig = KeyAPI.Signature(vrs=(sig_parity, tx.sig_r, tx.sig_s))

    pk = sig.recover_public_key_from_msg_hash(tx_sign_hash)
    pk_bytes = pk.to_bytes()
    keccak_table.add(pk_bytes, keccak_randomness)
    pk_hash = keccak(pk.to_bytes())
    addr = pk_hash[-20:]

    sign_verification = SignVerifyChip.assign(sig, pk, tx_sign_hash, keccak_randomness)

    call_data_gas_cost = sum(
        [
            (
                GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
                if byte == 0
                else GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
            )
            for byte in tx.data
        ]
    )

    # TODO: support (EIP 2930) type TX
    # access_list_gas_cost = sum(
    #     [
    #         GAS_COST_ACCESS_LIST_ADDRESS
    #         + len(access_tuple.storage_keys) * GAS_COST_ACCESS_LIST_STORAGE
    #         for access_tuple in tx.access_list
    #     ]
    # )
    access_list_gas_cost = 0

    tx_id = FQ(index + 1)
    rows: List[Row] = []
    rows.append(Row(tx_id, FQ(Tag.Nonce), FQ(0), FQ(tx.nonce)))
    rows.append(Row(tx_id, FQ(Tag.Gas), FQ(0), FQ(tx.gas)))
    rows.append(Row(tx_id, FQ(Tag.GasPrice), FQ(0), Word(tx.gas_price)))
    rows.append(Row(tx_id, FQ(Tag.CallerAddress), FQ(0), FQ(int.from_bytes(addr, "big"))))
    rows.append(Row(tx_id, FQ(Tag.CalleeAddress), FQ(0), FQ(tx.to or 0)))
    rows.append(Row(tx_id, FQ(Tag.IsCreate), FQ(0), FQ(1) if tx.to is None else FQ(0)))
    rows.append(Row(tx_id, FQ(Tag.Value), FQ(0), Word(tx.value)))
    rows.append(Row(tx_id, FQ(Tag.CallDataLength), FQ(0), FQ(len(tx.data))))
    rows.append(Row(tx_id, FQ(Tag.CallDataGasCost), FQ(0), FQ(call_data_gas_cost)))
    # here these 2 invalid flags are set by prover, and checking is deferred to begin_tx.
    rows.append(Row(tx_id, FQ(Tag.TxInvalid), FQ(0), FQ(0)))
    rows.append(Row(tx_id, FQ(Tag.AccessListGasCost), FQ(0), FQ(access_list_gas_cost)))
    tx_sign_hash_word = Word(int.from_bytes(tx_sign_hash, "big"))
    rows.append(Row(tx_id, FQ(Tag.TxSignHash), FQ(0), tx_sign_hash_word))
    for byte_index, byte in enumerate(tx.data):
        rows.append(Row(tx_id, FQ(Tag.CallData), FQ(byte_index), FQ(byte)))

    return (rows, sign_verification)


# Dummy signature, public key and message hash that passes verification used to
# padding transactions.  This values have calculated using the following values:
# secret key = 1
# message hash = 1
# keccak_randomness = 1
DUMMY_SIGNATURE = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81799,
)
DUMMY_PUBLIC_KEY = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)
DUMMY_MSG_HASH = 0x0000000000000000000000000000000000000000000000000000000000000001


def txs2witness(
    txs: List[Transaction],
    chain_id: U64,
    MAX_TXS: int,
    MAX_CALLDATA_BYTES: int,
    keccak_randomness: FQ,
) -> Witness:
    """
    Generate the complete witness of the transactions for a fixed size circuit.
    """

    assert len(txs) <= MAX_TXS

    keccak_table = KeccakTable()
    sign_verifications: List[SignVerifyChip] = []
    tx_fixed_rows: List[Row] = []  # Accumulate fixed rows of each tx
    tx_dyn_rows: List[Row] = []  # Accumulate CallData rows of each tx
    for index, tx in enumerate(txs):
        tx_rows, sign_verification = tx2witness(
            index, tx, chain_id, keccak_randomness, keccak_table
        )
        sign_verifications.append(sign_verification)
        for row in tx_rows:
            if row.tag == Tag.CallData:
                tx_dyn_rows.append(row)
            else:
                tx_fixed_rows.append(row)

    assert len(tx_dyn_rows) <= MAX_CALLDATA_BYTES

    # Fill all the rows in the fixed region to reach MAX_TXS * Tag.TxSignHash
    # offset in the bottom.  These front padding txs use sequential tx_id that
    # continue from the real txs.  Padding txs have all values at 0 (and in
    # particular, are defined with CallerAddress = 0), and they can used to
    # prove a lower bound on the number padding txs in the fixed region.
    # Then fill all the rows in the dynamic region to reach MAX_CALLDATA_BYTES with
    # pad rows in the back.
    tx_padding_rows = []
    for i in range(len(txs), MAX_TXS):
        tx_padding_rows += padding_tx(i + 1)
    rows = (
        tx_fixed_rows
        + tx_padding_rows
        + tx_dyn_rows
        + [Row(FQ(0), FQ(Tag.CallData), FQ(0), FQ(0))] * (MAX_CALLDATA_BYTES - len(tx_dyn_rows))
    )

    dummy_ecdsa_chip = ECDSAVerifyChip(
        (Secp256k1ScalarField(DUMMY_SIGNATURE[0]), Secp256k1ScalarField(DUMMY_SIGNATURE[1])),
        (Secp256k1BaseField(DUMMY_PUBLIC_KEY[0]), Secp256k1BaseField(DUMMY_PUBLIC_KEY[1])),
        Secp256k1ScalarField(DUMMY_MSG_HASH),
    )
    padding_sign_verification = SignVerifyChip(
        bytes([0] * 32),
        FQ(0),
        Word(0),
        dummy_ecdsa_chip,
    )
    # Fill the rest of sign_verifications with the witnessess assigned to 0s
    # and dummy ecdsa vefification values to disable the verification.
    sign_verifications = sign_verifications + [padding_sign_verification] * (MAX_TXS - len(txs))

    return Witness(rows, keccak_table, sign_verifications)
