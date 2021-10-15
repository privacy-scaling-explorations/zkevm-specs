from enum import IntEnum, auto
from typing import Any, Sequence, Set, Tuple, Union
from sha3 import keccak_256

FQ = 21888242871839275222246405745257275088548364400416034343698204186575808495617
EMPTY_CODE_HASH = bytearray.fromhex(
    'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')


class FixedTableTag(IntEnum):
    Range32 = auto()  # value, 0, 0
    Range64 = auto()  # value, 0, 0
    Range256 = auto()  # value, 0, 0
    Range512 = auto()  # value, 0, 0
    Range1024 = auto()  # value, 0, 0
    InvalidOpcode = auto()  # opcode, 0, 0
    StackUnderflow = auto()  # opcode, stack_pointer, 0
    StackOverflow = auto()  # opcode, stack_pointer, 0


class TxTableTag(IntEnum):
    Nonce = auto()
    Gas = auto()
    GasTipCap = auto()
    GasFeeCap = auto()
    CallerAddress = auto()
    CalleeAddress = auto()
    IsCreate = auto()
    Value = auto()
    CalldataLength = auto()
    Calldata = auto()


class CallTableTag(IntEnum):
    RWCounterEndOfRevert = auto()  # to know reversion section
    CallerCallId = auto()  # to return to caller's state
    TxId = auto()  # to lookup tx context
    Depth = auto()  # to know if call too deep
    CallerAddress = auto()
    CalleeAddress = auto()
    CalldataOffset = auto()
    CalldataLength = auto()
    ReturndataOffset = auto()  # for callee to set returndata to caller's memeory
    ReturndataLength = auto()
    Value = auto()
    Result = auto()  # to peek result in the future
    IsPersistent = auto()  # to know if current call is within reverted call or not
    IsStatic = auto()  # to know if state modification is within static call or not


class RWTableTag(IntEnum):
    TxAccessListAccount = auto()
    TxAccessListStorageSlot = auto()
    TxRefund = auto()
    CallState = auto()
    Stack = auto()
    Memory = auto()
    AccountNonce = auto()
    AccountBalance = auto()
    AccountCodeHash = auto()
    AccountStorage = auto()
    AccountSelfDestructed = auto()


class CallStateTag(IntEnum):
    IsRoot = auto()
    IsCreate = auto()
    ProgramCounter = auto()
    OpcodeSource = auto()
    StackPointer = auto()
    GasLeft = auto()
    MemorySize = auto()
    StateWriteCounter = auto()


class Tables:
    fixed_table: Set[Tuple[
        int,  # tag
        int,  # value1
        int,  # value2
        int,  # value3
    ]]
    tx_table: Set[Tuple[
        int,  # tx_id
        int,  # tag
        int,  # index (or 0)
        int,  # value
    ]]
    call_table: Set[Tuple[
        int,  # call_id
        int,  # tag
        int,  # value
    ]]
    bytecode_table: Set[Tuple[
        int,  # bytecode_hash
        int,  # index
        int,  # byte
    ]]
    rw_table: Set[Tuple[
        int,  # rw_counter
        int,  # is_write
        int,  # tag
        int,  # value1
        int,  # value2
        int,  # value3
        int,  # value4
        int,  # value5
    ]]

    def __init__(
        self,
        fixed_table,
        tx_table,
        call_table,
        bytecode_table,
        rw_table,
    ) -> None:
        self.fixed_table = fixed_table
        self.tx_table = tx_table
        self.call_table = call_table
        self.bytecode_table = bytecode_table
        self.rw_table = rw_table

    def fixed_lookup(self, inputs: Union[Tuple[int, int, int, int], Sequence[int]]) -> bool:
        return tuple(inputs) in self.fixed_table

    def tx_lookup(self, inputs: Union[Tuple[int, int, int, int], Sequence[int]]) -> bool:
        return tuple(inputs) in self.tx_table

    def call_lookup(self, inputs: Union[Tuple[int, int, int], Sequence[int]]) -> bool:
        return tuple(inputs) in self.call_table

    def bytecode_lookup(self, inputs: Union[Tuple[int, int, int], Sequence[int]]) -> bool:
        return tuple(inputs) in self.bytecode_table

    def rw_lookup(self, inputs: Union[Tuple[int, int, int, int, int, int, int, int], Sequence[int]]) -> bool:
        return tuple(inputs) in self.rw_table


