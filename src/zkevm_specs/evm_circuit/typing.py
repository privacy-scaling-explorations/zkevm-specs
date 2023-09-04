from __future__ import annotations
import dataclasses
from typing import (
    cast,
    Dict,
    Iterator,
    List,
    MutableSequence,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    Union,
    Mapping,
    Tuple,
)
from functools import reduce
from itertools import chain

from ..util import (
    U64,
    U160,
    U256,
    FQ,
    IntOrFQ,
    RLC,
    WordOrValue,
    Word,
    Expression,
    keccak256,
    GAS_COST_ACCESS_LIST_ADDRESS,
    GAS_COST_ACCESS_LIST_STORAGE,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
    EMPTY_CODE_HASH,
)
from .table import (
    RW,
    AccountFieldTag,
    BlockContextFieldTag,
    BlockTableRow,
    BytecodeFieldTag,
    BytecodeTableRow,
    CallContextFieldTag,
    RWTableRow,
    Target,
    TxContextFieldTag,
    TxLogFieldTag,
    TxReceiptFieldTag,
    TxTableRow,
    CopyDataTypeTag,
    CopyCircuitRow,
    KeccakTableRow,
    ExpCircuitRow,
)
from .opcode import get_push_size, Opcode


POW2 = 2**256


class Block:
    coinbase: U160

    # Gas needs a lot arithmetic operation or comparison in EVM circuit, so we
    # assume gas limit in the near futuer will not exceed U64, to reduce the
    # implementation complexity.
    gas_limit: U64

    # For other fields, we follow the size defined in yellow paper for now.
    # as described in https://eips.ethereum.org/EIPS/eip-1985,
    # block number and timestamp are inside a range between 0 and 0x7fffffffffffffff
    # (2**63 - 1, 9223372036854775807).
    number: U64
    timestamp: U64
    prev_randao: U256
    base_fee: U256

    # Even ChainId is not a block parameter, since all txs of a block are meant
    # to use the same chain_id, we set it as as a block parameter.
    chainid: U64

    # It contains most recent 256 block hashes in history, where the lastest
    # one is at history_hashes[-1].
    history_hashes: Sequence[U256]

    def __init__(
        self,
        coinbase: U160 = U160(0x10),
        gas_limit: U64 = U64(int(15e6)),
        number: U64 = U64(0),
        timestamp: U64 = U64(0),
        prev_randao: U256 = U256(0),
        base_fee: U256 = U256(int(1e9)),
        chainid: U64 = U64(0x01),
        history_hashes: Sequence[U256] = [],
    ) -> None:
        assert len(history_hashes) <= min(256, number)

        self.coinbase = coinbase
        self.gas_limit = gas_limit
        self.number = number
        self.timestamp = timestamp
        self.prev_randao = prev_randao
        self.base_fee = base_fee
        self.chainid = chainid
        self.history_hashes = history_hashes

    def table_assignments(self) -> List[BlockTableRow]:
        value = lambda v: WordOrValue(FQ(v))
        word = lambda w: WordOrValue(Word(w))
        return [
            BlockTableRow(FQ(BlockContextFieldTag.Coinbase), FQ(0), word(self.coinbase)),
            BlockTableRow(FQ(BlockContextFieldTag.GasLimit), FQ(0), value(self.gas_limit)),
            BlockTableRow(FQ(BlockContextFieldTag.Number), FQ(0), value(self.number)),
            BlockTableRow(FQ(BlockContextFieldTag.Timestamp), FQ(0), value(self.timestamp)),
            BlockTableRow(FQ(BlockContextFieldTag.PrevRandao), FQ(0), word(self.prev_randao)),
            BlockTableRow(FQ(BlockContextFieldTag.BaseFee), FQ(0), word(self.base_fee)),
            BlockTableRow(FQ(BlockContextFieldTag.ChainId), FQ(0), value(self.chainid)),
        ] + [
            BlockTableRow(
                FQ(BlockContextFieldTag.HistoryHash),
                FQ(self.number - idx - 1),
                word(history_hash),
            )
            for idx, history_hash in enumerate(reversed(self.history_hashes))
        ]


class AccessTuple(NamedTuple):
    address: U160
    storage_keys: List[U256]


