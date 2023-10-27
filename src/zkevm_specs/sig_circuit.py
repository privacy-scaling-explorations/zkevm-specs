from typing import List, NamedTuple
from .util import FQ, RLC, Word, ECDSAVerifyChip, KeccakTable, is_circuit_code
from eth_keys import KeyAPI  # type: ignore
from eth_utils import keccak


class Row:
    """
    Signature circuit
    Verify a message hash is signed by an Ethereum Address.
    """

    msg_hash: Word
    sig_v: FQ
    sig_r: Word
    sig_s: Word
    recovered_addr: FQ
    is_valid: FQ

    ecdsa_chip: ECDSAVerifyChip
    pub_key_hash: bytes
    pub_key_x_bytes: bytes
    pub_key_y_bytes: bytes
    msg_hash_bytes: bytes

    def __init__(
        self,
        pub_key_hash: bytes,
        address: FQ,
        msg_hash: Word,
        ecdsa_chip: ECDSAVerifyChip,
        is_valid: bool = True,
    ) -> None:
        self.ecdsa_chip = ecdsa_chip
        self.pub_key_x_bytes = ecdsa_chip.pub_key_x_bytes
        self.pub_key_y_bytes = ecdsa_chip.pub_key_y_bytes
        self.msg_hash_bytes = ecdsa_chip.msg_hash_bytes

        # table
        self.msg_hash = msg_hash
        self.sig_v = FQ(int.from_bytes(self.ecdsa_chip.sig_v.le_bytes, "little"))
        self.sig_r = Word(int.from_bytes(self.ecdsa_chip.sig_r.le_bytes, "little"))
        self.sig_s = Word(int.from_bytes(self.ecdsa_chip.sig_s.le_bytes, "little"))
        self.recovered_addr = address
        self.is_valid = is_valid

        self.pub_key_hash = pub_key_hash

    @classmethod
    def assign(
        cls,
        signature: KeyAPI.Signature,
        pub_key: KeyAPI.PublicKey,
        msg_hash: bytes,
        is_valid: bool = True,
    ):
        pub_key_hash = keccak(pub_key.to_bytes())
        self_pub_key_hash = pub_key_hash
        self_address = FQ(int.from_bytes(pub_key_hash[-20:], "big"))
        self_msg_hash = Word(int.from_bytes(msg_hash, "big"))
        self_ecdsa_chip = ECDSAVerifyChip.assign(signature, pub_key, msg_hash)
        return cls(self_pub_key_hash, self_address, self_msg_hash, self_ecdsa_chip, is_valid)

    def verify(self, keccak_table: KeccakTable, keccak_randomness: FQ, assert_msg: str):
        # 0. Copy constraints between pub_key, msg_hash and signature of this chip
        # and the ones in ECDSA chip
        assert self.pub_key_x_bytes == self.ecdsa_chip.pub_key_x_bytes
        assert self.pub_key_y_bytes == self.ecdsa_chip.pub_key_y_bytes
        assert self.msg_hash_bytes == self.ecdsa_chip.msg_hash_bytes
        assert self.sig_r.int_value() == int.from_bytes(self.ecdsa_chip.sig_r.le_bytes, "little")
        assert self.sig_s.int_value() == int.from_bytes(self.ecdsa_chip.sig_s.le_bytes, "little")

        # 1. Constrain v to be equal 0 or 1
        assert self.sig_v == 0 or self.sig_v == 1

        # 2. Verify that keccak(pub_key_bytes) = pub_key_hash by keccak table
        # lookup, where pub_key_bytes is built from the pub_key in the
        # ecdsa_chip
        pub_key_bytes = bytes(reversed(self.pub_key_x_bytes)) + bytes(
            reversed(self.pub_key_y_bytes)
        )
        keccak_table.lookup(
            True,
            RLC(bytes(reversed(pub_key_bytes)), keccak_randomness, n_bytes=64).expr(),
            FQ(64),
            Word(self.pub_key_hash),
            assert_msg,
        )

        # 3. Verify that the least significant 20 bytes of the pub_key_hash equals `recovered_addr`
        addr_expr = FQ(int.from_bytes(bytes(self.pub_key_hash[-20:]), "big"))
        assert (
            addr_expr == self.recovered_addr
        ), f"{assert_msg}: {hex(addr_expr.n)} != {hex(self.recovered_addr.n)}"

        # 4. Verify that the signed message in the ecdsa_chip equals `msg_hash`
        msg_hash = Word(self.msg_hash_bytes)
        assert (
            msg_hash == self.msg_hash
        ), f"{assert_msg}: {hex(msg_hash.int_value())} != {hex(self.msg_hash.int_value())}"

        # 5. Verify the ECDSA signature
        is_valid = self.ecdsa_chip.verify()
        assert is_valid == self.is_valid, f"{assert_msg}: {is_valid} != {self.is_valid}"


class Witness(NamedTuple):
    rows: List[Row]  # Transaction table rows
    keccak_table: KeccakTable


@is_circuit_code
def verify_circuit(
    witness: Witness,
    keccak_randomness: FQ,
) -> None:
    """
    Entry level circuit verification function
    """
    for i, row in enumerate(witness.rows):
        assert_msg = f"Constraints failed at row = {i}"
        row.verify(witness.keccak_table, keccak_randomness, assert_msg)