class Opcode(IntEnum):
    STOP = int(0x00)
    ADD = int(0x01)
    MUL = int(0x02)
    SUB = int(0x03)
    DIV = int(0x04)
    SDIV = int(0x05)
    MOD = int(0x06)
    SMOD = int(0x07)
    ADDMOD = int(0x08)
    MULMOD = int(0x09)
    EXP = int(0x0a)
    SIGNEXTEND = int(0x0b)
    LT = int(0x10)
    GT = int(0x11)
    SLT = int(0x12)
    SGT = int(0x13)
    EQ = int(0x14)
    ISZERO = int(0x15)
    AND = int(0x16)
    OR = int(0x17)
    XOR = int(0x18)
    NOT = int(0x19)
    BYTE = int(0x1a)
    SHL = int(0x1b)
    SHR = int(0x1c)
    SAR = int(0x1d)
    SHA3 = int(0x20)
    ADDRESS = int(0x30)
    BALANCE = int(0x31)
    ORIGIN = int(0x32)
    CALLER = int(0x33)
    CALLVALUE = int(0x34)
    CALLDATALOAD = int(0x35)
    CALLDATASIZE = int(0x36)
    CALLDATACOPY = int(0x37)
    CODESIZE = int(0x38)
    CODECOPY = int(0x39)
    GASPRICE = int(0x3a)
    EXTCODESIZE = int(0x3b)
    EXTCODECOPY = int(0x3c)
    RETURNDATASIZE = int(0x3d)
    RETURNDATACOPY = int(0x3e)
    EXTCODEHASH = int(0x3f)
    BLOCKHASH = int(0x40)
    COINBASE = int(0x41)
    TIMESTAMP = int(0x42)
    NUMBER = int(0x43)
    DIFFICULTY = int(0x44)
    GASLIMIT = int(0x45)
    CHAINID = int(0x46)
    SELFBALANCE = int(0x47)
    BASEFEE = int(0x48)
    POP = int(0x50)
    MLOAD = int(0x51)
    MSTORE = int(0x52)
    MSTORE8 = int(0x53)
    SLOAD = int(0x54)
    SSTORE = int(0x55)
    JUMP = int(0x56)
    JUMPI = int(0x57)
    PC = int(0x58)
    MSIZE = int(0x59)
    GAS = int(0x5a)
    JUMPDEST = int(0x5b)
    PUSH1 = int(0x60)
    PUSH2 = int(0x61)
    PUSH3 = int(0x62)
    PUSH4 = int(0x63)
    PUSH5 = int(0x64)
    PUSH6 = int(0x65)
    PUSH7 = int(0x66)
    PUSH8 = int(0x67)
    PUSH9 = int(0x68)
    PUSH10 = int(0x69)
    PUSH11 = int(0x6a)
    PUSH12 = int(0x6b)
    PUSH13 = int(0x6c)
    PUSH14 = int(0x6d)
    PUSH15 = int(0x6e)
    PUSH16 = int(0x6f)
    PUSH17 = int(0x70)
    PUSH18 = int(0x71)
    PUSH19 = int(0x72)
    PUSH20 = int(0x73)
    PUSH21 = int(0x74)
    PUSH22 = int(0x75)
    PUSH23 = int(0x76)
    PUSH24 = int(0x77)
    PUSH25 = int(0x78)
    PUSH26 = int(0x79)
    PUSH27 = int(0x7a)
    PUSH28 = int(0x7b)
    PUSH29 = int(0x7c)
    PUSH30 = int(0x7d)
    PUSH31 = int(0x7e)
    PUSH32 = int(0x7f)
    DUP1 = int(0x80)
    DUP2 = int(0x81)
    DUP3 = int(0x82)
    DUP4 = int(0x83)
    DUP5 = int(0x84)
    DUP6 = int(0x85)
    DUP7 = int(0x86)
    DUP8 = int(0x87)
    DUP9 = int(0x88)
    DUP10 = int(0x89)
    DUP11 = int(0x8a)
    DUP12 = int(0x8b)
    DUP13 = int(0x8c)
    DUP14 = int(0x8d)
    DUP15 = int(0x8e)
    DUP16 = int(0x8f)
    SWAP1 = int(0x90)
    SWAP2 = int(0x91)
    SWAP3 = int(0x92)
    SWAP4 = int(0x93)
    SWAP5 = int(0x94)
    SWAP6 = int(0x95)
    SWAP7 = int(0x96)
    SWAP8 = int(0x97)
    SWAP9 = int(0x98)
    SWAP10 = int(0x99)
    SWAP11 = int(0x9a)
    SWAP12 = int(0x9b)
    SWAP13 = int(0x9c)
    SWAP14 = int(0x9d)
    SWAP15 = int(0x9e)
    SWAP16 = int(0x9f)
    LOG0 = int(0xa0)
    LOG1 = int(0xa1)
    LOG2 = int(0xa2)
    LOG3 = int(0xa3)
    LOG4 = int(0xa4)
    CREATE = int(0xf0)
    CALL = int(0xf1)
    CALLCODE = int(0xf2)
    RETURN = int(0xf3)
    DELEGATECALL = int(0xf4)
    CREATE2 = int(0xf5)
    STATICCALL = int(0xfa)
    REVERT = int(0xfd)
    SELFDESTRUCT = int(0xff)