class Transaction:
    id: int
    nonce: U64
    gas: U64
    gas_price: U256
    caller_address: U160
    callee_address: Optional[U160]
    value: U256
    call_data: bytes
    invalid_tx: int
    access_list: List[AccessTuple]

    def __init__(
        self,
        id: int = 1,
        nonce: U64 = U64(0),
        gas: U64 = U64(21000),
        gas_price: U256 = U256(int(2e9)),
        caller_address: U160 = U160(0xCAFE),
        callee_address: Optional[U160] = None,
        value: U256 = U256(0),
        call_data: bytes = bytes(),
        invalid_tx: int = 0,
        access_list: List[AccessTuple] = list(),
    ) -> None:
        self.id = id
        self.nonce = nonce
        self.gas = gas
        self.gas_price = gas_price
        self.caller_address = caller_address
        self.callee_address = callee_address
        self.value = value
        self.call_data = call_data
        self.invalid_tx = invalid_tx
        self.access_list = access_list

    @classmethod
    def padding(obj, id: int):
        tx = obj(id, U64(0), U64(0), U256(0), U160(0), U160(0), U256(0), bytes(), 0, list())
        return tx

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

    def access_list_gas_cost(self) -> int:
        return sum(
            [
                GAS_COST_ACCESS_LIST_ADDRESS
                + len(access_tuple.storage_keys) * GAS_COST_ACCESS_LIST_STORAGE
                for access_tuple in self.access_list
            ]
        )

    def table_fixed(self) -> List[TxTableRow]:
        value = lambda v: WordOrValue(FQ(v))
        word = lambda w: WordOrValue(Word(w))
        return [
            TxTableRow(FQ(self.id), FQ(TxContextFieldTag.Nonce), FQ(0), value(self.nonce)),
            TxTableRow(FQ(self.id), FQ(TxContextFieldTag.Gas), FQ(0), value(self.gas)),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.GasPrice),
                FQ(0),
                word(self.gas_price),
            ),
            TxTableRow(
                FQ(self.id), FQ(TxContextFieldTag.CallerAddress), FQ(0), word(self.caller_address)
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.CalleeAddress),
                FQ(0),
                word(0 if self.callee_address is None else self.callee_address),
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.IsCreate),
                FQ(0),
                value(self.callee_address is None),
            ),
            TxTableRow(FQ(self.id), FQ(TxContextFieldTag.Value), FQ(0), word(self.value)),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.CallDataLength),
                FQ(0),
                value(len(self.call_data)),
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.CallDataGasCost),
                FQ(0),
                value(self.call_data_gas_cost()),
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.TxInvalid),
                FQ(0),
                value(self.invalid_tx),
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.AccessListGasCost),
                FQ(0),
                value(self.access_list_gas_cost()),
            ),
            TxTableRow(
                FQ(self.id),
                FQ(TxContextFieldTag.TxSignHash),
                FQ(0),
                value(1234),  # Mock value for TxSignHash
            ),
        ]

    def table_assignments(self) -> Iterator[TxTableRow]:
        return chain(
            self.table_fixed(),
            map(
                lambda item: TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.CallData),
                    FQ(item[0]),
                    WordOrValue(FQ(item[1])),
                ),
                enumerate(self.call_data),
            ),
        )


def init_is_code(code: bytearray) -> MutableSequence[bool]:
    is_codes = []
    push_data_left = 0
    for idx in range(0, len(code)):
        is_code = push_data_left == 0
        push_data_left = get_push_size(code[idx]) if is_code else push_data_left - 1
        is_codes.append(is_code)
    return is_codes


