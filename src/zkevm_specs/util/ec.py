from __future__ import annotations
from typing import Tuple
from eth_keys import KeyAPI  # type: ignore
from .arithmetic import FP, FQ
from py_ecc.bn128.bn128_curve import add, eq


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

    def to_int_value(self) -> int:
        (l0, l1, l2, l3) = self.limbs
        return l0.n + (l1.n << 1 * 72) + (l2.n << 2 * 72) + (l3.n << 3 * 72)

    def to_le_bytes(self) -> bytes:
        return self.to_int_value().to_bytes(32, "little")

    def to_be_bytes(self) -> bytes:
        return self.to_int_value().to_bytes(32, "big")


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


# TODO: There is another one used in tx_circuit, try to merge into one.
#       Reminder: endianness of public key is differ with the one in tx_circuit
class ECDSAVerifyChip:
    """
    ECDSA Signature Verification Chip.  This represents an ECDSA signature
    verification Chip as implemented in
    https://github.com/privacy-scaling-explorations/halo2wrong/blob/master/ecdsa/src/ecdsa.rs
    """

    sig_v: Secp256k1ScalarField
    sig_r: Secp256k1ScalarField
    sig_s: Secp256k1ScalarField
    pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField]
    pub_key_x_bytes: bytes
    pub_key_y_bytes: bytes
    msg_hash: Secp256k1ScalarField
    msg_hash_bytes: bytes

    def __init__(
        self,
        signature: Tuple[Secp256k1ScalarField, Secp256k1ScalarField, Secp256k1ScalarField],
        pub_key: Tuple[Secp256k1BaseField, Secp256k1BaseField],
        msg_hash: Secp256k1ScalarField,
    ) -> None:
        self.sig_v = signature[0]
        self.sig_r = signature[1]
        self.sig_s = signature[2]
        self.pub_key = pub_key
        self.msg_hash = msg_hash
        self.pub_key_x_bytes = pub_key[0].to_le_bytes()
        self.pub_key_y_bytes = pub_key[1].to_le_bytes()
        self.msg_hash_bytes = msg_hash.to_be_bytes()
        # NOTE: The circuit must constrain that all elements in the `*_bytes`
        # parameters  are in range 0..255 and that they represent the same
        # value as their corresponding WrongFieldInteger limbs.

    @classmethod
    def assign(cls, signature: KeyAPI.Signature, pub_key: KeyAPI.PublicKey, msg_hash: bytes):
        # signature
        self_sig_v = Secp256k1ScalarField(signature.v)
        self_sig_r = Secp256k1ScalarField(signature.r)
        self_sig_s = Secp256k1ScalarField(signature.s)
        # public key
        pub_key_bytes = pub_key.to_bytes()
        pub_key_bytes_x, pub_key_bytes_y = pub_key_bytes[:32], pub_key_bytes[32:]
        pub_key_x = int.from_bytes(pub_key_bytes_x, "big")
        pub_key_y = int.from_bytes(pub_key_bytes_y, "big")
        self_pub_key = (Secp256k1BaseField(pub_key_x), Secp256k1BaseField(pub_key_y))
        # message hash
        self_msg_hash = Secp256k1ScalarField(int.from_bytes(msg_hash, "big"))
        return cls((self_sig_v, self_sig_r, self_sig_s), self_pub_key, self_msg_hash)

    def verify(self) -> bool:
        sig_v = int.from_bytes(self.sig_v.to_le_bytes(), "little")
        sig_r = int.from_bytes(self.sig_r.to_le_bytes(), "little")
        sig_s = int.from_bytes(self.sig_s.to_le_bytes(), "little")
        signature = KeyAPI.Signature(vrs=[sig_v, sig_r, sig_s])

        msg_hash = bytes(self.msg_hash.to_be_bytes())
        public_key = KeyAPI.PublicKey(self.pub_key[0].to_be_bytes() + self.pub_key[1].to_be_bytes())
        return KeyAPI().ecdsa_verify(msg_hash, signature, public_key)


class ECCVerifyChip:
    """
    ECC Verification Chip.  This represents an ECC verification Chip as implemented in
    https://github.com/privacy-scaling-explorations/halo2wrong/blob/master/ecc/src/general_field_ecc.rs
    """

    p0: Tuple[FP, FP]
    p1: Tuple[FP, FP]
    output: Tuple[FP, FP]

    def __init__(
        self,
        p0: Tuple[FP, FP],
        p1: Tuple[FP, FP],
        output: Tuple[FP, FP],
    ) -> None:
        self.p0 = p0
        self.p1 = p1
        self.output = output

    @classmethod
    def assign(
        cls,
        p0: Tuple[FP, FP],
        p1: Tuple[FP, FP],
        output: Tuple[FP, FP],
    ):
        return cls((p0[0], p0[1]), (p1[0], p1[1]), (output[0], output[1]))

    def verify_add(self) -> bool:
        result = add(self.p0, self.p1)
        result = (0, 0) if result is None else result
        return eq(result, self.output)

    def verify_mul(self) -> bool:
        raise NotImplementedError("verify_mul is not supported yet")

    def verify_pairing(self) -> bool:
        raise NotImplementedError("verify_pairing is not supported yet")