class ExecutionResult(IntEnum):
    BEGIN_TX = auto()

    # Opcode's successful cases
    STOP = auto()
    ADD = auto()  # ADD, SUB
    MUL = auto()
    DIV = auto()
    SDIV = auto()
    MOD = auto()
    SMOD = auto()
    ADDMOD = auto()
    MULMOD = auto()
    EXP = auto()
    SIGNEXTEND = auto()
    LT = auto()  # LT, GT
    SLT = auto()  # SLT, SGT
    EQ = auto()
    ISZERO = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto()
    BYTE = auto()
    SHL = auto()
    SHR = auto()
    SAR = auto()
    SHA3 = auto()
    ADDRESS = auto()
    BALANCE = auto()
    ORIGIN = auto()
    CALLER = auto()
    CALLVALUE = auto()
    CALLDATALOAD = auto()
    CALLDATASIZE = auto()
    CALLDATACOPY = auto()
    CODESIZE = auto()
    CODECOPY = auto()
    GASPRICE = auto()
    EXTCODESIZE = auto()
    EXTCODECOPY = auto()
    RETURNDATASIZE = auto()
    RETURNDATACOPY = auto()
    EXTCODEHASH = auto()
    BLOCKHASH = auto()
    COINBASE = auto()
    TIMESTAMP = auto()
    NUMBER = auto()
    DIFFICULTY = auto()
    GASLIMIT = auto()
    CHAINID = auto()
    SELFBALANCE = auto()
    BASEFEE = auto()
    POP = auto()
    MLOAD = auto()
    MSTORE = auto()
    MSTORE8 = auto()
    SLOAD = auto()
    SSTORE = auto()
    JUMP = auto()
    JUMPI = auto()
    PC = auto()
    MSIZE = auto()
    GAS = auto()
    JUMPDEST = auto()
    PUSH = auto()  # PUSH1, PUSH2, ..., PUSH32
    DUP = auto()  # DUP1, DUP2, ..., DUP16
    SWAP = auto()  # SWAP1, SWAP2, ..., SWAP16
    LOG = auto()  # LOG1, LOG2, ..., LOG5
    CREATE = auto()
    CALL = auto()
    CALLCODE = auto()
    RETURN = auto()
    DELEGATECALL = auto()
    CREATE2 = auto()
    STATICCALL = auto()
    REVERT = auto()
    SELFDESTRUCT = auto()

    # Error cases
    ERROR_INVALID_OPCODE = auto()
    # For opcodes who push more than pop
    ERROR_STACK_OVERFLOW = auto()
    # For opcodes who pop and DUP, SWAP who peek deeper element directly
    ERROR_STACK_UNDERFLOW = auto()
    # For opcodes who have non-zero constant gas cost
    ERROR_OOG_CONSTANT = auto()
    # For opcodes MLOAD, MSTORE, MSTORE8, CREATE, RETURN, REVERT, who have pure memory expansion gas cost
    ERROR_OOG_PURE_MEMORY = auto()
    # For opcodes who have dynamic gas usage rather than pure memory expansion
    ERROR_OOG_SHA3 = auto()
    ERROR_OOG_CALLDATACOPY = auto()
    ERROR_OOG_CODECOPY = auto()
    ERROR_OOG_EXTCODECOPY = auto()
    ERROR_OOG_RETURNDATACOPY = auto()
    ERROR_OOG_LOG = auto()
    ERROR_OOG_CALL = auto()
    ERROR_OOG_CALLCODE = auto()
    ERROR_OOG_DELEGATECALL = auto()
    ERROR_OOG_CREATE2 = auto()
    ERROR_OOG_STATICCALL = auto()
    # For SSTORE, LOG0, LOG1, LOG2, LOG3, LOG4, CREATE, CALL, CREATE2, SELFDESTRUCT
    ERROR_WRITE_PROTECTION = auto()
    # For CALL, CALLCODE, DELEGATECALL, STATICCALL
    ERROR_DEPTH = auto()
    # For CALL, CALLCODE
    ERROR_INSUFFICIENT_BALANCE = auto()
    # For CREATE, CREATE2
    ERROR_CONTRACT_ADDRESS_COLLISION = auto()
    ERROR_MAX_CODE_SIZE_EXCEEDED = auto()
    ERROR_INVALID_CODE = auto()
    # For REVERT
    ERROR_EXECUTION_REVERTED = auto()
    # For JUMP, JUMPI
    ERROR_INVALID_JUMP = auto()
    # For RETURNDATACOPY
    ERROR_RETURN_DATA_OUT_OF_BOUNDS = auto()


class CallState:
    call_id: int
    is_root: bool
    is_create: bool
    opcode_source: int
    program_counter: int
    stack_pointer: int
    gas_left: int
    memory_size: int
    state_write_counter: int
    last_callee_id: int
    last_callee_returndata_offset: int
    last_callee_returndata_length: int

    def __init__(
        self,
        call_id: int,
        is_root: bool,
        is_create: bool,
        opcode_source: int,
        program_counter: int,
        stack_pointer: int,
        gas_left: int,
        memory_size: int,
        state_write_counter: int,
        last_callee_id: int,
        last_callee_returndata_offset: int,
        last_callee_returndata_length: int,
    ) -> None:
        self.call_id = call_id
        self.is_root = is_root
        self.is_create = is_create
        self.opcode_source = opcode_source
        self.program_counter = program_counter
        self.stack_pointer = stack_pointer
        self.gas_left = gas_left
        self.memory_size = memory_size
        self.state_write_counter = state_write_counter
        self.last_callee_id = last_callee_id
        self.last_callee_returndata_offset = last_callee_returndata_offset
        self.last_callee_returndata_length = last_callee_returndata_length