class Bytecode:
    code: bytearray
    is_code: MutableSequence[bool]

    def __init__(
        self, code: Optional[bytearray] = None, is_code: Optional[MutableSequence[bool]] = None
    ) -> None:
        self.code = bytearray() if code is None else code
        self.is_code = init_is_code(self.code) if is_code is None else is_code

    def __getattr__(self, name: str):
        def method(*args) -> Bytecode:
            opcode: Opcode
            try:
                opcode = Opcode[name.removesuffix("_").upper()]
            except KeyError:
                raise ValueError(f"Invalid opcode {name}")

            if opcode.is_push_with_data():
                assert len(args) == 1
                self.push(args[0], opcode - Opcode.PUSH0)
            elif opcode.is_dup() or opcode.is_swap():
                assert len(args) == 0
                self.code.append(opcode)
                self.is_code.append(True)
            else:
                assert len(args) <= 1024 - opcode.max_stack_pointer()
                for arg in reversed(args):
                    self.push(arg)
                self.code.append(opcode)
                self.is_code.append(True)

            return self

        return method

    def push(self, value: Union[int, str, bytes, bytearray, RLC], n_bytes: int = 32) -> Bytecode:
        if isinstance(value, int):
            value = value.to_bytes(n_bytes, "big")
        elif isinstance(value, str):
            value = bytes.fromhex(value.lower().removeprefix("0x"))
        elif isinstance(value, RLC):
            value = bytes(reversed(value.le_bytes))
        elif isinstance(value, Word):
            value = value.int_value().to_bytes(n_bytes, "big")
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            ...
        else:
            raise NotImplementedError(f"Value of type {type(value)} is not yet supported")

        assert 0 <= len(value) <= n_bytes, ValueError("Too many bytes as data portion of PUSH*")

        opcode = Opcode.PUSH0 + n_bytes
        self.code.append(opcode)
        self.is_code.append(True)
        self.code.extend(value.rjust(n_bytes, b"\x00"))
        self.is_code.extend([False] * n_bytes)

        return self

    def hash(self) -> U256:
        return U256(int.from_bytes(keccak256(self.code), "big"))

    def table_assignments(self) -> Iterator[BytecodeTableRow]:
        class BytecodeIterator:
            idx: int
            hash: Word
            code: bytes
            is_code: Sequence[bool]

            def __init__(self, hash: Word, code: bytes, is_code: Sequence[bool]):
                self.idx = 0
                self.hash = hash
                self.code = code
                self.is_code = is_code
                assert len(code) == len(is_code)

            def __iter__(self):
                return self

            def __next__(self):
                # return the length of the bytecode in the first row
                if self.idx == 0:
                    self.idx += 1
                    return BytecodeTableRow(
                        self.hash, FQ(BytecodeFieldTag.Header), FQ(0), FQ(0), FQ(len(self.code))
                    )

                if self.idx > len(self.code):
                    raise StopIteration

                # the other rows represent each byte in the bytecode
                idx = self.idx - 1
                byte = self.code[idx]
                is_code = self.is_code[idx]
                self.idx += 1
                return BytecodeTableRow(
                    self.hash, FQ(BytecodeFieldTag.Byte), FQ(idx), FQ(is_code), FQ(byte)
                )

        return BytecodeIterator(Word(self.hash()), self.code, self.is_code)


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

    def is_empty(self) -> bool:
        return self.nonce == 0 and self.balance == 0 and self.code_hash() == EMPTY_CODE_HASH


