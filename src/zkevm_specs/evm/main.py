from enum import IntEnum, auto
from typing import Sequence, Set, Tuple, Union


FQ = 21888242871839275222246405745257275088548364400416034343698204186575808495617
EMPTY_CODE_HASH = bytearray.fromhex(
    'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')


class FixedTableTag(IntEnum):
    Range32 = auto()
    Range256 = auto()
    Range512 = auto()
    Range1024 = auto()


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
        int,  # v1
        int,  # v2
        int,  # v3
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
        int,  # v1
        int,  # v2
        int,  # v3
        int,  # v4
        int,  # v5
    ]]

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
    SUB = int(0x03)
    CALL = int(0xf1)


class ExecutionResult(IntEnum):
    BEGIN_TX = auto()

    # opcodes
    STOP = auto()
    ADD = auto()
    CALL = auto()
    PUSH = auto()
    # more...

    # errors
    ERROR_OUT_OF_GAS = auto()
    ERROR_STACK_UNDERFLOW = auto()
    ERROR_STACK_OVERFLOW = auto()
    # more...


class CallState:
    call_id: int
    is_root: bool
    is_create: bool
    program_counter: int
    opcode_source: int
    stack_pointer: int
    gas_left: int
    memory_size: int
    state_write_counter: int
    last_callee_id: int
    last_callee_returndata_offset: int
    last_callee_returndata_length: int


class Step:
    # witness
    rw_counter: int
    execution_result: ExecutionResult
    call_state: CallState
    allocation: Sequence[int]
    # helper table
    tables: Tables
    # helper constant
    rw_counter_diff: int
    allocation_offset: int

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

    def decompress(self, value: int, n: int, r: int) -> Sequence[int]:
        allocation = self.allocate(n)

        assert value == random_linear_combine(allocation, r)
        for byte in allocation:
            self.byte_range_lookup(byte)

        return allocation

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

    def r_lookup(self, tag: RWTableTag, inputs: Sequence[int], rw_counter: int) -> Sequence[int]:
        allocation = self.allocate(8)

        assert allocation[0] == rw_counter or \
            (self.rw_counter + self.rw_counter_diff)
        assert allocation[1] == False
        assert allocation[2] == tag
        assert allocation[3:3+len(inputs)] == inputs
        assert self.tables.rw_lookup(allocation)

        if rw_counter is None:
            self.rw_counter_diff += 1

        return allocation[3+len(inputs):]

    def w_lookup(self, tag: RWTableTag, inputs: Sequence[int], rw_counter: int) -> Sequence[int]:
        allocation = self.allocate(8)

        assert allocation[0] == rw_counter or \
            (self.rw_counter + self.rw_counter_diff)
        assert allocation[1] == True
        assert allocation[2] == tag
        assert allocation[3:3+len(inputs)] == inputs
        assert self.tables.rw_lookup(allocation)

        if rw_counter is None:
            self.rw_counter_diff += 1

        return allocation[3+len(inputs):]


def le_to_int(bytes: Sequence[int]) -> int:
    assert len(bytes) < 32

    ret = 0
    for byte in reversed(bytes):
        ret = (ret * 256) + byte
    return ret


def random_linear_combine(bytes: Sequence[int], r: int) -> int:
    ret = 0
    for byte in reversed(bytes):
        ret = (ret * r + byte) % FQ
    return ret


def assert_bool(value):
    assert value in [0, 1]


def assert_state_transition(curr: Step, next: Step, **kwargs):
    for key in ['rw_counter', 'execution_result']:
        assert getattr(next, key) == kwargs.get(
            key, getattr(curr, key) + kwargs.get(f'{key}_diff', 0))

    for key in [
        'call_id',
        'is_root',
        'is_create',
        'program_counter',
        'opcode_source',
        'stack_pointer',
        'gas_left',
        'memory_size',
    ]:
        assert getattr(next.call_state, key) == kwargs.get(
            key, getattr(curr.call_state, key) + kwargs.get(f'{key}_diff', 0))


def opcode_lookup(curr: Step) -> Opcode:
    if curr.call_state.is_create:
        if curr.call_state.is_root:
            return curr.tx_lookup(TxTableTag.Calldata, [
                curr.call_state.opcode_source,
                curr.call_state.program_counter,
            ])
        else:
            # TODO: Add offsize and verify creation code length
            return curr.r_lookup(RWTableTag.Memory, [
                curr.call_state.opcode_source,
                curr.call_state.program_counter,
            ])
    else:
        return curr.bytecode_lookup([
            curr.call_state.opcode_source,
            curr.call_state.program_counter,
        ])