class Step:
    # witness
    rw_counter: int
    execution_result: ExecutionResult
    call_state: CallState
    allocation: Sequence[int]
    # lookup tables
    tables: Tables
    # helper numbers
    rw_counter_diff: int = 0
    stack_pointer_diff: int = 0
    state_write_counter_diff: int = 0
    allocation_offset: int = 0

    def __init__(
        self,
        rw_counter: int,
        execution_result: ExecutionResult,
        call_state: CallState,
        allocation: Sequence[int],
        tables: Tables,
    ) -> None:
        self.rw_counter = rw_counter
        self.execution_result = execution_result
        self.call_state = call_state
        self.allocation = allocation
        self.tables = tables

    def peek_allocation(self, idx: int) -> int:
        return self.allocation[idx]

    def allocate(self, n: int) -> Sequence[int]:
        allocation = self.allocation[self.allocation_offset:self.allocation_offset+n]
        self.allocation_offset += n
        return allocation

    def allocate_bool(self, n: int) -> Sequence[int]:
        allocation = self.allocate(n)

        for bool in allocation:
            assert_bool(bool)

        return allocation

    def allocate_byte(self, n: int) -> Sequence[int]:
        allocation = self.allocate(n)

        for byte in allocation:
            self.byte_range_lookup(byte)

        return allocation

    def is_zero(self, value: int) -> bool:
        value_inv = self.allocate(1)[0]
        is_zero = 1 - value * value_inv

        assert value * is_zero == 0
        assert value_inv * is_zero == 0

        return is_zero

    def is_equal(self, lhs: int, rhs: int) -> bool:
        return self.is_zero(lhs - rhs)

    def decompress(self, value: int, n: int, r: int) -> Sequence[int]:
        allocation = self.allocate(n)

        assert value == linear_combine(allocation, r)
        for byte in allocation:
            self.byte_range_lookup(byte)

        return allocation

    def bytes_range_lookup(self, value: int, n: int):
        self.decompress(value, n, 256)

    def byte_range_lookup(self, input: int):
        assert self.tables.fixed_lookup([FixedTableTag.Range256, input, 0, 0])

    def fixed_lookup(self, tag: FixedTableTag, inputs: Sequence[int]):
        allocation = self.allocate(4)

        assert allocation[0] == tag.value
        assert allocation[1:1+len(inputs)] == inputs
        assert self.tables.fixed_lookup(allocation)

    def tx_lookup(self, tag: TxTableTag, tx_id: int, index: int) -> int:
        allocation = self.allocate(4)

        assert allocation[0] == tx_id
        assert allocation[1] == tag.value
        assert allocation[2] == index
        assert self.tables.tx_lookup(allocation)

        return allocation[3]

    def call_lookup(self, tag: CallTableTag, call_id: int) -> int:
        allocation = self.allocate(3)

        assert allocation[0] == call_id or self.call_state.call_id
        assert allocation[1] == tag.value
        assert self.tables.call_lookup(allocation)

        return allocation[2]

    def bytecode_lookup(self, inputs: Sequence[int]) -> Opcode:
        allocation = self.allocate(3)

        assert allocation[:len(inputs)] == inputs
        assert self.tables.bytecode_lookup(allocation)

        return Opcode(allocation[2])

    def r_lookup(self, tag: RWTableTag, inputs: Sequence[int]) -> Sequence[int]:
        allocation = self.allocate(8)

        assert allocation[0] == self.rw_counter + self.rw_counter_diff
        assert allocation[1] == False
        assert allocation[2] == tag
        assert allocation[3:3+len(inputs)] == inputs
        assert self.tables.rw_lookup(allocation)

        self.rw_counter_diff += 1

        return allocation[3+len(inputs):]

    def w_lookup(self, tag: RWTableTag, inputs: Sequence[int], rw_counter_end_of_revert: Union[int, None] = None) -> Sequence[int]:
        allocation = self.allocate(8)

        assert allocation[0] == self.rw_counter + self.rw_counter_diff
        assert allocation[1] == True
        assert allocation[2] == tag
        assert allocation[3:3+len(inputs)] == inputs
        assert self.tables.rw_lookup(allocation)

        self.rw_counter_diff += 1

        if rw_counter_end_of_revert is not None:
            allocation_revert = self.allocate(8)

            assert allocation_revert[0] == rw_counter_end_of_revert - \
                (self.call_state.state_write_counter + self.state_write_counter_diff)
            assert allocation_revert[1] == True
            assert allocation_revert[2] == tag
            if tag == RWTableTag.TxAccessListAccount:
                assert allocation_revert[3] == allocation[3]  # tx_id
                assert allocation_revert[4] == allocation[4]  # account address
                assert allocation_revert[5] == allocation[6]  # revert value
            elif tag == RWTableTag.TxAccessListStorageSlot:
                assert allocation_revert[3] == allocation[3]  # tx_id
                assert allocation_revert[4] == allocation[4]  # account address
                assert allocation_revert[5] == allocation[5]  # storage slot
                assert allocation_revert[6] == allocation[7]  # revert value
            elif tag == RWTableTag.TxRefund:
                assert allocation_revert[3] == allocation[3]  # tx_id
                assert allocation_revert[4] == allocation[5]  # revert value
            elif tag == RWTableTag.AccountNonce:
                assert allocation_revert[3] == allocation[3]  # account address
                assert allocation_revert[4] == allocation[5]  # revert value
            elif tag == RWTableTag.AccountBalance:
                assert allocation_revert[3] == allocation[3]  # account address
                assert allocation_revert[4] == allocation[5]  # revert value
            elif tag == RWTableTag.AccountCodeHash:
                assert allocation_revert[3] == allocation[3]  # account address
                assert allocation_revert[4] == allocation[5]  # revert value
            elif tag == RWTableTag.AccountStorage:
                assert allocation_revert[3] == allocation[3]  # account address
                assert allocation_revert[4] == allocation[4]  # storage slot
                assert allocation_revert[5] == allocation[6]  # revert value
            elif tag == RWTableTag.AccountSelfDestructed:
                assert allocation_revert[3] == allocation[3]  # account address
                assert allocation_revert[4] == allocation[5]  # revert value
            assert self.tables.rw_lookup(allocation_revert)

            self.state_write_counter_diff += 1

        return allocation[3+len(inputs):]

    def opcode_lookup(self, offset: int = 0) -> Opcode:
        if self.call_state.is_create:
            if self.call_state.is_root:
                return Opcode(self.tx_lookup(TxTableTag.Calldata, [
                    self.call_state.opcode_source,
                    self.call_state.program_counter + offset,
                ]))
            else:
                # TODO: Add offset and verify creation code length
                return Opcode(self.r_lookup(RWTableTag.Memory, [
                    self.call_state.opcode_source,
                    self.call_state.program_counter + offset,
                ])[0])
        else:
            return self.bytecode_lookup([
                self.call_state.opcode_source,
                self.call_state.program_counter + offset,
            ])

    def stack_pop_lookup(self) -> int:
        value = self.r_lookup(RWTableTag.Stack, [
            self.call_state.call_id,
            self.call_state.stack_pointer + self.stack_pointer_diff
        ])[0]
        self.stack_pointer_diff += 1
        return value

    def stack_push_lookup(self) -> int:
        self.stack_pointer_diff -= 1
        return self.w_lookup(RWTableTag.Stack, [
            self.call_state.call_id,
            self.call_state.stack_pointer + self.stack_pointer_diff
        ])[0]


def le_to_int(bytes: Sequence[int]) -> int:
    assert len(bytes) < 32

    return linear_combine(bytes, 256)


def linear_combine(bytes: Sequence[int], r: int) -> int:
    ret = 0
    for byte in reversed(bytes):
        ret = (ret * r + byte) % FQ
    return ret


def assert_bool(value):
    assert value in [0, 1]


