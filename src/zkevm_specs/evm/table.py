from __future__ import annotations
from typing import Sequence, Set, Tuple
from enum import IntEnum, auto
from itertools import chain, product

from ..util import Array3, Array4, Array10
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

    def table_assignments(self) -> Sequence[Array4]:
        if self == FixedTableTag.Range16:
            return [(self, i, 0, 0) for i in range(16)]
        elif self == FixedTableTag.Range32:
            return [(self, i, 0, 0) for i in range(32)]
        elif self == FixedTableTag.Range64:
            return [(self, i, 0, 0) for i in range(64)]
        elif self == FixedTableTag.Range256:
            return [(self, i, 0, 0) for i in range(256)]
        elif self == FixedTableTag.Range512:
            return [(self, i, 0, 0) for i in range(512)]
        elif self == FixedTableTag.Range1024:
            return [(self, i, 0, 0) for i in range(1024)]
        elif self == FixedTableTag.SignByte:
            return [(self, i, (i >> 7) * 0xFF, 0) for i in range(256)]
        elif self == FixedTableTag.BitwiseAnd:
            return [(self, lhs, rhs, lhs & rhs) for lhs, rhs in product(range(256), range(256))]
        elif self == FixedTableTag.BitwiseOr:
            return [(self, lhs, rhs, lhs | rhs) for lhs, rhs in product(range(256), range(256))]
        elif self == FixedTableTag.BitwiseXor:
            return [(self, lhs, rhs, lhs ^ rhs) for lhs, rhs in product(range(256), range(256))]
        elif self == FixedTableTag.ResponsibleOpcode:
            return [
                (self, execution_state, opcode, 0)
                for execution_state in list(ExecutionState)
                for opcode in execution_state.responsible_opcode()
            ]
        elif self == FixedTableTag.InvalidOpcode:
            return [(self, opcode, 0, 0) for opcode in invalid_opcodes()]
        elif self == FixedTableTag.StateWriteOpcode:
            return [(self, opcode, 0, 0) for opcode in state_write_opcodes()]
        elif self == FixedTableTag.StackOverflow:
            return [(self, opcode, stack_pointer, 0) for opcode, stack_pointer in stack_underflow_pairs()]
        elif self == FixedTableTag.StackUnderflow:
            return [(self, opcode, stack_pointer, 0) for opcode, stack_pointer in stack_overflow_pairs()]
        else:
            ValueError("Unreacheable")

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


class RW:
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


class LookupUnsatFailure(Exception):
    def __init__(self, table_name: str, inputs: Tuple[int, ...]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is unsatisfied on inputs {inputs}"


class LookupAmbiguousFailure(Exception):
    def __init__(self, table_name: str, inputs: Tuple[int, ...], matched_rows: Sequence[Tuple[int, ...]]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is ambiguous on inputs {inputs}, ${len(matched_rows)} matched rows found: {matched_rows}"


class Tables:
    """
    A collection of lookup tables used in EVM circuit.
    """

    _: Placeholder = Placeholder()

    # Each row in FixedTable contains:
    # - tag
    # - value1
    # - value2
    # - value3
    fixed_table: Set[Array4] = set(chain(*[tag.table_assignments() for tag in list(FixedTableTag)]))

    # Each row in BlockTable contains:
    # - tag
    # - block_number_or_zero (meaningful only for HistoryHash, will be zero for other tags)
    # - value
    block_table: Set[Array3]

    # Each row in TxTable contains:
    # - tx_id
    # - tag
    # - call_data_index_or_zero (meaningful only for CallData, will be zero for other tags)
    # - value
    tx_table: Set[Array4]

    # Each row in BytecodeTable contains:
    # - bytecode_hash
    # - index
    # - byte
    # - is_code
    bytecode_table: Set[Array4]

    # Each row in RWTable contains:
    # - rw_counter
    # - is_write
    # - key1 (tag)
    # - key2
    # - key3
    # - key4
    # - value
    # - value_prev
    # - aux1
    # - aux2
    rw_table: Set[Array10]

    def __init__(
        self,
        block_table: Set[Array3],
        tx_table: Set[Array4],
        bytecode_table: Set[Array4],
        rw_table: Set[Array10],
    ) -> None:
        self.block_table = block_table
        self.tx_table = tx_table
        self.bytecode_table = bytecode_table
        self.rw_table = rw_table

    def fixed_lookup(self, inputs: Sequence[int]) -> Array4:
        assert len(inputs) <= 4
        return _lookup("fixed_table", self.fixed_table, inputs)

    def block_lookup(self, inputs: Sequence[int]) -> Array3:
        assert len(inputs) <= 3
        return _lookup("block_table", self.block_table, inputs)

    def tx_lookup(self, inputs: Sequence[int]) -> Array4:
        assert len(inputs) <= 4
        return _lookup("tx_table", self.tx_table, inputs)

    def bytecode_lookup(self, inputs: Sequence[int]) -> Array4:
        assert len(inputs) <= 4
        return _lookup("bytecode_table", self.bytecode_table, inputs)

    def rw_lookup(self, inputs: Sequence[int]) -> Array10:
        assert len(inputs) <= 10
        return _lookup("rw_table", self.rw_table, inputs)


def _lookup(
    table_name: str,
    table: Set[Tuple[int, ...]],
    inputs: Sequence[int],
) -> Tuple[int, ...]:
    inputs = tuple(inputs)
    inputs_len = len(inputs)
    matched_rows = []

    for row in table:
        if inputs == row[:inputs_len]:
            matched_rows.append(row)

    if len(matched_rows) == 0:
        raise LookupUnsatFailure(table_name, inputs)
    elif len(matched_rows) > 1:
        raise LookupAmbiguousFailure(table_name, inputs, matched_rows)

    return matched_rows[0]
