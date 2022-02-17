from __future__ import annotations
from typing import Any, Dict, Iterator, NewType, Optional, Sequence, List
from functools import reduce
from itertools import chain

from ..util import (
    FQ,
    U64,
    U160,
    U256,
    RLC,
    keccak256,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
)
from .table import (
    BlockContextFieldTag,
    TxContextFieldTag,
    BytecodeTableRow,
    TxTableRow,
    BlockTableRow,
)
from .opcode import get_push_size, Opcode


class Block:
    coinbase: U160

    # Gas needs a lot arithmetic operation or comparison in EVM circuit, so we
    # assume gas limit in the near futuer will not exceed U64, to reduce the
    # implementation complexity.
    gas_limit: U64

    # For other fields, we follow the size defined in yellow paper for now.
    number: U256
    timestamp: U64
    difficulty: U256
    base_fee: U256

    # It contains most recent 256 block hashes in history, where the lastest
    # one is at history_hashes[-1].
    history_hashes: Sequence[U256]

    def __init__(
        self,
        coinbase: U160 = U160(0x10),
        gas_limit: U64 = U64(15_000_000),
        number: U256 = U256(0),
        timestamp: U64 = U64(0),
        difficulty: U256 = U256(0),
        base_fee: U256 = U256(1_000_000_000),
        history_hashes: Sequence[U256] = [],
    ) -> None:
        assert len(history_hashes) <= min(256, number)

        self.coinbase = coinbase
        self.gas_limit = gas_limit
        self.number = number
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.base_fee = base_fee
        self.history_hashes = history_hashes

    def table_assignments(self, randomness: FQ) -> List[BlockTableRow]:
        return [
            BlockTableRow(BlockContextFieldTag.Coinbase, FQ(0), FQ(self.coinbase)),
            BlockTableRow(BlockContextFieldTag.GasLimit, FQ(0), FQ(self.gas_limit)),
            BlockTableRow(BlockContextFieldTag.Number, FQ(0), RLC(self.number, randomness)),
            BlockTableRow(BlockContextFieldTag.Timestamp, FQ(0), FQ(self.timestamp)),
            BlockTableRow(BlockContextFieldTag.Difficulty, FQ(0), RLC(self.difficulty, randomness)),
            BlockTableRow(BlockContextFieldTag.BaseFee, FQ(0), RLC(self.base_fee, randomness)),
        ] + [
            BlockTableRow(
                BlockContextFieldTag.HistoryHash,
                FQ(self.number - idx - 1),
                RLC(history_hash, randomness),
            )
            for idx, history_hash in enumerate(reversed(self.history_hashes))
        ]


class Transaction:
    id: int
    nonce: U64
    gas: U64
    gas_price: U256
    caller_address: U160
    callee_address: Optional[U160]
    value: U256
    call_data: bytes

    def __init__(
        self,
        id: int = 1,
        nonce: U64 = U64(0),
        gas: U64 = U64(21_000),
        gas_price: U256 = U256(2_000_000_000),
        caller_address: U160 = U160(0),
        callee_address: Optional[U160] = None,
        value: U256 = U256(0),
        call_data: bytes = bytes(),
    ) -> None:
        self.id = id
        self.nonce = nonce
        self.gas = gas
        self.gas_price = gas_price
        self.caller_address = caller_address
        self.callee_address = callee_address
        self.value = value
        self.call_data = call_data

    def call_data_gas_cost(self) -> int:
        return reduce(
            lambda acc, byte: (
                acc
                + (
                    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
                    if byte == 0
                    else GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
                )
            ),
            self.call_data,
            0,
        )

    def table_assignments(self, randomness: FQ) -> Iterator[TxTableRow]:
        return chain(
            [
                TxTableRow(FQ(self.id), TxContextFieldTag.Nonce, FQ(0), FQ(self.nonce)),
                TxTableRow(FQ(self.id), TxContextFieldTag.Gas, FQ(0), FQ(self.gas)),
                TxTableRow(
                    FQ(self.id),
                    TxContextFieldTag.GasPrice,
                    FQ(0),
                    RLC(self.gas_price, randomness),
                ),
                TxTableRow(
                    FQ(self.id), TxContextFieldTag.CallerAddress, FQ(0), FQ(self.caller_address)
                ),
                TxTableRow(
                    FQ(self.id),
                    TxContextFieldTag.CalleeAddress,
                    FQ(0),
                    FQ(self.callee_address or 0),
                ),
                TxTableRow(
                    FQ(self.id), TxContextFieldTag.IsCreate, FQ(0), FQ(self.callee_address is None)
                ),
                TxTableRow(
                    FQ(self.id), TxContextFieldTag.Value, FQ(0), RLC(self.value, randomness)
                ),
                TxTableRow(
                    FQ(self.id), TxContextFieldTag.CallDataLength, FQ(0), FQ(len(self.call_data))
                ),
                TxTableRow(
                    FQ(self.id),
                    TxContextFieldTag.CallDataGasCost,
                    FQ(0),
                    FQ(self.call_data_gas_cost()),
                ),
            ],
            map(
                lambda item: TxTableRow(
                    FQ(self.id), TxContextFieldTag.CallData, FQ(item[0]), FQ(item[1])
                ),
                enumerate(self.call_data),
            ),
        )