def assert_addition(bytes_a: Sequence[int], bytes_b: Sequence[int], bytes_c: Sequence[int], carries: Sequence[bool]):
    for idx, (a, b, c, carry) in enumerate(zip(bytes_a, bytes_b, bytes_c, carries)):
        assert carry * 256 + c == a + b + (0 if idx == 0 else carries[idx - 1])


def assert_transfer(curr: Step, caller_address: int, callee_address: int, bytes_value: Sequence[int], r: int):
    is_static = curr.call_lookup(CallTableTag.IsStatic)
    assert is_static == False

    is_persistent = curr.call_lookup(CallTableTag.IsPersistent)
    rw_counter_end_of_revert = None if is_persistent else \
        curr.call_lookup(CallTableTag.RWCounterEndOfRevert)

    caller_prev_balance = curr.r_lookup(RWTableTag.AccountBalance,
                                        [caller_address])[0]
    callee_prev_balance = curr.r_lookup(RWTableTag.AccountBalance,
                                        [callee_address])[0]
    caller_new_balance = curr.w_lookup(RWTableTag.AccountBalance,
                                       [caller_address],
                                       rw_counter_end_of_revert)[0]
    callee_new_balance = curr.w_lookup(RWTableTag.AccountBalance,
                                       [callee_address],
                                       rw_counter_end_of_revert)[0]

    # Verify caller's new balance is subtracted by value and not underflow
    bytes_caller_prev_balance = curr.decompress(caller_prev_balance, 32, r)
    bytes_caller_new_balance = curr.decompress(caller_new_balance, 32, r)
    caller_carries = curr.allocate_bool(32)
    assert_addition(bytes_caller_new_balance, bytes_value,
                    bytes_caller_prev_balance, caller_carries)
    assert caller_carries[31] == 0

    # Verify callee's new balance is added by value and not overflow
    bytes_callee_prev_balance = curr.decompress(callee_prev_balance, 32, r)
    bytes_callee_new_balance = curr.decompress(callee_new_balance, 32, r)
    callee_carries = curr.allocate_bool(32)
    assert_addition(bytes_callee_prev_balance, bytes_value,
                    bytes_callee_new_balance, callee_carries)
    assert callee_carries[31] == 0


def assert_memory_expansion(
    curr: Step,
    bytes_cd_offset: Sequence[int],
    bytes_cd_length: Sequence[int],
    bytes_rd_offset: Sequence[int],
    bytes_rd_length: Sequence[int],
) -> Tuple[int, int]:
    next_memory_size = curr.allocate(1)[0]

    is_nonzero_cd_length = not curr.is_zero(le_to_int(bytes_cd_length))
    is_nonzero_rd_length = not curr.is_zero(le_to_int(bytes_rd_length))
    bytes_next_memory_size_cd = curr.allocate_byte(4)
    bytes_next_memory_size_rd = curr.allocate_byte(4)
    next_memory_size_cd = is_nonzero_cd_length * \
        le_to_int(bytes_next_memory_size_cd)
    next_memory_size_rd = is_nonzero_rd_length * \
        le_to_int(bytes_next_memory_size_rd)

    # Verify next_memory_size_cd is correct
    if is_nonzero_cd_length:
        assert sum(bytes_cd_offset[5:]) == 0
        curr.fixed_lookup(FixedTableTag.Range32,
                          [32 * next_memory_size_cd - (le_to_int(bytes_cd_offset) + le_to_int(bytes_cd_length))])

    # Verify next_memory_size_rd is correct
    if is_nonzero_rd_length:
        assert sum(bytes_rd_offset[5:]) == 0
        curr.fixed_lookup(FixedTableTag.Range32,
                          [32 * next_memory_size_rd - (le_to_int(bytes_rd_offset) + le_to_int(bytes_rd_length))])

    # Verify next_memory_size == \
    #   max(curr.call_state.memory_size, next_memory_size_cd, next_memory_size_rd)
    assert next_memory_size in [
        curr.call_state.memory_size,
        next_memory_size_cd,
        next_memory_size_rd,
    ]
    curr.bytes_range_lookup(next_memory_size - curr.call_state.memory_size, 4)
    curr.bytes_range_lookup(next_memory_size - next_memory_size_cd, 4)
    curr.bytes_range_lookup(next_memory_size - next_memory_size_rd, 4)

    # Verify memory_gas_cost is correct
    curr_quad_memory_gas_cost = le_to_int(curr.allocate_byte(8))
    next_quad_memory_gas_cost = le_to_int(curr.allocate_byte(8))
    curr.fixed_lookup(FixedTableTag.Range512,
                      [512 * curr_quad_memory_gas_cost - curr.call_state.memory_size * curr.call_state.memory_size])
    curr.fixed_lookup(FixedTableTag.Range512,
                      [512 * next_quad_memory_gas_cost - next_memory_size * next_memory_size])
    memory_gas_cost = next_quad_memory_gas_cost - curr_quad_memory_gas_cost + \
        3 * (next_memory_size - curr.call_state.memory_size)

    return next_memory_size, memory_gas_cost


def assert_step_transition(curr: Step, next: Step, **kwargs):
    def assert_transition(obj_curr: Any, obj_next: Any, keys: Sequence[str]):
        for key in keys:
            curr, next = getattr(obj_curr, key), getattr(obj_next, key)
            key_not, key_diff = f'{key}_not', f'{key}_diff'
            if key_not in kwargs:
                value_not = kwargs.get(key_not)
                if type(value_not) is list:
                    assert next not in value_not
                else:
                    assert next != value_not
            elif key_diff in kwargs:
                assert next == curr + kwargs.get(key_diff)
            elif key in kwargs:
                assert next == kwargs.get(key)
            else:
                assert next == curr

    assert_transition(curr, next, ['rw_counter', 'execution_result'])
    assert_transition(curr.call_state, next.call_state, [
        'call_id',
        'is_root',
        'is_create',
        'opcode_source',
        'program_counter',
        'stack_pointer',
        'gas_left',
        'memory_size',
        'state_write_counter',
        'last_callee_id',
        'last_callee_returndata_offset',
        'last_callee_returndata_length',
    ])