class RWDictionary:
    rw_counter: int
    rws: List[RWTableRow]

    def __init__(self, rw_counter: int) -> None:
        self.rw_counter = rw_counter
        self.rws = list()

    def stack_read(self, call_id: IntOrFQ, stack_pointer: IntOrFQ, value: Word) -> RWDictionary:
        return self._append(
            RW.Read, Target.Stack, id=FQ(call_id), address=FQ(stack_pointer), value=value
        )

    def stack_write(self, call_id: IntOrFQ, stack_pointer: IntOrFQ, value: Word) -> RWDictionary:
        return self._append(
            RW.Write, Target.Stack, id=FQ(call_id), address=FQ(stack_pointer), value=value
        )

    def memory_read(self, call_id: IntOrFQ, memory_address: IntOrFQ, byte: IntOrFQ) -> RWDictionary:
        return self._append(
            RW.Read, Target.Memory, id=FQ(call_id), address=FQ(memory_address), value=FQ(byte)
        )

    def memory_write(
        self, call_id: IntOrFQ, memory_address: IntOrFQ, byte: IntOrFQ
    ) -> RWDictionary:
        return self._append(
            RW.Write, Target.Memory, id=FQ(call_id), address=FQ(memory_address), value=FQ(byte)
        )

    def call_context_read(
        self, call_id: IntOrFQ, field_tag: CallContextFieldTag, value: Union[int, FQ, Word]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        # Sanity checks
        if field_tag in [
            CallContextFieldTag.CallerAddress,
            CallContextFieldTag.CalleeAddress,
            CallContextFieldTag.Value,
            CallContextFieldTag.CodeHash,
        ]:
            assert isinstance(value, Word)
        else:
            assert isinstance(value, FQ)
        return self._append(
            RW.Read, Target.CallContext, id=FQ(call_id), address=FQ(field_tag), value=value
        )

    def call_context_write(
        self, call_id: IntOrFQ, field_tag: CallContextFieldTag, value: Union[int, FQ, Word]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        # Sanity checks
        if field_tag in [
            CallContextFieldTag.CallerAddress,
            CallContextFieldTag.CalleeAddress,
            CallContextFieldTag.Value,
            CallContextFieldTag.CodeHash,
        ]:
            assert isinstance(value, Word)
        else:
            assert isinstance(value, FQ)
        return self._append(
            RW.Write, Target.CallContext, id=FQ(call_id), address=FQ(field_tag), value=value
        )

    def tx_log_write(
        self,
        tx_id: IntOrFQ,
        log_id: int,
        field_tag: TxLogFieldTag,
        index: IntOrFQ,
        value: Union[int, FQ, Word],
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        # Sanity checks
        if field_tag in [TxLogFieldTag.Address, TxLogFieldTag.Topic]:
            assert isinstance(value, Word)
        else:
            assert isinstance(value, FQ)
        return self._append(
            RW.Write,
            Target.TxLog,
            id=FQ(tx_id),
            address=FQ(index + (int(field_tag) << 32) + (log_id << 48)),
            field_tag=FQ(0),
            storage_key=Word(0),
            value=value,
        )

    def tx_receipt_read(
        self,
        tx_id: IntOrFQ,
        field_tag: TxReceiptFieldTag,
        value: IntOrFQ,
    ) -> RWDictionary:
        return self._append(
            RW.Read,
            Target.TxReceipt,
            id=FQ(tx_id),
            field_tag=FQ(field_tag),
            value=FQ(value),
        )

    def tx_receipt_write(
        self,
        tx_id: IntOrFQ,
        field_tag: TxReceiptFieldTag,
        value: IntOrFQ,
    ) -> RWDictionary:
        return self._append(
            RW.Write,
            Target.TxReceipt,
            id=FQ(tx_id),
            field_tag=FQ(field_tag),
            value=FQ(value),
        )

    def tx_refund_read(self, tx_id: IntOrFQ, refund: IntOrFQ) -> RWDictionary:
        return self._append(
            RW.Read, Target.TxRefund, id=FQ(tx_id), value=FQ(refund), value_prev=FQ(refund)
        )

    def tx_refund_write(
        self,
        tx_id: IntOrFQ,
        refund: IntOrFQ,
        refund_prev: IntOrFQ,
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        return self._state_write(
            Target.TxRefund,
            id=FQ(tx_id),
            value=FQ(refund),
            value_prev=FQ(refund_prev),
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def tx_access_list_account_write(
        self,
        tx_id: IntOrFQ,
        account_address: IntOrFQ,
        value: bool,
        value_prev: bool,
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        return self._state_write(
            Target.TxAccessListAccount,
            id=FQ(tx_id),
            address=FQ(account_address),
            value=FQ(value),
            value_prev=FQ(value_prev),
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def tx_access_list_account_read(
        self,
        tx_id: IntOrFQ,
        account_address: IntOrFQ,
        value: bool,
    ) -> RWDictionary:
        return self._state_read(
            Target.TxAccessListAccount,
            id=FQ(tx_id),
            address=FQ(account_address),
            value=FQ(value),
            value_prev=FQ(value),
        )

    def tx_access_list_account_storage_write(
        self,
        tx_id: IntOrFQ,
        account_address: IntOrFQ,
        storage_key: Word,
        value: bool,
        value_prev: bool,
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        return self._state_write(
            Target.TxAccessListAccountStorage,
            id=FQ(tx_id),
            address=FQ(account_address),
            storage_key=storage_key,
            value=FQ(value),
            value_prev=FQ(value_prev),
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def tx_access_list_account_storage_read(
        self,
        tx_id: IntOrFQ,
        account_address: IntOrFQ,
        storage_key: Word,
        value: bool,
    ) -> RWDictionary:
        return self._state_read(
            Target.TxAccessListAccountStorage,
            id=FQ(tx_id),
            address=FQ(account_address),
            storage_key=storage_key,
            value=FQ(value),
            value_prev=FQ(value),
        )

    def account_read(
        self, account_address: IntOrFQ, field_tag: AccountFieldTag, value: Union[int, FQ, Word]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Read,
            Target.Account,
            address=FQ(account_address),
            field_tag=FQ(field_tag),
            value=value,
            value_prev=value,
        )

    def account_write(
        self,
        account_address: IntOrFQ,
        field_tag: AccountFieldTag,
        value: Union[int, FQ, Word],
        value_prev: Union[int, FQ, Word],
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        if isinstance(value_prev, int):
            value_prev = FQ(value_prev)
        return self._state_write(
            Target.Account,
            address=FQ(account_address),
            field_tag=FQ(field_tag),
            value=value,
            value_prev=value_prev,
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def account_storage_read(
        self,
        account_address: IntOrFQ,
        storage_key: Word,
        value: Word,
        tx_id: IntOrFQ,
        value_committed: Word,
    ) -> RWDictionary:
        if isinstance(tx_id, int):
            tx_id = FQ(tx_id)
        return self._append(
            RW.Read,
            Target.AccountStorage,
            id=tx_id,
            address=FQ(account_address),
            storage_key=storage_key,
            value=value,
            value_prev=value,
            aux0=value_committed,
        )

    def account_storage_write(
        self,
        account_address: IntOrFQ,
        storage_key: Word,
        value: Word,
        value_prev: Word,
        tx_id: IntOrFQ,
        value_committed: Word,
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        if isinstance(tx_id, int):
            tx_id = FQ(tx_id)
        return self._state_write(
            Target.AccountStorage,
            id=tx_id,
            address=FQ(account_address),
            storage_key=storage_key,
            value=value,
            value_prev=value_prev,
            aux0=value_committed,
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def _state_write(
        self,
        tag: Target,
        id: Expression = FQ(0),
        address: Expression = FQ(0),
        field_tag: Expression = FQ(0),
        storage_key: Word = Word(0),
        value: Union[Word, FQ] = Word(0),
        value_prev: Union[Word, FQ] = Word(0),
        aux0: Word = Word(0),
        rw_counter_of_reversion: Optional[int] = None,
    ) -> RWDictionary:
        self._append(
            RW.Write,
            tag=tag,
            id=id,
            address=address,
            field_tag=field_tag,
            storage_key=storage_key,
            value=value,
            value_prev=value_prev,
            aux0=aux0,
        )

        if rw_counter_of_reversion is None:
            return self
        else:
            return self._append(
                RW.Write,
                tag=tag,
                id=id,
                address=address,
                field_tag=field_tag,
                storage_key=storage_key,
                value=value_prev,
                value_prev=value,
                aux0=aux0,
                rw_counter=rw_counter_of_reversion,
            )

    def _state_read(
        self,
        tag: Target,
        id: Expression = FQ(0),
        address: Expression = FQ(0),
        field_tag: Expression = FQ(0),
        storage_key: Word = Word(0),
        value: Union[Word, FQ] = Word(0),
        value_prev: Union[Word, FQ] = Word(0),
        aux0: Word = Word(0),
    ) -> RWDictionary:
        return self._append(
            RW.Read,
            tag=tag,
            id=id,
            address=address,
            field_tag=field_tag,
            storage_key=storage_key,
            value=value,
            value_prev=value_prev,
            aux0=aux0,
        )

    def _append(
        self,
        rw: RW,
        tag: Target,
        id: Expression = FQ(0),
        address: Expression = FQ(0),
        field_tag: Expression = FQ(0),
        storage_key: Word = Word(0),
        value: Union[Word, FQ] = Word(0),
        value_prev: Union[Word, FQ] = Word(0),
        aux0: Word = Word(0),
        rw_counter: Optional[int] = None,
    ) -> RWDictionary:
        if rw_counter is None:
            rw_counter = self.rw_counter
            self.rw_counter += 1

        self.rws.append(
            RWTableRow(
                FQ(rw_counter),
                FQ(rw),
                FQ(tag),
                id,
                address,
                field_tag,
                storage_key,
                WordOrValue(value),
                WordOrValue(value_prev),
                aux0,
            )
        )

        return self


class KeccakCircuit:
    rows: List[KeccakTableRow]

    def __init__(self) -> None:
        self.rows = []

    def add(self, data: bytes, r: FQ) -> KeccakCircuit:
        output = Word(int.from_bytes(keccak256(data), "big"))
        acc_input = RLC(bytes(reversed(data)), r, n_bytes=len(data))
        self.rows.append(
            KeccakTableRow(
                state_tag=FQ(2),  # Finalize
                input_rlc=acc_input.expr(),
                input_len=FQ(len(data)),
                output=output,
            )
        )
        return self


class ExpCircuit:
    rows: List[ExpCircuitRow]
    max_exp_steps: int
    OFFSET_INCREMENT = 7

    def __init__(self, max_exp_steps: int = 100) -> None:
        self.rows = []
        self.max_exp_steps = max_exp_steps

    def table(self) -> Sequence[ExpCircuitRow]:
        return self.rows

    def add_event(self, base: int, exponent: int, identifier: IntOrFQ):
        steps: List[Tuple[int, int, int]] = []
        exponentiation = self._exp_by_squaring(base, exponent, steps)
        steps.reverse()
        self._append_steps(base, exponent, exponentiation, steps, identifier)
        return self

    def _exp_by_squaring(self, base: int, exponent: int, steps: List[Tuple[int, int, int]]):
        # we assume that base and exponent are both < 2**256
        if exponent == 0:
            return 1
        if exponent == 1:
            return base

        exp1 = self._exp_by_squaring(base, exponent // 2, steps)
        exp2 = (exp1 * exp1) % POW2
        steps.append((exp1, exp1, exp2))
        if exponent % 2 == 0:
            # exponent is even
            return exp2
        else:
            # exponent is odd
            exp = (base * exp2) % POW2
            steps.append((exp2, base, exp))
            return exp

    def _append_steps(
        self,
        base: int,
        exponent: int,
        exponentiation: int,
        steps: List[Tuple[int, int, int]],
        identifier: IntOrFQ,
    ):
        base_word = Word(base)
        for i, step in enumerate(steps):
            # multiplication gadget
            a, b, d = step[0], step[1], step[2]
            # exp table
            quotient, is_odd = divmod(exponent, 2)
            exponent_word = Word(exponent)
            self._append_step(
                identifier,
                FQ(1 if i == len(steps) - 1 else 0),
                base_word,
                exponent_word,
                Word(d),
                Word(a),
                Word(b),
                Word(0),
                Word(d),
                Word(quotient),
                FQ(is_odd),
            )
            if is_odd == 0:
                # exponent is even
                exponent = exponent // 2
            else:
                # exponent is odd
                exponent = exponent - 1

    def fill_dummy_events(self):
        max_exp_rows = self.max_exp_steps * self.OFFSET_INCREMENT
        rows_left = max_exp_rows - len(self.rows)
        for i in range(rows_left):
            self.rows.append(
                ExpCircuitRow(
                    q_usable=FQ.one(),
                    is_step=FQ.zero(),
                    identifier=FQ.zero(),
                    is_last=FQ.zero(),
                    base=Word(1),
                    exponent=Word(1),
                    exponentiation=Word(1),
                    a=Word(1),
                    b=Word(1),
                    c=Word(0),
                    d=Word(1),
                    q=Word(0),
                    r=FQ(1),
                )
            )
        return self

    def _append_step(
        self,
        identifier: IntOrFQ,
        is_last: IntOrFQ,
        base: Word,
        exponent: Word,
        exponentiation: Word,
        a: Word,
        b: Word,
        c: Word,
        d: Word,
        quotient: Word,
        remainder: FQ,
    ):
        self.rows.append(
            ExpCircuitRow(
                q_usable=FQ.one(),
                is_step=FQ.one(),
                identifier=FQ(identifier),
                is_last=FQ(is_last),
                base=base,
                exponent=exponent,
                exponentiation=exponentiation,
                a=a,
                b=b,
                c=c,
                d=d,
                q=quotient,
                r=remainder,
            )
        )


class CopyCircuit:
    rows: List[CopyCircuitRow]
    pad_rows: List[CopyCircuitRow]

    def __init__(self, pad_rows: Optional[List[CopyCircuitRow]] = None) -> None:
        self.rows = []
        self.pad_rows = []
        if pad_rows is not None:
            self.pad_rows = pad_rows

    def table(self) -> Sequence[CopyCircuitRow]:
        return self.rows + self.pad_rows

    def copy(
        self,
        r: FQ,
        rw_dict: RWDictionary,
        src_id: IntOrFQ,
        src_tag: CopyDataTypeTag,
        dst_id: IntOrFQ,
        dst_tag: CopyDataTypeTag,
        src_addr: IntOrFQ,
        src_addr_end: IntOrFQ,
        dst_addr: IntOrFQ,
        copy_length: IntOrFQ,
        src_data: Mapping[IntOrFQ, Union[IntOrFQ, Tuple[IntOrFQ, IntOrFQ]]],
        log_id: int = 0,
    ):
        new_rows: List[CopyCircuitRow] = []
        rlc_acc = FQ.zero()
        for i in range(int(copy_length)):
            if int(src_addr + i) < int(src_addr_end):
                is_pad = False
                assert src_addr + i in src_data, f"Cannot find data at the offset {src_addr+i}"
                value = src_data[src_addr + i]
                if src_tag == CopyDataTypeTag.Bytecode or dst_tag == CopyDataTypeTag.Bytecode:
                    value = cast(Tuple[IntOrFQ, IntOrFQ], value)
                    value, is_code = value
                else:
                    value = cast(IntOrFQ, value)
                    is_code = FQ(0)
                value = FQ(value)
                is_code = FQ(is_code)
            else:
                is_pad = True
                value = FQ(0)
                is_code = FQ(0)

            # read row, because TxLog is write-only, no need to feed log_id in the read row
            self._append_row(
                new_rows,
                rw_dict,
                False,
                i == 0,
                False,
                src_id,
                src_tag,
                src_addr + i,
                value,
                FQ.zero(),  # rlc_acc will be updated later
                is_code,
                is_pad,
                src_addr_end=src_addr_end,
                bytes_left=copy_length - i,
            )

            # write row
            if dst_tag == CopyDataTypeTag.RlcAcc:
                rlc_acc = rlc_acc * r + value
            self._append_row(
                new_rows,
                rw_dict,
                True,
                False,
                i == copy_length - 1,
                dst_id,
                dst_tag,
                dst_addr + i,
                rlc_acc if dst_tag == CopyDataTypeTag.RlcAcc else value,
                FQ.zero(),
                is_code,
                False,
                log_id=log_id,
            )

        # update the rwc_inc_left column
        rw_counter = rw_dict.rw_counter
        new_rows = [
            dataclasses.replace(row, rwc_inc_left=rw_counter - row.rw_counter, rlc_acc=rlc_acc)
            if dst_tag == CopyDataTypeTag.RlcAcc
            else dataclasses.replace(row, rwc_inc_left=rw_counter - row.rw_counter)
            for row in new_rows
        ]
        self.rows.extend(new_rows)
        return self

    def _append_row(
        self,
        rows: MutableSequence[CopyCircuitRow],
        rw_dict: RWDictionary,
        is_write: bool,
        is_first: bool,
        is_last: bool,
        id: Union[int, FQ, Word],
        tag: CopyDataTypeTag,
        addr: IntOrFQ,
        value: IntOrFQ,
        rlc_acc: IntOrFQ,
        is_code: IntOrFQ,
        is_pad: bool,
        src_addr_end: IntOrFQ = FQ(0),
        bytes_left: IntOrFQ = FQ(0),
        log_id: int = 0,
    ):
        if isinstance(id, int):
            id = FQ(id)
        id = WordOrValue(id)
        is_memory = tag == CopyDataTypeTag.Memory
        is_bytecode = tag == CopyDataTypeTag.Bytecode
        is_tx_calldata = tag == CopyDataTypeTag.TxCalldata
        is_tx_log = tag == CopyDataTypeTag.TxLog
        is_rlc_acc = tag == CopyDataTypeTag.RlcAcc
        rw_counter = rw_dict.rw_counter
        if is_memory:
            if is_write:
                rw_dict.memory_write(id.value().expr(), addr, value)
            elif is_pad is False:
                rw_dict.memory_read(id.value().expr(), addr, value)
        elif is_tx_log:
            assert is_write
            rw_dict.tx_log_write(id.value().expr(), log_id, TxLogFieldTag.Data, addr, value)
            addr += (int(TxLogFieldTag.Data) << 32) + (log_id << 48)
        rows.append(
            CopyCircuitRow(
                q_step=FQ(not is_write),
                is_first=FQ(is_first),
                is_last=FQ(is_last),
                id=id,
                tag=FQ(tag),
                addr=FQ(addr),
                src_addr_end=FQ(src_addr_end),
                bytes_left=FQ(bytes_left),
                value=FQ(value),
                rlc_acc=FQ(rlc_acc),
                is_code=FQ(is_code),
                is_pad=FQ(is_pad),
                rw_counter=FQ(rw_counter),
                rwc_inc_left=FQ(0),  # placeholder for now
                is_memory=FQ(is_memory),
                is_bytecode=FQ(is_bytecode),
                is_tx_calldata=FQ(is_tx_calldata),
                is_tx_log=FQ(is_tx_log),
                is_rlc_acc=FQ(is_rlc_acc),
            )
        )
