from typing import Iterator, Optional, Sequence, Union

from ..util import U64, U160, U256, Array4, RLCStore, keccak256
from .table import TxContextFieldTag


class Block:
    coinbase: U160
    gas_limit: U64
    block_number: U256
    time: U256
    difficulty: U256
    base_fee: U256
    block_hashes: Sequence[U256]

    def __init__(
        self,
        coinbase: U160 = 0x10,
        gas_limit: U64 = int(15e6),
        block_number: U256 = 0,
        time: U256 = 0,
        difficulty: U256 = 0,
        base_fee: U256 = int(1e9),
        block_hashes: Sequence[U256] = [],
    ) -> None:
        self.coinbase = coinbase
        self.gas_limit = gas_limit
        self.block_number = block_number
        self.time = time
        self.difficulty = difficulty
        self.base_fee = base_fee
        self.block_hashes = block_hashes


class Transaction:
    id: int
    nonce: U64
    gas: U64
    gas_tip_cap: U256
    gas_fee_cap: U256
    caller_address: U160
    callee_address: Optional[U160]
    value: U256
    call_data: bytes

    def __init__(
        self,
        id: int = 1,
        nonce: U64 = 0,
        gas: U64 = 21000,
        gas_tip_cap: U256 = int(1e9),
        gas_fee_cap: U256 = int(2e9),
        caller_address: U160 = 0,
        callee_address: Optional[U160] = None,
        value: U256 = 0,
        call_data: bytes = bytes(),
    ) -> None:
        self.id = id
        self.nonce = nonce
        self.gas = gas
        self.gas_tip_cap = gas_tip_cap
        self.gas_fee_cap = gas_fee_cap
        self.caller_address = caller_address
        self.callee_address = callee_address
        self.value = value
        self.call_data = call_data

    def gas_price(self, base_fee: int) -> int:
        return min(base_fee + self.gas_tip_cap, self.gas_fee_cap)

    def table_assignments(self, rlc_store: RLCStore) -> Sequence[Array4]:
        return [
            (self.id, TxContextFieldTag.Nonce, 0, self.nonce),
            (self.id, TxContextFieldTag.Gas, 0, self.gas),
            (self.id, TxContextFieldTag.GasTipCap, 0, rlc_store.to_rlc(self.gas_tip_cap, 32)),
            (self.id, TxContextFieldTag.GasFeeCap, 0, rlc_store.to_rlc(self.gas_fee_cap, 32)),
            (self.id, TxContextFieldTag.CallerAddress, 0, self.caller_address),
            (self.id, TxContextFieldTag.CalleeAddress, 0, self.callee_address),
            (self.id, TxContextFieldTag.IsCreate, 0, self.callee_address is None),
            (self.id, TxContextFieldTag.Value, 0, rlc_store.to_rlc(self.value, 32)),
            (self.id, TxContextFieldTag.CallDataLength, 0, len(self.call_data)),
        ] + [(self.id, TxContextFieldTag.CallData, idx, byte) for idx, byte in enumerate(self.call_data)]


class Bytecode:
    hash: U256
    bytes: bytes

    def __init__(
        self,
        str_or_bytes: Union[str, bytes],
    ):
        if type(str_or_bytes) is str:
            str_or_bytes = bytes.fromhex(str_or_bytes)

        self.hash = int.from_bytes(keccak256(str_or_bytes), "little")
        self.bytes = str_or_bytes

    def table_assignments(self, rlc_store: RLCStore) -> Iterator[Array4]:
        class BytecodeIterator:
            idx: int
            push_data_left: int
            hash: int
            bytes: bytes

            def __init__(self, hash: int, bytes: bytes):
                self.idx = 0
                self.push_data_left = 0
                self.hash = hash
                self.bytes = bytes

            def __iter__(self):
                return self

            def __next__(self):
                if self.idx == len(self.bytes):
                    raise StopIteration

                idx = self.idx
                byte = self.bytes[idx]
                is_code = True

                if self.push_data_left > 0:
                    is_code = False
                    self.push_data_left -= 1
                elif 0x60 <= byte < 0x80:
                    self.push_data_left = byte - 0x60 + 1

                self.idx += 1

                return (self.hash, idx, byte, is_code)

        return BytecodeIterator(rlc_store.to_rlc(self.hash, 32), self.bytes)