def begin_tx(curr: Step, next: Step, r: int, is_first_step: bool):
    tx_id = curr.call_lookup(CallTableTag.TxId)
    depth = curr.call_lookup(CallTableTag.Depth)

    if is_first_step:
        assert curr.rw_counter == 1
        assert curr.call_state.call_id == 1
        assert tx_id == 1
        assert depth == 1

    # Copy data from TxTable to CallTable
    tx_caller_address = curr.tx_lookup(TxTableTag.CallerAddress, tx_id)
    tx_callee_address = curr.tx_lookup(TxTableTag.CalleeAddress, tx_id)
    tx_is_create = curr.tx_lookup(TxTableTag.IsCreate, tx_id)
    tx_value = curr.tx_lookup(TxTableTag.Value, tx_id)
    tx_calldata_length = curr.tx_lookup(TxTableTag.CalldataLength, tx_id)
    caller_address = curr.call_lookup(CallTableTag.CallerAddress)
    callee_address = curr.call_lookup(CallTableTag.CalleeAddress)
    calldata_offset = curr.call_lookup(CallTableTag.CalldataOffset)
    calldata_length = curr.call_lookup(CallTableTag.CalldataLength)
    value = curr.call_lookup(CallTableTag.Value)
    assert caller_address == tx_caller_address
    assert callee_address == tx_callee_address
    assert value == tx_value
    assert calldata_offset == 0
    assert calldata_length == tx_calldata_length

    # Verify nonce
    tx_nonce = curr.tx_lookup(TxTableTag.Nonce, tx_id)
    assert curr.w_lookup(RWTableTag.AccountNonce, [caller_address, tx_nonce])

    # TODO: Buy intrinsic gas (EIP 2930)
    tx_gas = curr.tx_lookup(TxTableTag.Gas, tx_id)
    curr.bytes_range_lookup(tx_gas, 8)

    # Verify transfer
    is_zero_value = curr.is_zero(value)
    if not is_zero_value:
        bytes_value = curr.bytes_range_lookup(value, 8)
        assert_transfer(curr, caller_address, callee_address, bytes_value, r)

    if tx_is_create:
        # TODO: Verify receiver address
        # TODO: Set next.call_state.opcode_source to tx_id
        raise NotImplementedError
    else:
        code_hash = curr.r_lookup(RWTableTag.AccountCodeHash,
                                  [callee_address])
        is_empty_code_hash = curr.is_equal(
            code_hash, linear_combine(EMPTY_CODE_HASH, r))

        # TODO: Handle precompile
        if is_empty_code_hash:
            assert_step_transition(
                rw_counter_diff=curr.rw_counter_diff,
                execution_result=ExecutionResult.BEGIN_TX,
                call_id=next.rw_counter,
            )
            assert next.peek_allocation(2) == tx_id + 1

            # TODO: Refund caller and tip coinbase
        else:
            assert_step_transition(
                curr, next,
                rw_counter_diff=curr.rw_counter_diff,
                execution_result_not=ExecutionResult.BEGIN_TX,
                is_root=True,
                is_create=tx_is_create,
                opcode_source=code_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=tx_gas,
                memory_size=0,
                state_write_counter=0,
                last_callee_id=0,
                last_callee_returndata_offset=0,
                last_callee_returndata_length=0,
            )


def add(curr: Step, next: Step, r: int, opcode: Opcode):
    swap, *carries = curr.allocate_bool(33)

    # Verify opcode
    assert opcode == (Opcode.SUB if swap else Opcode.ADD)

    # Verify gas
    next_gas_left = curr.call_state.gas_left - 3
    curr.bytes_range_lookup(next_gas_left, 8)

    a = curr.stack_pop_lookup()
    b = curr.stack_pop_lookup()
    c = curr.stack_push_lookup()
    bytes_a = curr.decompress(a, 32, r)
    bytes_b = curr.decompress(c if swap else b, 32, r)
    bytes_c = curr.decompress(b if swap else c, 32, r)

    assert_addition(bytes_a, bytes_b, bytes_c, carries)

    assert_step_transition(
        curr, next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
        program_counter_diff=1,
        stack_pointer_diff=curr.stack_pointer_diff,
        gas_left=next_gas_left,
    )


def push(curr: Step, next: Step, r: int, opcode: Opcode):
    selectors = curr.allocate_bool(32)

    # Verify opcode
    num_pushed = opcode - Opcode.PUSH1 + 1
    curr.fixed_lookup(FixedTableTag.Range32, [num_pushed])

    # Verify gas
    next_gas_left = curr.call_state.gas_left - 3
    curr.bytes_range_lookup(next_gas_left, 8)

    value = curr.stack_push_lookup()
    bytes_value = curr.decompress(value, 32, r)

    assert sum(selectors) == num_pushed
    for i, byte in enumerate(bytes_value):
        if i > 0:
            assert_bool(selectors[i] - selectors[i - 1])
        if selectors[i]:
            assert byte == curr.opcode_lookup(i + 1)
        else:
            assert bytes_value[i] == 0

    assert_step_transition(
        curr, next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
        program_counter_diff=num_pushed + 1,
        stack_pointer_diff=curr.stack_pointer_diff,
        gas_left=next_gas_left,
    )