class Bytecode:
    code: bytearray

    def __init__(self, code: Optional[bytearray] = None) -> None:
        self.code = bytearray() if code is None else code

    def __getattr__(self, name: str):
        def method(*args) -> Bytecode:
            try:
                opcode = Opcode[name.removesuffix("_").upper()]
            except KeyError:
                raise ValueError(f"Invalid opcode {name}")

            if opcode.is_push():
                assert len(args) == 1
                self.push(args[0], opcode - Opcode.PUSH1 + 1)
            elif opcode.is_dup() or opcode.is_swap():
                assert len(args) == 0
                self.code.append(opcode)
            else:
                assert len(args) <= 1024 - opcode.max_stack_pointer()
                for arg in reversed(args):
                    self.push(arg, 32)
                self.code.append(opcode)

            return self

        return method

    def push(self, value: Any, n_bytes: int = 32) -> Bytecode:
        if isinstance(value, int):
            value = value.to_bytes(n_bytes, "big")
        elif isinstance(value, str):
            value = bytes.fromhex(value.lower().removeprefix("0x"))
        elif isinstance(value, RLC):
            value = value.be_bytes()
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            ...
        else:
            raise NotImplementedError(f"Value of type {type(value)} is not yet supported")

        assert 0 < len(value) <= n_bytes, ValueError("Too many bytes as data portion of PUSH*")

        opcode = Opcode.PUSH1 + n_bytes - 1
        self.code.append(opcode)
        self.code.extend(value.rjust(n_bytes, bytes(1)))

        return self

    def hash(self) -> U256:
        return U256(int.from_bytes(keccak256(self.code), "big"))

    def table_assignments(self, randomness: FQ) -> Iterator[BytecodeTableRow]:
        class BytecodeIterator:
            idx: int
            push_data_left: int
            hash: RLC
            code: bytes

            def __init__(self, hash: RLC, code: bytes):
                self.idx = 0
                self.push_data_left = 0
                self.hash = hash
                self.code = code

            def __iter__(self):
                return self

            def __next__(self):
                if self.idx == len(self.code):
                    raise StopIteration

                idx = self.idx
                byte = self.code[idx]

                is_code = self.push_data_left == 0
                self.push_data_left = get_push_size(byte) if is_code else self.push_data_left - 1

                self.idx += 1

                return (self.hash.value, idx, byte, is_code)

        return BytecodeIterator(RLC(self.hash(), randomness), self.code)


Storage = NewType("Storage", Dict[U256, U256])


class Account:
    address: U160
    nonce: U256
    balance: U256
    code: Bytecode
    storage: Storage

    def __init__(
        self,
        address: U160 = U160(0),
        nonce: U256 = U256(0),
        balance: U256 = U256(0),
        code: Optional[Bytecode] = None,
        storage: Optional[Storage] = None,
    ) -> None:
        self.address = address
        self.nonce = nonce
        self.balance = balance
        self.code = Bytecode() if code is None else code
        self.storage = Storage(dict()) if storage is None else storage

    def code_hash(self) -> U256:
        return self.code.hash()

    def storage_trie_hash(self) -> U256:
        raise NotImplementedError("Trie has not been implemented")
