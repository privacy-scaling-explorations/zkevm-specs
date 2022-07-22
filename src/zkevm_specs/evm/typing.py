from __future__ import annotations
from typing import (
    cast,
    Dict,
    Iterator,
    List,
    MutableSequence,
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
    Expression,
    keccak256,
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
    RWTableTag,
    TxContextFieldTag,
    TxLogFieldTag,
    TxReceiptFieldTag,
    TxTableRow,
    CopyDataTypeTag,
    CopyCircuitRow,
    CopyTableRow,
)
from .opcode import get_push_size, Opcode


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
    difficulty: U256
    base_fee: U256

    # Even ChainId is not a block parameter, since all txs of a block are meant
    # to use the same chain_id, we set it as as a block parameter.
    chainid: U256

    # It contains most recent 256 block hashes in history, where the lastest
    # one is at history_hashes[-1].
    history_hashes: Sequence[U256]

    def __init__(
        self,
        coinbase: U160 = U160(0x10),
        gas_limit: U64 = U64(int(15e6)),
        number: U64 = U64(0),
        timestamp: U64 = U64(0),
        difficulty: U256 = U256(0),
        base_fee: U256 = U256(int(1e9)),
        chainid: U256 = U256(0x01),
        history_hashes: Sequence[U256] = [],
    ) -> None:
        assert len(history_hashes) <= min(256, number)

        self.coinbase = coinbase
        self.gas_limit = gas_limit
        self.number = number
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.base_fee = base_fee
        self.chainid = chainid
        self.history_hashes = history_hashes

    def table_assignments(self, randomness: FQ) -> List[BlockTableRow]:
        return [
            BlockTableRow(FQ(BlockContextFieldTag.Coinbase), FQ(0), FQ(self.coinbase)),
            BlockTableRow(FQ(BlockContextFieldTag.GasLimit), FQ(0), FQ(self.gas_limit)),
            BlockTableRow(FQ(BlockContextFieldTag.Number), FQ(0), FQ(self.number)),
            BlockTableRow(FQ(BlockContextFieldTag.Timestamp), FQ(0), FQ(self.timestamp)),
            BlockTableRow(
                FQ(BlockContextFieldTag.Difficulty), FQ(0), RLC(self.difficulty, randomness)
            ),
            BlockTableRow(FQ(BlockContextFieldTag.BaseFee), FQ(0), RLC(self.base_fee, randomness)),
            BlockTableRow(FQ(BlockContextFieldTag.ChainId), FQ(0), RLC(self.chainid, randomness)),
        ] + [
            BlockTableRow(
                FQ(BlockContextFieldTag.HistoryHash),
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
        gas: U64 = U64(21000),
        gas_price: U256 = U256(int(2e9)),
        caller_address: U160 = U160(0),
        callee_address: U160 = None,
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
                TxTableRow(FQ(self.id), FQ(TxContextFieldTag.Nonce), FQ(0), FQ(self.nonce)),
                TxTableRow(FQ(self.id), FQ(TxContextFieldTag.Gas), FQ(0), FQ(self.gas)),
                TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.GasPrice),
                    FQ(0),
                    RLC(self.gas_price, randomness),
                ),
                TxTableRow(
                    FQ(self.id), FQ(TxContextFieldTag.CallerAddress), FQ(0), FQ(self.caller_address)
                ),
                TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.CalleeAddress),
                    FQ(0),
                    FQ(0 if self.callee_address is None else self.callee_address),
                ),
                TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.IsCreate),
                    FQ(0),
                    FQ(self.callee_address is None),
                ),
                TxTableRow(
                    FQ(self.id), FQ(TxContextFieldTag.Value), FQ(0), RLC(self.value, randomness)
                ),
                TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.CallDataLength),
                    FQ(0),
                    FQ(len(self.call_data)),
                ),
                TxTableRow(
                    FQ(self.id),
                    FQ(TxContextFieldTag.CallDataGasCost),
                    FQ(0),
                    FQ(self.call_data_gas_cost()),
                ),
            ],
            map(
                lambda item: TxTableRow(
                    FQ(self.id), FQ(TxContextFieldTag.CallData), FQ(item[0]), FQ(item[1])
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
                self.is_code.append(True)
            else:
                assert len(args) <= 1024 - opcode.max_stack_pointer()
                for arg in reversed(args):
                    self.push(arg, 32)
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
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            ...
        else:
            raise NotImplementedError(f"Value of type {type(value)} is not yet supported")

        assert 0 < len(value) <= n_bytes, ValueError("Too many bytes as data portion of PUSH*")

        opcode = Opcode.PUSH1 + n_bytes - 1
        self.code.append(opcode)
        self.is_code.append(True)
        self.code.extend(value.rjust(n_bytes, b"\x00"))
        self.is_code.extend([False] * n_bytes)

        return self

    def hash(self) -> U256:
        return U256(int.from_bytes(keccak256(self.code), "big"))

    def table_assignments(self, randomness: FQ) -> Iterator[BytecodeTableRow]:
        class BytecodeIterator:
            idx: int
            hash: FQ
            code: bytes
            is_code: Sequence[bool]

            def __init__(self, hash: FQ, code: bytes, is_code: Sequence[bool]):
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
                        self.hash, FQ(BytecodeFieldTag.Length), FQ(0), FQ(0), FQ(len(self.code))
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

        return BytecodeIterator(RLC(self.hash(), randomness).expr(), self.code, self.is_code)


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
        code: Bytecode = None,
        storage: Storage = None,
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

    def stack_read(self, call_id: IntOrFQ, stack_pointer: IntOrFQ, value: RLC) -> RWDictionary:
        return self._append(
            RW.Read, RWTableTag.Stack, key1=FQ(call_id), key2=FQ(stack_pointer), value=value
        )

    def stack_write(self, call_id: IntOrFQ, stack_pointer: IntOrFQ, value: RLC) -> RWDictionary:
        return self._append(
            RW.Write, RWTableTag.Stack, key1=FQ(call_id), key2=FQ(stack_pointer), value=value
        )

    def memory_read(self, call_id: IntOrFQ, memory_address: IntOrFQ, byte: IntOrFQ) -> RWDictionary:
        return self._append(
            RW.Read, RWTableTag.Memory, key1=FQ(call_id), key2=FQ(memory_address), value=FQ(byte)
        )

    def memory_write(
        self, call_id: IntOrFQ, memory_address: IntOrFQ, byte: IntOrFQ
    ) -> RWDictionary:
        return self._append(
            RW.Write, RWTableTag.Memory, key1=FQ(call_id), key2=FQ(memory_address), value=FQ(byte)
        )

    def call_context_read(
        self, call_id: IntOrFQ, field_tag: CallContextFieldTag, value: Union[int, FQ, RLC]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Read, RWTableTag.CallContext, key1=FQ(call_id), key2=FQ(field_tag), value=value
        )

    def call_context_write(
        self, call_id: IntOrFQ, field_tag: CallContextFieldTag, value: Union[int, FQ, RLC]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Write, RWTableTag.CallContext, key1=FQ(call_id), key2=FQ(field_tag), value=value
        )

    def tx_log_write(
        self,
        tx_id: IntOrFQ,
        log_id: int,
        field_tag: TxLogFieldTag,
        index: IntOrFQ,
        value: Union[int, FQ, RLC],
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Write,
            RWTableTag.TxLog,
            key1=FQ(tx_id),
            key2=FQ(index + (int(field_tag) << 32) + (log_id << 48)),
            key3=FQ(0),
            key4=FQ(0),
            value=value,
        )

    def tx_receipt_read(
        self,
        tx_id: IntOrFQ,
        field_tag: TxReceiptFieldTag,
        value: Union[int, FQ, RLC],
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Read,
            RWTableTag.TxReceipt,
            key1=FQ(tx_id),
            key3=FQ(field_tag),
            value=value,
        )

    def tx_receipt_write(
        self,
        tx_id: IntOrFQ,
        field_tag: TxReceiptFieldTag,
        value: Union[int, FQ, RLC],
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Write,
            RWTableTag.TxReceipt,
            key1=FQ(tx_id),
            key3=FQ(field_tag),
            value=value,
        )

    def tx_refund_read(self, tx_id: IntOrFQ, refund: IntOrFQ) -> RWDictionary:
        return self._append(
            RW.Read, RWTableTag.TxRefund, key1=FQ(tx_id), value=FQ(refund), value_prev=FQ(refund)
        )

    def tx_refund_write(
        self,
        tx_id: IntOrFQ,
        refund: IntOrFQ,
        refund_prev: IntOrFQ,
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        return self._state_write(
            RWTableTag.TxRefund,
            key1=FQ(tx_id),
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
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        return self._state_write(
            RWTableTag.TxAccessListAccount,
            key1=FQ(tx_id),
            key2=FQ(account_address),
            value=FQ(value),
            value_prev=FQ(value_prev),
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def tx_access_list_account_storage_write(
        self,
        tx_id: IntOrFQ,
        account_address: IntOrFQ,
        storage_key: RLC,
        value: bool,
        value_prev: bool,
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        return self._state_write(
            RWTableTag.TxAccessListAccountStorage,
            key1=FQ(tx_id),
            key2=FQ(account_address),
            key3=storage_key,
            value=FQ(value),
            value_prev=FQ(value_prev),
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def account_read(
        self, account_address: IntOrFQ, field_tag: AccountFieldTag, value: Union[int, FQ, RLC]
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        return self._append(
            RW.Read,
            RWTableTag.Account,
            key2=FQ(account_address),
            key3=FQ(field_tag),
            value=value,
            value_prev=value,
        )

    def account_write(
        self,
        account_address: IntOrFQ,
        field_tag: AccountFieldTag,
        value: Union[int, FQ, RLC],
        value_prev: Union[int, FQ, RLC],
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        if isinstance(value, int):
            value = FQ(value)
        if isinstance(value_prev, int):
            value_prev = FQ(value_prev)
        return self._state_write(
            RWTableTag.Account,
            key2=FQ(account_address),
            key3=FQ(field_tag),
            value=value,
            value_prev=value_prev,
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def account_storage_read(
        self,
        account_address: IntOrFQ,
        storage_key: RLC,
        value: RLC,
        tx_id: IntOrFQ,
        value_committed: RLC,
    ) -> RWDictionary:
        if isinstance(tx_id, int):
            tx_id = FQ(tx_id)
        return self._append(
            RW.Read,
            RWTableTag.AccountStorage,
            key1=tx_id,
            key2=FQ(account_address),
            key4=storage_key,
            value=value,
            value_prev=value,
            aux0=value_committed,
        )

    def account_storage_write(
        self,
        account_address: IntOrFQ,
        storage_key: RLC,
        value: RLC,
        value_prev: RLC,
        tx_id: IntOrFQ,
        value_committed: RLC,
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        if isinstance(tx_id, int):
            tx_id = FQ(tx_id)
        return self._state_write(
            RWTableTag.AccountStorage,
            key1=tx_id,
            key2=FQ(account_address),
            key4=storage_key,
            value=value,
            value_prev=value_prev,
            aux0=value_committed,
            rw_counter_of_reversion=rw_counter_of_reversion,
        )

    def _state_write(
        self,
        tag: RWTableTag,
        key1: Expression = FQ(0),
        key2: Expression = FQ(0),
        key3: Expression = FQ(0),
        key4: Expression = FQ(0),
        value: Expression = FQ(0),
        value_prev: Expression = FQ(0),
        aux0: Expression = FQ(0),
        rw_counter_of_reversion: int = None,
    ) -> RWDictionary:
        self._append(
            RW.Write,
            tag=tag,
            key1=key1,
            key2=key2,
            key3=key3,
            key4=key4,
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
                key1=key1,
                key2=key2,
                key3=key3,
                key4=key4,
                value=value_prev,
                value_prev=value,
                aux0=aux0,
                rw_counter=rw_counter_of_reversion,
            )

    def _append(
        self,
        rw: RW,
        tag: RWTableTag,
        key1: Expression = FQ(0),
        key2: Expression = FQ(0),
        key3: Expression = FQ(0),
        key4: Expression = FQ(0),
        value: Expression = FQ(0),
        value_prev: Expression = FQ(0),
        aux0: Expression = FQ(0),
        rw_counter: int = None,
    ) -> RWDictionary:
        if rw_counter is None:
            rw_counter = self.rw_counter
            self.rw_counter += 1

        self.rws.append(
            RWTableRow(
                FQ(rw_counter),
                FQ(rw),
                FQ(tag),
                key1,
                key2,
                key3,
                key4,
                value,
                value_prev,
                aux0,
            )
        )

        return self


class CopyCircuit:
    rows: List[CopyCircuitRow]
    pad_rows: List[CopyCircuitRow]

    def __init__(self) -> None:
        self.rows = []
        self.pad_rows = [CopyCircuitRow(FQ(1), *[FQ(0)] * 17), CopyCircuitRow(*[FQ(0)] * 18)]

    def table(self) -> Sequence[CopyCircuitRow]:
        return self.rows + self.pad_rows

    def copy(
        self,
        rw_dict: RWDictionary,
        src_id: IntOrFQ,
        src_type: CopyDataTypeTag,
        dst_id: IntOrFQ,
        dst_type: CopyDataTypeTag,
        src_addr: IntOrFQ,
        src_addr_end: IntOrFQ,
        dst_addr: IntOrFQ,
        copy_length: IntOrFQ,
        src_data: Mapping[IntOrFQ, Union[IntOrFQ, Tuple[IntOrFQ, IntOrFQ]]],
        log_id: int = 0,
    ):
        new_rows: List[CopyCircuitRow] = []
        acc_val = FQ(0)
        for i in range(int(copy_length)):
            if int(src_addr + i) < int(src_addr_end):
                is_pad = False
                assert src_addr + i in src_data, f"Cannot find data at the offset {src_addr+i}"
                value = src_data[src_addr + i]
                if src_type == CopyDataTypeTag.Bytecode:
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
                src_type,
                src_addr + i,
                value,
                is_code,
                is_pad,
                src_addr_end=src_addr_end,
                bytes_left=copy_length - i,
            )

            # write row
            if dst_type == CopyDataTypeTag.RlcAcc:
                acc_val += value
            self._append_row(
                new_rows,
                rw_dict,
                True,
                False,
                i == copy_length - 1,
                dst_id,
                dst_type,
                dst_addr + i,
                acc_val if dst_type == CopyDataTypeTag.RlcAcc else value,
                is_code,
                False,
                log_id=log_id,
            )

        # update the rwc_inc_left column
        rw_counter = rw_dict.rw_counter
        for row in new_rows:
            row.rwc_inc_left = rw_counter - row.rw_counter
        self.rows.extend(new_rows)
        return self

    def _append_row(
        self,
        rows: MutableSequence[CopyCircuitRow],
        rw_dict: RWDictionary,
        is_write: bool,
        is_first: bool,
        is_last: bool,
        id: IntOrFQ,
        tag: CopyDataTypeTag,
        addr: IntOrFQ,
        value: IntOrFQ,
        is_code: IntOrFQ,
        is_pad: bool,
        src_addr_end: IntOrFQ = FQ(0),
        bytes_left: IntOrFQ = FQ(0),
        log_id: int = 0,
    ):
        is_memory = tag == CopyDataTypeTag.Memory
        is_bytecode = tag == CopyDataTypeTag.Bytecode
        is_tx_calldata = tag == CopyDataTypeTag.TxCalldata
        is_tx_log = tag == CopyDataTypeTag.TxLog
        is_rlc_acc = tag == CopyDataTypeTag.RlcAcc
        rw_counter = rw_dict.rw_counter
        if is_memory:
            if is_write:
                rw_dict.memory_write(id, addr, value)
            else:
                rw_dict.memory_read(id, addr, value)
        elif is_tx_log:
            assert is_write
            rw_dict.tx_log_write(id, log_id, TxLogFieldTag.Data, addr, value)
            addr += (int(TxLogFieldTag.Data) << 32) + (log_id << 48)
        rows.append(
            CopyCircuitRow(
                q_step=FQ(not is_write),
                is_first=FQ(is_first),
                is_last=FQ(is_last),
                id=FQ(id),
                tag=FQ(tag),
                addr=FQ(addr),
                src_addr_end=FQ(src_addr_end),
                bytes_left=FQ(bytes_left),
                value=FQ(value),
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