def call(curr: Step, next: Step, r: int, opcode: Opcode):
    # Verify opcode
    assert opcode == Opcode.CALL

    # Verify depth
    depth = curr.call_lookup(CallTableTag.Depth)
    curr.fixed_lookup(FixedTableTag.Range1024, [depth])

    # Gas needs full decompression due to EIP 150
    bytes_gas = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_callee_address = curr.decompress(curr.stack_pop_lookup(), 32, r)
    value = curr.stack_pop_lookup()
    bytes_value = curr.decompress(value, 32, r)
    bytes_cd_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_cd_length = curr.decompress(curr.stack_pop_lookup(), 5, r)
    bytes_rd_offset = curr.decompress(curr.stack_pop_lookup(), 32, r)
    bytes_rd_length = curr.decompress(curr.stack_pop_lookup(), 5, r)
    result = curr.stack_push_lookup()
    assert_bool(result)

    callee_address = le_to_int(bytes_callee_address[:20])

    # Verify transfer
    is_zero_value = curr.is_zero(value)
    if not is_zero_value:
        caller_address = curr.call_lookup(CallTableTag.CalleeAddress)
        assert_transfer(curr, caller_address, callee_address, bytes_value, r)

    # Verify memory expansion
    next_memory_size, memory_gas_cost = assert_memory_expansion(curr)

    # Verify gas cost
    tx_id = curr.call_lookup(CallTableTag.TxId)
    is_cold_access = 1 - \
        curr.w_lookup(RWTableTag.TxAccessListAccount,
                      [tx_id, callee_address, 1])[0]
    code_hash = curr.r_lookup(RWTableTag.AccountCodeHash, [callee_address])[0]
    is_empty_code_hash = curr.is_equal(
        code_hash, linear_combine(EMPTY_CODE_HASH, r))
    callee_nonce = curr.r_lookup(RWTableTag.AccountNonce, [callee_address])[0]
    callee_balance = curr.r_lookup(
        RWTableTag.AccountBalance, [callee_address])[0]
    is_account_empty = curr.is_zero(callee_nonce) and \
        curr.is_zero(callee_balance) and \
        is_empty_code_hash
    base_gas_cost = 100 + \
        is_cold_access * 2500 + \
        + is_account_empty * 25000 + \
        (not is_zero_value) * 9000 + \
        memory_gas_cost

    available_gas = curr.call_state.gas_left - base_gas_cost
    one_64th_available_gas = le_to_int(curr.allocate_byte(8))
    curr.fixed_lookup(FixedTableTag.Range64, [
                      available_gas - 64 * one_64th_available_gas])

    is_capped = curr.allocate_bool(1)[0]
    is_uint64 = curr.is_zero(sum(bytes_gas[8:]))
    callee_gas_left = available_gas - one_64th_available_gas
    if is_uint64:
        if is_capped:
            curr.bytes_range_lookup(le_to_int(bytes_gas) - callee_gas_left, 8)
        else:
            curr.bytes_range_lookup(callee_gas_left - le_to_int(bytes_gas), 8)
            callee_gas_left = le_to_int(bytes_gas)
    else:
        assert is_capped

    next_gas_left = curr.call_state.gas_left - base_gas_cost - callee_gas_left
    curr.bytes_range_lookup(next_gas_left, 8)

    # TODO: Handle precompile
    if is_empty_code_hash:
        assert result == 1

        assert_step_transition(
            curr, next,
            rw_counter_diff=curr.rw_counter_diff,
            execution_result_not=ExecutionResult.BEGIN_TX,
            state_write_counter_diff=curr.state_write_counter_diff,
            program_counter_diff=1,
            stack_pointer_diff=curr.stack_pointer_diff,
            gas_left=next_gas_left,
            memory_size=next_memory_size,
        )
    else:
        # Save caller's call state
        for (tag, value) in [
            (CallTableTag.IsRoot, curr.call_state.is_root),
            (CallTableTag.IsCreate, curr.call_state.is_create),
            (CallTableTag.OpcodeSource, curr.call_state.opcode_source),
            (CallTableTag.ProgramCounter, curr.call_state.program_counter + 1),
            (CallTableTag.StackPointer,
             curr.call_state.stack_pointer + curr.stack_pointer_diff),
            (CallTableTag.GasLeft, next_gas_left),
            (CallTableTag.MemorySize, next_memory_size),
            (CallTableTag.StateWriteCounter,
             curr.call_state.state_write_counter + curr.state_write_counter_diff),
        ]:
            curr.w_lookup(RWTableTag.CallState,
                          [curr.call_state.call_id, tag, value])

        # Setup callee's context
        rw_counter_end_of_revert = curr.call_lookup(
            CallTableTag.RWCounterEndOfRevert)
        caller_address = curr.call_lookup(CallTableTag.CalleeAddress)
        is_persistent = curr.call_lookup(CallTableTag.IsPersistent)
        is_static = curr.call_lookup(CallTableTag.IsStatic)

        [
            callee_rw_counter_end_of_revert,
            callee_caller_call_id,
            callee_tx_id,
            callee_depth,
            callee_caller_address,
            callee_callee_address,
            callee_calldata_offset,
            callee_calldata_length,
            callee_returndata_offset,
            callee_returndata_length,
            callee_value,
            callee_result,
            callee_is_persistent,
            callee_is_static,
            callee_is_create
        ] = [
            curr.call_lookup(tag, next.call_state.call_id) for tag in [
                CallTableTag.RWCounterEndOfRevert,
                CallTableTag.CallerCallId,
                CallTableTag.TxId,
                CallTableTag.Depth,
                CallTableTag.CallerAddress,
                CallTableTag.CalleeAddress,
                CallTableTag.CalldataOffset,
                CallTableTag.CalldataLength,
                CallTableTag.ReturndataOffset,
                CallTableTag.ReturndataLength,
                CallTableTag.Value,
                CallTableTag.Result,
                CallTableTag.IsPersistent,
                CallTableTag.IsStatic,
                CallTableTag.IsCreate,
            ]
        ]

        assert callee_caller_call_id == curr.call_state.call_id
        assert callee_tx_id == tx_id
        assert callee_depth == depth + 1
        assert callee_caller_address == caller_address
        assert callee_callee_address == le_to_int(bytes_callee_address[:20])
        assert callee_calldata_offset == le_to_int(bytes_cd_offset)
        assert callee_calldata_length == le_to_int(bytes_cd_length)
        assert callee_returndata_offset == le_to_int(bytes_rd_offset)
        assert callee_returndata_length == le_to_int(bytes_rd_length)
        assert callee_value == value
        assert callee_result == result
        assert callee_is_persistent == is_persistent * result
        assert callee_is_static == is_static
        assert callee_is_create == False

        callee_state_write_counter = 0
        # Callee succeed but one of callers reverts at some point
        if result and not is_persistent:
            assert rw_counter_end_of_revert == callee_rw_counter_end_of_revert
            assert callee_state_write_counter == \
                curr.call_state.state_write_counter + curr.state_write_counter_diff

        assert_step_transition(
            curr, next,
            rw_counter_diff=curr.rw_counter_diff,
            execution_result_not=ExecutionResult.BEGIN_TX,
            call_id=next.rw_counter,
            is_root=False,
            is_create=False,
            opcode_source=code_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=callee_gas_left + (0 if is_zero_value else 2300),
            memory_size=0,
            state_write_counter=callee_state_write_counter,
            last_callee_id=0,
            last_callee_returndata_offset=0,
            last_callee_returndata_length=0,
        )


