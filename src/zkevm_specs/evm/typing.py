from typing import Iterator, Optional, Sequence, Union

from ..util import U64, U160, U256, Array3, Array4, RLCStore, keccak256
from .table import BlockContextFieldTag, TxContextFieldTag
from .opcode import get_push_size


class Block:
    coinbase: U160
    gas_limit: U64
    block_number: U256
    time: U64
    difficulty: U256
    base_fee: U256

    # history_hashes contains most recent 256 block hashes in history, where
    # the lastest one is at history_hashes[-1].
    history_hashes: Sequence[U256]

    def __init__(
        self,
        coinbase: U160 = 0x10,
        gas_limit: U64 = int(15e6),
        block_number: U256 = 0,
        time: U64 = 0,
        difficulty: U256 = 0,
        base_fee: U256 = int(1e9),
        history_hashes: Sequence[U256] = [],
    ) -> None:
        assert len(history_hashes) <= 256

        self.coinbase = coinbase
        self.gas_limit = gas_limit
        self.block_number = block_number
        self.time = time
        self.difficulty = difficulty
        self.base_fee = base_fee
        self.history_hashes = history_hashes

    def table_assignments(self, rlc_store: RLCStore) -> Sequence[Array3]:
        return [
            (BlockContextFieldTag.Coinbase, 0, self.coinbase),
            (BlockContextFieldTag.GasLimit, 0, self.gas_limit),
            (BlockContextFieldTag.BlockNumber, 0, rlc_store.to_rlc(self.block_number, 32)),
            (BlockContextFieldTag.Time, 0, rlc_store.to_rlc(self.time, 32)),
            (BlockContextFieldTag.Difficulty, 0, rlc_store.to_rlc(self.difficulty, 32)),
            (BlockContextFieldTag.BaseFee, 0, rlc_store.to_rlc(self.base_fee, 32)),
        ] + [
            (BlockContextFieldTag.BlockHash, self.block_number + idx - 1, rlc_store.to_rlc(block_hash, 32))
            for idx, block_hash in enumerate(reversed(self.history_hashes))
        ]


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

                is_code = self.push_data_left == 0
                self.push_data_left = get_push_size(byte) if is_code else self.push_data_left - 1

                self.idx += 1

                return (self.hash, idx, byte, is_code)

        return BytecodeIterator(rlc_store.to_rlc(self.hash, 32), self.bytes)
