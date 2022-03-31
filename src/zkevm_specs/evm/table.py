from __future__ import annotations
from typing import Any, List, Mapping, Optional, Sequence, Set, Type, TypeVar, Union
from enum import IntEnum, auto
from itertools import chain, product
from dataclasses import dataclass, field, fields

from ..util import Expression, FQ
from .execution_state import ExecutionState


class FixedTableTag(IntEnum):
    """
    Tag for FixedTable lookup, where the FixedTable is a prebuilt fixed-column
    table.
    """

    Range5 = auto()  # value, 0, 0
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
    ResponsibleOpcode = auto()  # execution_state, opcode, aux

    def table_assignments(self) -> List[FixedTableRow]:
        if self == FixedTableTag.Range5:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(5)]
        if self == FixedTableTag.Range16:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(16)]
        elif self == FixedTableTag.Range32:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(32)]
        elif self == FixedTableTag.Range64:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(64)]
        elif self == FixedTableTag.Range256:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(256)]
        elif self == FixedTableTag.Range512:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(512)]
        elif self == FixedTableTag.Range1024:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(1024)]
        elif self == FixedTableTag.SignByte:
            return [FixedTableRow(FQ(self), FQ(i), FQ((i >> 7) * 0xFF), FQ(0)) for i in range(256)]
        elif self == FixedTableTag.BitwiseAnd:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs & rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseOr:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs | rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseXor:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs ^ rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.ResponsibleOpcode:
            return [
                FixedTableRow(FQ(self), FQ(execution_state), FQ(opcode), FQ(aux))
                for execution_state in list(ExecutionState)
                for opcode, aux in map(
                    lambda pair: pair if isinstance(pair, tuple) else (pair, 0),
                    execution_state.responsible_opcode(),
                )
            ]
        else:
            raise ValueError("Unreacheable")

    def range_table_tag(range: int) -> FixedTableTag:
        if range == 5:
            return FixedTableTag.Range5
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


class BytecodeFieldTag(IntEnum):
    """
    Tag for BytecodeTable lookup.
    """

    Length = 1
    Byte = 2


class RW(IntEnum):
    Read = 0
    Write = 1


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
    TxLog = auto()
    TxReceipt = auto()

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
    IsRoot = auto()
    IsCreate = auto()
    CodeSource = auto()

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
    ProgramCounter = auto()
    StackPointer = auto()
    GasLeft = auto()
    MemorySize = auto()
    StateWriteCounter = auto()


class TxLogFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag TxLog, which is used to index specific
    field of TxLog.
    """

    # The following are write-only data inside a transaction, they will be written in
    # State circuit directly.
    Address = auto()  # address of the contract that generated the event
    Topic = auto()  # list of topics provided by the contract
    Data = auto()  # log data in bytes
    TopicLength = auto()  # topic number, For RLP encoding
    DataLength = auto()  # how many bytes read from memory, For RLP encoding


class TxReceiptFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag TxReceipt, which is used to index specific
    field of TxReceipt.
    """

    # The following are write-only data inside a transaction, they will be written in
    # State circuit directly.
    PostStateOrStatus = auto()  # flag indicates whether if a tx succeed or not
    # the cumulative gas used in the block containing the transaction receipt as of immediately
    # after the transaction has happened.
    CumulativeGasUsed = auto()


class WrongQueryKey(Exception):
    def __init__(self, table_name: str, diff: Set[str]) -> None:
        self.message = f"Lookup {table_name} with invalid keys {diff}"


class LookupUnsatFailure(Exception):
    def __init__(self, table_name: str, inputs: Any) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is unsatisfied on inputs {inputs}"


