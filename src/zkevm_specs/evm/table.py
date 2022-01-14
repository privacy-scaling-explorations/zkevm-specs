from typing import Sequence, Set, Tuple
from enum import IntEnum, auto

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


class BlockContextFieldTag(IntEnum):
    """
    Tag for BlockTable lookup, where the BlockTable is an instance-column table
    where part of it will be built by verifier.
    We can also merge BlockTable and TxTable together to save columns, but for
    simplicity we keep them separate for now.
    """

    Coinbase = auto()
    GasLimit = auto()
    BlockNumber = auto()
    Time = auto()
    Difficulty = auto()
    BaseFee = auto()
    BlockHash = auto()


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
    TxAccessListStorageSlot = auto()
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
            RWTableTag.TxAccessListStorageSlot,
            RWTableTag.Account,
            RWTableTag.AccountStorage,
        ]

    # For state writes which don't affect future execution before reversion, we
    # don't need to write them with reversion, instead we only need to write
    # them (enable the lookup) when is_persistent is True.
    def write_only_persistent(self) -> bool:
        return self in [
            RWTableTag.TxRefund,
            RWTableTag.AccountDestructed,
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
    RWCounterEndOfReversion = auto()  # to know at which point in the future we should revert
    CallerCallId = auto()  # to know caller's id
    TxId = auto()  # to know tx's id
    Depth = auto()  # to know if call too deep
    CallerAddress = auto()
    CalleeAddress = auto()
    CallDataOffset = auto()
    CallDataLength = auto()
    ReturnDataOffset = auto()  # for callee to set return_data to caller's memeory
    ReturnDataLength = auto()
    Value = auto()
    Result = auto()  # to peek result in the future
    IsPersistent = auto()  # to know if current call is within reverted call or not
    IsStatic = auto()  # to know if state modification is within static call or not

    # The following are used by caller to save its own CallState when it's
    # going to dive into another call, and will be read out to restore caller's
    # CallState in the end by callee.
    # Note that stack and memory could also be included here, but since they
    # need extra constraints on their data format, so we separate them to be
    # different kinds of RWTableTag.
    IsRoot = auto()
    IsCreate = auto()
    OpcodeSource = auto()
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
    fixed_table: Set[Array4] = set(
        [(FixedTableTag.Range16, i, 0, 0) for i in range(16)]
        + [(FixedTableTag.Range32, i, 0, 0) for i in range(32)]
        + [(FixedTableTag.Range64, i, 0, 0) for i in range(64)]
        + [(FixedTableTag.Range256, i, 0, 0) for i in range(256)]
        + [(FixedTableTag.Range512, i, 0, 0) for i in range(512)]
        + [(FixedTableTag.Range1024, i, 0, 0) for i in range(1024)]
        + [(FixedTableTag.SignByte, i, (i & 1) * 0xFF, 0) for i in range(256)]
        + [(FixedTableTag.BitwiseAnd, lhs, rhs, lhs & rhs) for lhs in range(256) for rhs in range(256)]
        + [(FixedTableTag.BitwiseOr, lhs, rhs, lhs | rhs) for lhs in range(256) for rhs in range(256)]
        + [(FixedTableTag.BitwiseXor, lhs, rhs, lhs ^ rhs) for lhs in range(256) for rhs in range(256)]
        + [
            (FixedTableTag.ResponsibleOpcode, execution_state, opcode, 0)
            for execution_state in list(ExecutionState)
            for opcode in execution_state.responsible_opcode()
        ]
        + [(FixedTableTag.InvalidOpcode, opcode, 0, 0) for opcode in invalid_opcodes()]
        + [(FixedTableTag.StateWriteOpcode, opcode, 0, 0) for opcode in state_write_opcodes()]
        + [
            (FixedTableTag.StackUnderflow, opcode, stack_pointer, 0)
            for (opcode, stack_pointer) in stack_underflow_pairs()
        ]
        + [
            (FixedTableTag.StackOverflow, opcode, stack_pointer, 0)
            for (opcode, stack_pointer) in stack_overflow_pairs()
        ]
    )

    # Each row in BlockTable contains:
    # - tag
    # - block_number_or_zero (meaningful only for BlockHash, will be zero for other tags)
    # - value
    block_table: Set[Array3]

    # Each row in TxTable contains:
    # - tx_id
    # - tag
    # - index_or_zero (meaningful only for CallData, will be zero for other tags)
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