def main(curr: Step, next: Step, r: int, is_first_step: bool):
    if is_first_step:
        assert curr.execution_result == ExecutionResult.BEGIN_TX

    if curr.execution_result == ExecutionResult.BEGIN_TX:
        begin_tx(curr, next, r, is_first_step)
    else:
        opcode = opcode_lookup(curr)

        if curr.execution_result == ExecutionResult.ADD:
            add(curr, next, r, opcode)
        elif curr.execution_result == ExecutionResult.CALL:
            call(curr, next, r, opcode)
        else:
            raise NotImplementedError


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
    curr.decompress(tx_gas, 8, 256)

    # TODO: Transfer value (also with reversion)

    if tx_is_create:
        # TODO: Verify receiver address
        # TODO: Set next.call_state.opcode_source to tx_id
        raise NotImplementedError
    else:
        code_hash = curr.r_lookup(RWTableTag.AccountCodeHash,
                                  [callee_address])

        # TODO: Handle precompile
        if code_hash == random_linear_combine(EMPTY_CODE_HASH, r):
            assert_state_transition(
                execution_result=ExecutionResult.BEGIN_TX,
                rw_counter_diff=curr.rw_counter_diff,
                call_id=next.rw_counter,
            )
            assert next.peek_allocation(2) == tx_id + 1

            # TODO: Refund caller and tip coinbase
        else:
            assert next.execution_result != ExecutionResult.BEGIN_TX
            assert_state_transition(
                curr, next,
                rw_counter_diff=curr.rw_counter_diff,
                is_root=True,
                is_create=tx_is_create,
                opcode_source=code_hash,
                program_counter=0,
                stack_pointer=1024,
                # TODO: Minus intrinsic gas
                gas_left=tx_gas,
                memory_size=0,
                state_write_counter=0,
            )


def add(curr: Step, next: Step, r: int, opcode: Opcode):
    swap, *carries = curr.allocate_bool(33)

    # Verify opcode
    assert opcode == (Opcode.SUB if swap else Opcode.ADD)

    # Verify gas
    next_gas_left = curr.call_state.gas_left - 3
    curr.decompress(next_gas_left, 8, 256)

    a = curr.r_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer])[0]
    b = curr.r_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer + 1])[0]
    c = curr.w_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer + 1])[0]
    bytes_a = curr.decompress(a, 32, r)
    bytes_b = curr.decompress(c if swap else b, 32, r)
    bytes_c = curr.decompress(b if swap else c, 32, r)

    for idx, (a, b, c, carry) in enumerate(zip(bytes_a, bytes_b, bytes_c, carries)):
        assert carry * 256 + c == a + b + (0 if idx == 0 else carries[idx - 1])

    assert next.execution_result != ExecutionResult.BEGIN_TX
    assert_state_transition(
        curr, next,
        rw_counter_diff=curr.rw_counter_diff,
        program_counter_diff=1,
        stack_pointer_diff=1,
        gas_left=next_gas_left,
    )


