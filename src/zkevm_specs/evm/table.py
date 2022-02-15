from __future__ import annotations
from typing import Mapping, Sequence, Set, List, TypeVar, Any, Type, Optional, Dict
from enum import IntEnum, auto, Enum
from itertools import chain, product
from dataclasses import dataclass, field, asdict, fields


from ..util import FQ, IntOrFQ
from .execution_state import ExecutionState
from .opcode import (
    invalid_opcodes,
    state_write_opcodes,
    stack_underflow_pairs,
    stack_overflow_pairs,
)


class Placeholder:
    def __eq__(self, _) -> bool:
        return True


class FixedTableTag(IntEnum):
    """
    Tag for FixedTable lookup, where the FixedTable is a prebuilt fixed-column
    table.
    """

    Range16 = auto()  # value, 0, 0
    Range32 = auto()  # value, 0, 0
    Range64 = auto()  # value, 0, 0
    Range256 = auto()  # value, 0, 0
    Range512 = auto()  # value, 0, 0
    Range1024 = auto()  # value, 0, 0
    SignByte = auto()  # value, signbyte, 0
    BitwiseAnd = auto()  # lhs, rhs, lhs & rhs, 0
    BitwiseOr = auto()  # lhs, rhs, lhs | rhs, 0
    BitwiseXor = auto()  # lhs, rhs, lhs ^ rhs, 0
    ResponsibleOpcode = auto()  # execution_state, opcode, 0
    InvalidOpcode = auto()  # opcode, 0, 0
    StateWriteOpcode = auto()  # opcode, 0, 0
    StackOverflow = auto()  # opcode, stack_pointer, 0
    StackUnderflow = auto()  # opcode, stack_pointer, 0

    def table_assignments(self) -> List[FixedTableRow]:
        if self == FixedTableTag.Range16:
            return [FixedTableRow(self, FQ(i)) for i in range(16)]
        elif self == FixedTableTag.Range32:
            return [FixedTableRow(self, FQ(i)) for i in range(32)]
        elif self == FixedTableTag.Range64:
            return [FixedTableRow(self, FQ(i)) for i in range(64)]
        elif self == FixedTableTag.Range256:
            return [FixedTableRow(self, FQ(i)) for i in range(256)]
        elif self == FixedTableTag.Range512:
            return [FixedTableRow(self, FQ(i)) for i in range(512)]
        elif self == FixedTableTag.Range1024:
            return [FixedTableRow(self, FQ(i)) for i in range(1024)]
        elif self == FixedTableTag.SignByte:
            return [FixedTableRow(self, FQ(i), FQ((i >> 7) * 0xFF)) for i in range(256)]
        elif self == FixedTableTag.BitwiseAnd:
            return [
                FixedTableRow(self, FQ(lhs), FQ(rhs), FQ(lhs & rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseOr:
            return [
                FixedTableRow(self, FQ(lhs), FQ(rhs), FQ(lhs | rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseXor:
            return [
                FixedTableRow(self, FQ(lhs), FQ(rhs), FQ(lhs ^ rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.ResponsibleOpcode:
            return [
                FixedTableRow(self, FQ(execution_state), FQ(opcode))
                for execution_state in list(ExecutionState)
                for opcode in execution_state.responsible_opcode()
            ]
        elif self == FixedTableTag.InvalidOpcode:
            return [FixedTableRow(self, FQ(opcode)) for opcode in invalid_opcodes()]
        elif self == FixedTableTag.StateWriteOpcode:
            return [FixedTableRow(self, FQ(opcode)) for opcode in state_write_opcodes()]
        elif self == FixedTableTag.StackOverflow:
            return [
                FixedTableRow(self, FQ(opcode), FQ(stack_pointer))
                for opcode, stack_pointer in stack_underflow_pairs()
            ]
        elif self == FixedTableTag.StackUnderflow:
            return [
                FixedTableRow(self, FQ(opcode), FQ(stack_pointer))
                for opcode, stack_pointer in stack_overflow_pairs()
            ]
        else:
            raise ValueError("Unreacheable")

    def range_table_tag(range: int) -> FixedTableTag:
        if range == 16:
            return FixedTableTag.Range16
        elif range == 32:
            return FixedTableTag.Range32
        elif range == 64:
            return FixedTableTag.Range64
        elif range == 256:
            return FixedTableTag.Range256
        elif range == 512:
            return FixedTableTag.Range512
        elif range == 1024:
            return FixedTableTag.Range1024
        else:
            raise ValueError(
                f"Range {range} lookup is not supported yet, please add a new variant Range{range} in FixedTableTag with proper table assignments"
            )


class BlockContextFieldTag(IntEnum):
    """
    Tag for BlockTable lookup, where the BlockTable is an instance-column table
    where part of it will be built by verifier.
    We can also merge BlockTable and TxTable together to save columns, but for
    simplicity we keep them separate for now.
    """

    Coinbase = auto()
    GasLimit = auto()
    Number = auto()
    Timestamp = auto()
    Difficulty = auto()
    BaseFee = auto()
    HistoryHash = auto()


class TxContextFieldTag(IntEnum):
    """
    Tag for TxTable lookup, where the TxTable is an instance-column table where
    part of it will be built by verifier.
    Note that the field here is targeting legacy transaction format, supporting
    of EIP1559 is deferred to future work.
    """

    Nonce = auto()
    Gas = auto()
    GasPrice = auto()
    CallerAddress = auto()
    CalleeAddress = auto()
    IsCreate = auto()
    Value = auto()
    CallDataLength = auto()
    CallDataGasCost = auto()
    CallData = auto()


class RW(Enum):
    Read = False
    Write = True


class RWTableTag(IntEnum):
    """
    Tag for RWTable lookup, where the RWTable an advice-column table built by
    prover, which will be part of State circuit and each unit read-write data
    will be verified to be consistent between each write.
    """

    TxAccessListAccount = auto()
    TxAccessListAccountStorage = auto()
    TxRefund = auto()

    Account = auto()
    AccountStorage = auto()
    AccountDestructed = auto()

    CallContext = auto()
    Stack = auto()
    Memory = auto()

    # For state writes which affect future execution before reversion, we need
    # to write them with reversion when the write might fail.
    def write_with_reversion(self) -> bool:
        return self in [
            RWTableTag.TxAccessListAccount,
            RWTableTag.TxAccessListAccountStorage,
            RWTableTag.Account,
            RWTableTag.AccountStorage,
            RWTableTag.AccountDestructed,
            RWTableTag.TxRefund,
        ]


class AccountFieldTag(IntEnum):
    Nonce = auto()
    Balance = auto()
    CodeHash = auto()


class CallContextFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag CallContext, which is used to index specific
    field of CallContext.
    """

    # The following are read-only data inside a call, they will be written in
    # State circuit directly in their first row, and most of them will be
    # read and checked to be agreed with caller before the beginning of call.
    # It's not like transaction or bytecode that require specifically friendly
    # layout for verification, so maintaining the consistency directly in
    # RWTable seems more intuitive than creating another table for it.
    RwCounterEndOfReversion = auto()  # to know at which point in the future we should revert
    CallerId = auto()  # to know caller's id
    TxId = auto()  # to know tx's id
    Depth = auto()  # to know if call too deep
    CallerAddress = auto()
    CalleeAddress = auto()
    CallDataOffset = auto()
    CallDataLength = auto()
    ReturnDataOffset = auto()  # for callee to set return_data to caller's memeory
    ReturnDataLength = auto()
    Value = auto()
    IsSuccess = auto()  # to peek result in the future
    IsPersistent = auto()  # to know if current call is within reverted call or not
    IsStatic = auto()  # to know if state modification is within static call or not

    # The following are read-only data inside a call like previous section for
    # opcode RETURNDATASIZE and RETURNDATACOPY, except they will be updated when
    # end of callee execution.
    LastCalleeId = auto()
    LastCalleeReturnDataOffset = auto()
    LastCalleeReturnDataLength = auto()

    # The following are used by caller to save its own CallState when it's
    # going to dive into another call, and will be read out to restore caller's
    # CallState in the end by callee.
    # Note that stack and memory could also be included here, but since they
    # need extra constraints on their data format, so we separate them to be
    # different kinds of RWTableTag.
    IsRoot = auto()
    IsCreate = auto()
    CodeSource = auto()
    ProgramCounter = auto()
    StackPointer = auto()
    GasLeft = auto()
    MemorySize = auto()
    StateWriteCounter = auto()


class WrongQueryKey(Exception):
    def __init__(self, table_name: str, diff: Set[str]) -> None:
        self.message = f"Lookup {table_name} with invalid keys {diff}"


class LookupUnsatFailure(Exception):
    def __init__(self, table_name: str, inputs: Tuple[int, ...]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is unsatisfied on inputs {inputs}"


class LookupAmbiguousFailure(Exception):
    def __init__(self, table_name: str, inputs: Tuple[int, ...], matched_rows: Sequence[Any]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is ambiguous on inputs {inputs}, ${len(matched_rows)} matched rows found: {matched_rows}"


class TableRow:
    @classmethod
    def validate_query(cls, table_name: str, query: Mapping[str, Any]):
        names = set([field.name for field in fields(cls)])
        queried = set(query.keys())
        if not queried.issubset(names):
            raise WrongQueryKey(table_name, queried - names)

    def match(self, query: Mapping[str, Any]) -> bool:
        kv = asdict(self)
        return all([int(kv[key]) == int(value) for key, value in query.items()])


@dataclass(frozen=True)
class FixedTableRow(TableRow):
    tag: FixedTableTag
    value1: FQ
    value2: FQ = field(default=FQ(0))
    value3: FQ = field(default=FQ(0))


@dataclass(frozen=True)
class BlockTableRow(TableRow):
    tag: BlockContextFieldTag
    # meaningful only for HistoryHash, will be zero for other tags
    block_number_or_zero: FQ
    value: FQ


@dataclass(frozen=True)
class TxTableRow(TableRow):
    tx_id: FQ
    tag: TxContextFieldTag
    # meaningful only for CallData, will be zero for other tags
    call_data_index_or_zero: FQ
    value: FQ


@dataclass(frozen=True)
class BytecodeTableRow(TableRow):
    bytecode_hash: FQ
    index: FQ
    byte: FQ
    is_code: FQ


@dataclass(frozen=True)
class RWTableRow(TableRow):
    rw_counter: FQ
    is_write: FQ
    # key1 is also the tag
    key1: RWTableTag
    key2: FQ
    key3: FQ
    key4: FQ
    value: FQ
    value_prev: FQ
    aux1: FQ
    aux2: FQ


class Tables:
    """
    A collection of lookup tables used in EVM circuit.
    """

    _: Placeholder = Placeholder()

    fixed_table: Set[FixedTableRow] = set(
        chain(*[tag.table_assignments() for tag in list(FixedTableTag)])
    )
    block_table: Set[BlockTableRow]
    tx_table: Set[TxTableRow]
    bytecode_table: Set[BytecodeTableRow]
    rw_table: Set[RWTableRow]

    def __init__(
        self,
        block_table: Set[BlockTableRow],
        tx_table: Set[TxTableRow],
        bytecode_table: Set[BytecodeTableRow],
        rw_table: Set[RWTableRow],
    ) -> None:
        self.block_table = block_table
        self.tx_table = tx_table
        self.bytecode_table = bytecode_table
        self.rw_table = rw_table

    def fixed_lookup(
        self, tag: FixedTableTag, value1: FQ, value2: FQ = None, value3: FQ = None
    ) -> FixedTableRow:
        query: Dict[str, Optional[IntOrFQ]] = {
            "tag": tag,
            "value1": value1,
            "value2": value2,
            "value3": value3,
        }
        return _lookup(FixedTableRow, self.fixed_table, query)

    def block_lookup(self, tag: BlockContextFieldTag, index: FQ = FQ(0)) -> BlockTableRow:
        query: Dict[str, Optional[IntOrFQ]] = {"tag": tag, "block_number_or_zero": index}
        return _lookup(BlockTableRow, self.block_table, query)

    def tx_lookup(self, tx_id: int, field_tag: TxContextFieldTag, index: FQ) -> TxTableRow:
        query: Dict[str, Optional[IntOrFQ]] = {"tx_id": tx_id, "tag": field_tag, "call_data_index_or_zero": index}
        return _lookup(TxTableRow, self.tx_table, query)

    def bytecode_lookup(self, bytecode_hash: FQ, index: FQ, is_code: FQ) -> BytecodeTableRow:
        query: Dict[str, Optional[IntOrFQ]] = {
            "bytecode_hash": bytecode_hash,
            "index": index,
            "is_code": is_code,
        }
        return _lookup(BytecodeTableRow, self.bytecode_table, query)

    def rw_lookup(self, rw_counter: FQ, rw: RW, tag: RWTableTag, **other_queries: IntOrFQ) -> RWTableRow:
        query: Dict[str, Optional[IntOrFQ]] = {"rw_counter": rw_counter, "rw": int(rw.value), "tag": tag, **other_queries}
        return _lookup(RWTableRow, self.rw_table, query)


T = TypeVar("T", bound=TableRow)


def _lookup(
    table_cls: Type[T],
    table: Set[T],
    query: Mapping[str, Optional[IntOrFQ]],
) -> T:
    # cleanup none value
    query = {k: v for k, v in query.items() if v is not None}

    table_name = table_cls.__name__
    table_cls.validate_query(table_name, query)

    matched_rows = [row for row in table if row.match(query)]

    if len(matched_rows) == 0:
        raise LookupUnsatFailure(table_name, query)
    elif len(matched_rows) > 1:
        raise LookupAmbiguousFailure(table_name, query, matched_rows)

    return matched_rows[0]