def error_invalid_opcode(curr: Step, next: Step, r: int, opcode: Opcode):
    curr.fixed_lookup(FixedTableTag.InvalidOpcode, [opcode])

    # TODO: Return to caller's state or go to next tx


def error_stack_overflow(curr: Step, next: Step, r: int, opcode: Opcode):
    curr.fixed_lookup(FixedTableTag.StackOverflow,
                      [opcode, curr.call_state.stack_pointer])

    # TODO: Return to caller's state or go to next tx


def error_stack_underflow(curr: Step, next: Step, r: int, opcode: Opcode):
    curr.fixed_lookup(FixedTableTag.StackUnderflow,
                      [opcode, curr.call_state.stack_pointer])

    # TODO: Return to caller's state or go to next tx


def error_depth(curr: Step, next: Step, r: int, opcode: Opcode):
    assert opcode in [Opcode.CALL, Opcode.CALLCODE,
                      Opcode.DELEGATECALL, Opcode.STATICCALL]

    depth = curr.call_lookup(CallTableTag.Depth)
    assert depth == 1024

    # TODO: Return to caller's state or go to next tx


def main(curr: Step, next: Step, r: int, is_first_step: bool, is_final_step: bool):
    if is_first_step or curr.execution_result == ExecutionResult.BEGIN_TX:
        begin_tx(curr, next, r, is_first_step)
    else:
        opcode = curr.opcode_lookup()

        # opcode's successful cases
        if curr.execution_result == ExecutionResult.ADD:
            add(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.PUSH:
            push(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.CALL:
            call(curr, next, r, opcode)
        # error cases
        elif curr.execution_result == ExecutionResult.ERROR_INVALID_CODE:
            error_invalid_opcode(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.ERROR_STACK_OVERFLOW:
            error_stack_overflow(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.ERROR_STACK_UNDERFLOW:
            error_stack_underflow(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.ERROR_DEPTH:
            error_depth(curr, next, r, opcode)
        else:
            raise NotImplementedError

    if is_final_step:
        # Verify no malicious insertion
        assert curr.rw_counter == len(curr.tables.rw_table)

        # TODO: Verify final step is a padding
        # TODO: Verify final step has the tx_id identical to the amount in tx_table


# TODO: Refactor
def test_add():
    r = 1
    bytecode = bytearray.fromhex('602060400100')
    bytecode_hash = linear_combine(keccak_256(bytecode).digest(), r)
    tables = Tables(
        fixed_table=set(
            [(FixedTableTag.Range256, i, 0, 0) for i in range(256)]
        ),
        tx_table=set(),
        call_table=set(),
        bytecode_table=set(
            [(bytecode_hash, i, byte) for (i, byte) in enumerate(bytecode)],
        ),
        rw_table=set([
            (9, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0),
            (10, False, RWTableTag.Stack, 1, 1023, 0x20, 0, 0),
            (11, True, RWTableTag.Stack, 1, 1023, 0x60, 0, 0),
        ]),
    )

    curr = Step(
        rw_counter=9,
        execution_result=ExecutionResult.ADD,
        call_state=CallState(
            call_id=1,
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=4,
            stack_pointer=1022,
            gas_left=3,
            memory_size=0,
            state_write_counter=0,
            last_callee_id=0,
            last_callee_returndata_offset=0,
            last_callee_returndata_length=0,
        ),
        allocation=[
            bytecode_hash, 4, Opcode.ADD,  # bytecode lookup
            0,  # swap
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # carry
            0, 0, 0, 0, 0, 0, 0, 0,  # next gas_left decompression
            9, False, RWTableTag.Stack, 1, 1022, 0x40, 0, 0,  # stack pop (a)
            10, False, RWTableTag.Stack, 1, 1023, 0x20, 0, 0,  # stack pop (b)
            11, True, RWTableTag.Stack, 1, 1023, 0x60, 0, 0,  # stack push (c)
            0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # a decompression
            0x20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # b decompression
            0x60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # c decompression
        ],
        tables=tables,
    )
    next = Step(
        rw_counter=12,
        execution_result=ExecutionResult.STOP,
        call_state=CallState(
            call_id=1,
            is_root=True,
            is_create=False,
            opcode_source=bytecode_hash,
            program_counter=5,
            stack_pointer=1023,
            gas_left=0,
            memory_size=0,
            state_write_counter=0,
            last_callee_id=0,
            last_callee_returndata_offset=0,
            last_callee_returndata_length=0,
        ),
        allocation=[],
        tables=tables,
    )

    main(curr, next, r, is_first_step=False, is_final_step=False)