def call(curr: Step, next: Step, r: int, opcode: Opcode):
    # Verify opcode
    assert opcode == Opcode.CALL

    # Verify depth
    depth = curr.call_lookup(CallTableTag.Depth)
    curr.fixed_lookup(FixedTableTag.Range1024, [depth])

    gas = curr.r_lookup(RWTableTag.Stack,
                        [curr.call_state.call_id, curr.call_state.stack_pointer])[0]
    callee_address = curr.r_lookup(RWTableTag.Stack,
                                   [curr.call_state.call_id, curr.call_state.stack_pointer + 1])[0]
    value = curr.r_lookup(RWTableTag.Stack,
                          [curr.call_state.call_id, curr.call_state.stack_pointer + 2])[0]
    cd_offset = curr.r_lookup(RWTableTag.Stack,
                              [curr.call_state.call_id, curr.call_state.stack_pointer + 3])[0]
    cd_length = curr.r_lookup(RWTableTag.Stack,
                              [curr.call_state.call_id, curr.call_state.stack_pointer + 4])[0]
    rd_offset = curr.r_lookup(RWTableTag.Stack,
                              [curr.call_state.call_id, curr.call_state.stack_pointer + 5])[0]
    rd_length = curr.r_lookup(RWTableTag.Stack,
                              [curr.call_state.call_id, curr.call_state.stack_pointer + 6])[0]
    result = curr.w_lookup(RWTableTag.Stack,
                           [curr.call_state.call_id, curr.call_state.stack_pointer + 6])[0]

    # Need full decompression due to EIP 150
    bytes_gas = curr.decompress(gas, 32, r)
    bytes_callee_address = curr.decompress(callee_address, 32, r)
    bytes_value = curr.decompress(value, 32, r)
    bytes_cd_offset = curr.decompress(cd_offset, 32, r)
    bytes_cd_length = curr.decompress(cd_length, 5, r)
    bytes_rd_offset = curr.decompress(rd_offset, 32, r)
    bytes_rd_length = curr.decompress(rd_length, 5, r)
    assert_bool(result)

    # TODO: Transfer value (also with reversion)
    is_zero_value = curr.is_zero(value)
    if not is_zero_value:
        is_static = curr.call_lookup(CallTableTag.IsStatic)
        assert is_static == False

        caller_prev_balance = curr.r_lookup(
            RWTableTag.AccountBalance, [callee_address])

        is_persistent = curr.call_lookup(CallTableTag.IsPersistent)
        if not is_persistent:
            rw_counter_end_of_revert = curr.call_lookup(
                CallTableTag.RWCounterEndOfRevert)

    # Verify memory expansion
    is_nonzero_cd_length = not curr.is_zero(le_to_int(bytes_cd_length))
    is_nonzero_rd_length = not curr.is_zero(le_to_int(bytes_rd_length))
    new_memory_size = curr.allocate(1)[0]
    bytes_new_memory_size_cd = curr.allocate_byte(4)
    bytes_new_memory_size_rd = curr.allocate_byte(4)
    new_memory_size_cd = is_nonzero_cd_length * \
        le_to_int(bytes_new_memory_size_cd)
    new_memory_size_rd = is_nonzero_rd_length * \
        le_to_int(bytes_new_memory_size_rd)
    # Verify new_memory_size_cd is correct
    if is_nonzero_cd_length:
        assert sum(bytes_cd_offset[5:]) == 0
        curr.fixed_lookup(FixedTableTag.Range32,
                          [32 * new_memory_size_cd - (le_to_int(bytes_cd_offset) + le_to_int(bytes_cd_length))])
    # Verify new_memory_size_rd is correct
    if is_nonzero_rd_length:
        assert sum(bytes_rd_offset[5:]) == 0
        curr.fixed_lookup(FixedTableTag.Range32,
                          [32 * new_memory_size_rd - (le_to_int(bytes_rd_offset) + le_to_int(bytes_rd_length))])
    # Verify new_memory_size == \
    #   max(curr.call_state.memory_size, new_memory_size_cd, new_memory_size_rd)
    assert new_memory_size in [
        curr.call_state.memory_size,
        new_memory_size_cd,
        new_memory_size_rd,
    ]
    curr.decompress(new_memory_size - curr.call_state.memory_size, 4, 256)
    curr.decompress(new_memory_size - new_memory_size_cd, 4, 256)
    curr.decompress(new_memory_size - new_memory_size_rd, 4, 256)
    # Verify memory_gas_cost is correct
    curr_quad_memory_gas_cost = curr.allocate_byte(8)
    next_quad_memory_gas_cost = curr.allocate_byte(8)
    curr.fixed_lookup(FixedTableTag.Range512,
                      [512 * curr_quad_memory_gas_cost - curr.call_state.memory_size * curr.call_state.memory_size])
    curr.fixed_lookup(FixedTableTag.Range512,
                      [512 * next_quad_memory_gas_cost - new_memory_size * new_memory_size])
    memory_gas_cost = next_quad_memory_gas_cost - curr_quad_memory_gas_cost + \
        3 * (new_memory_size - curr.call_state.memory_size)

    # TODO: Handle EIP 150
    callee_gas_left = le_to_int(bytes_gas)

    # TODO: Verify gas (memory expansion and EIP 2929)
    next_gas_left = curr.call_state.gas_left - \
        (100 + callee_gas_left + memory_gas_cost)
    curr.decompress(next_gas_left, 8, 256)

    code_hash = curr.r_lookup(RWTableTag.AccountCodeHash,
                              [le_to_int(bytes_callee_address[:20])])[0]

    # TODO: Handle precompile
    if code_hash == random_linear_combine(EMPTY_CODE_HASH, r):
        assert result == 1

        assert next.execution_result != ExecutionResult.BEGIN_TX
        assert_state_transition(
            curr, next,
            rw_counter_diff=curr.rw_counter_diff,
            program_counter_diff=1,
            stack_pointer_diff=6,
            gas_left=next_gas_left,
            memory_size=new_memory_size,
        )
    else:
        rw_counter_end_of_revert = curr.call_lookup(
            CallTableTag.RWCounterEndOfRevert)
        tx_id = curr.call_lookup(CallTableTag.TxId)
        current_address = curr.call_lookup(CallTableTag.CalleeAddress)
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

        # Callee succeed but current call reverts at some point
        if result and not is_persistent:
            assert rw_counter_end_of_revert == callee_rw_counter_end_of_revert
            assert next.call_state.state_write_counter == curr.call_state.state_write_counter

        assert callee_caller_call_id == curr.call_state.call_id
        assert callee_tx_id == tx_id
        assert callee_depth == depth + 1
        assert callee_caller_address == current_address
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

        # TODO: Save current call_state

        assert next.execution_result != ExecutionResult.BEGIN_TX
        assert_state_transition(
            curr, next,
            rw_counter_diff=curr.rw_counter_diff,
            call_id=next.rw_counter,
            is_root=False,
            is_create=False,
            opcode_source=code_hash,
            program_counter=0,
            stack_pointer=1024,
            gas_left=callee_gas_left + (0 if is_zero_value else 2300),
            memory_size=0,
        )