class LookupAmbiguousFailure(Exception):
    def __init__(self, table_name: str, inputs: Any, matched_rows: Sequence[Any]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is ambiguous on inputs {inputs}, ${len(matched_rows)} matched rows found: {matched_rows}"


class TableRow:
    @classmethod
    def validate_query(cls, table_name: str, query: Mapping[str, Any]):
        names = set([field.name for field in fields(cls)])
        queried = set(query.keys())
        if not queried.issubset(names):
            raise WrongQueryKey(table_name, queried - names)

    def match(self, query: Mapping[str, Expression]) -> bool:
        return all([value.expr() == getattr(self, key).expr() for key, value in query.items()])


@dataclass(frozen=True)
class FixedTableRow(TableRow):
    tag: Expression
    value0: Expression
    value1: Expression = field(default=FQ(0))
    value2: Expression = field(default=FQ(0))


@dataclass(frozen=True)
class BlockTableRow(TableRow):
    field_tag: Expression
    # meaningful only for HistoryHash, will be zero for other tags
    block_number_or_zero: Expression
    value: Expression


@dataclass(frozen=True)
class TxTableRow(TableRow):
    tx_id: Expression
    field_tag: Expression
    # meaningful only for CallData, will be zero for other tags
    call_data_index_or_zero: Expression
    value: Expression


@dataclass(frozen=True)
class BytecodeTableRow(TableRow):
    bytecode_hash: Expression
    field_tag: Expression
    index: Expression
    is_code: Expression
    value: Expression


@dataclass(frozen=True)
class RWTableRow(TableRow):
    rw_counter: Expression
    rw: Expression
    key0: Expression  # RWTableTag
    key1: Expression = field(default=FQ(0))
    key2: Expression = field(default=FQ(0))
    key3: Expression = field(default=FQ(0))
    key4: Expression = field(default=FQ(0))
    value: Expression = field(default=FQ(0))
    value_prev: Expression = field(default=FQ(0))
    aux0: Expression = field(default=FQ(0))
    aux1: Expression = field(default=FQ(0))


class Tables:
    """
    A collection of lookup tables used in EVM circuit.
    """

    fixed_table = set(chain(*[tag.table_assignments() for tag in list(FixedTableTag)]))
    block_table: Set[BlockTableRow]
    tx_table: Set[TxTableRow]
    bytecode_table: Set[BytecodeTableRow]
    rw_table: Set[RWTableRow]

    def __init__(
        self,
        block_table: Set[BlockTableRow],
        tx_table: Set[TxTableRow],
        bytecode_table: Set[BytecodeTableRow],
        rw_table: Union[Set[Sequence[Expression]], Set[RWTableRow]],
    ) -> None:
        self.block_table = block_table
        self.tx_table = tx_table
        self.bytecode_table = bytecode_table
        self.rw_table = set(
            row if isinstance(row, RWTableRow) else RWTableRow(*row)  # type: ignore  # (RWTableRow input args)
            for row in rw_table
        )

    def fixed_lookup(
        self,
        tag: Expression,
        value0: Expression,
        value1: Expression = FQ(0),
        value2: Expression = FQ(0),
    ) -> FixedTableRow:
        query = {
            "tag": tag,
            "value0": value0,
            "value1": value1,
            "value2": value2,
        }
        row = FixedTableRow(tag, value0, value1, value2)
        if row not in self.fixed_table:
            raise LookupUnsatFailure(FixedTableRow.__name__, query)
        return row

    def block_lookup(
        self, field_tag: Expression, block_number: Expression = FQ(0)
    ) -> BlockTableRow:
        query = {"field_tag": field_tag, "block_number_or_zero": block_number}
        return _lookup(BlockTableRow, self.block_table, query)

    def tx_lookup(
        self, tx_id: Expression, field_tag: Expression, call_data_index: Expression = FQ(0)
    ) -> TxTableRow:
        query = {
            "tx_id": tx_id,
            "field_tag": field_tag,
            "call_data_index_or_zero": call_data_index,
        }
        return _lookup(TxTableRow, self.tx_table, query)

    def bytecode_lookup(
        self,
        bytecode_hash: Expression,
        field_tag: Expression,
        index: Expression,
        is_code: Expression = None,
    ) -> BytecodeTableRow:
        query = {
            "bytecode_hash": bytecode_hash,
            "field_tag": field_tag,
            "index": index,
            "is_code": is_code,
        }
        return _lookup(BytecodeTableRow, self.bytecode_table, query)

    def rw_lookup(
        self,
        rw_counter: Expression,
        rw: Expression,
        tag: Expression,
        key1: Expression = None,
        key2: Expression = None,
        key3: Expression = None,
        key4: Expression = None,
        value: Expression = None,
        value_prev: Expression = None,
        aux0: Expression = None,
        aux1: Expression = None,
    ) -> RWTableRow:
        query = {
            "rw_counter": rw_counter,
            "rw": rw,
            "key0": tag,
            "key1": key1,
            "key2": key2,
            "key3": key3,
            "key4": key4,
            "value": value,
            "value_prev": value_prev,
            "aux0": aux0,
            "aux1": aux1,
        }
        return _lookup(RWTableRow, self.rw_table, query)


T = TypeVar("T", bound=TableRow)


def _lookup(
    table_cls: Type[T],
    table: Set[T],
    query: Mapping[str, Optional[Expression]],
) -> T:
    table_name = table_cls.__name__
    table_cls.validate_query(table_name, query)

    matched_rows = [
        row
        for row in table
        # Filter out None values
        if row.match({key: value for key, value in query.items() if value is not None})
    ]

    if len(matched_rows) == 0:
        raise LookupUnsatFailure(table_name, query)
    elif len(matched_rows) > 1:
        raise LookupAmbiguousFailure(table_name, query, matched_rows)

    return matched_rows[0]
