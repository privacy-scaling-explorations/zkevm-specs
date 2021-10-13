from enum import IntEnum, auto
from typing import Any, Sequence, Set, Tuple, Union


FQ = 21888242871839275222246405745257275088548364400416034343698204186575808495617
EMPTY_CODE_HASH = bytearray.fromhex(
    'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')


class FixedTableTag(IntEnum):
    Range32 = auto()
    Range64 = auto()
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
    opcode_source: int
    program_counter: int
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
    # lookup tables
    tables: Tables
    # helper numbers
    rw_counter_diff: int
    state_write_counter_diff: int
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

    def w_lookup(self, tag: RWTableTag, inputs: Sequence[int], rw_counter_end_of_revert: Union[int, None]) -> Sequence[int]:
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

    def opcode_lookup(self) -> Opcode:
        if self.call_state.is_create:
            if self.call_state.is_root:
                return Opcode(self.tx_lookup(TxTableTag.Calldata, [
                    self.call_state.opcode_source,
                    self.call_state.program_counter,
                ]))
            else:
                # TODO: Add offset and verify creation code length
                return Opcode(self.r_lookup(RWTableTag.Memory, [
                    self.call_state.opcode_source,
                    self.call_state.program_counter,
                ])[0])
        else:
            return self.bytecode_lookup([
                self.call_state.opcode_source,
                self.call_state.program_counter,
            ])


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


def main(curr: Step, next: Step, r: int, is_first_step: bool):
    if is_first_step or curr.execution_result == ExecutionResult.BEGIN_TX:
        begin_tx(curr, next, r, is_first_step)
    else:
        opcode = curr.opcode_lookup()

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
        is_empty_cost_hash = curr.is_zero(
            code_hash - linear_combine(EMPTY_CODE_HASH, r))

        # TODO: Handle precompile
        if is_empty_cost_hash:
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

    a = curr.r_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer])[0]
    b = curr.r_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer + 1])[0]
    c = curr.w_lookup(RWTableTag.Stack,
                      [curr.call_state.call_id, curr.call_state.stack_pointer + 1])[0]
    bytes_a = curr.decompress(a, 32, r)
    bytes_b = curr.decompress(c if swap else b, 32, r)
    bytes_c = curr.decompress(b if swap else c, 32, r)

    assert_addition(bytes_a, bytes_b, bytes_c, carries)

    assert_step_transition(
        curr, next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
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
    bytes_cd_offset = curr.decompress(cd_offset, 32, r)
    bytes_cd_length = curr.decompress(cd_length, 5, r)
    bytes_rd_offset = curr.decompress(rd_offset, 32, r)
    bytes_rd_length = curr.decompress(rd_length, 5, r)
    assert_bool(result)

    callee_address = le_to_int(bytes_callee_address[:20])

    # Verify transfer
    is_zero_value = curr.is_zero(value)
    if not is_zero_value:
        caller_address = curr.call_lookup(CallTableTag.CalleeAddress)
        bytes_value = curr.decompress(value, 32, r)
        assert_transfer(curr, caller_address, callee_address, bytes_value, r)

    # Verify memory expansion
    is_nonzero_cd_length = not curr.is_zero(le_to_int(bytes_cd_length))
    is_nonzero_rd_length = not curr.is_zero(le_to_int(bytes_rd_length))
    next_memory_size = curr.allocate(1)[0]
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

    # Verify gas cost
    tx_id = curr.call_lookup(CallTableTag.TxId)
    is_cold_access = 1 - \
        curr.w_lookup(RWTableTag.TxAccessListAccount,
                      [tx_id, callee_address, 1])[0]
    code_hash = curr.r_lookup(RWTableTag.AccountCodeHash, [callee_address])[0]
    is_empty_cost_hash = curr.is_zero(
        code_hash - linear_combine(EMPTY_CODE_HASH, r))
    is_account_empty = curr.is_zero(curr.r_lookup(RWTableTag.AccountNonce, [callee_address])[0]) * \
        curr.is_zero(curr.r_lookup(RWTableTag.AccountBalance, [callee_address])[0]) * \
        is_empty_cost_hash
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
    if is_empty_cost_hash:
        assert result == 1

        assert_step_transition(
            curr, next,
            rw_counter_diff=curr.rw_counter_diff,
            execution_result_not=ExecutionResult.BEGIN_TX,
            state_write_counter_diff=curr.state_write_counter_diff,
            program_counter_diff=1,
            stack_pointer_diff=6,
            gas_left=next_gas_left,
            memory_size=next_memory_size,
        )
    else:
        # Save caller's call state
        for (tag, value) in [
            (CallTableTag.IsRoot, curr.call_state.is_root),
            (CallTableTag.IsCreate, curr.call_state.is_create),
            (CallTableTag.OpcodeSource, curr.call_state.opcode_source),
            (CallTableTag.ProgramCounter, curr.call_state.program_counter),
            (CallTableTag.StackPointer, curr.call_state.stack_pointer),
            (CallTableTag.GasLeft, curr.call_state.gas_left),
            (CallTableTag.MemorySize, curr.call_state.memory_size),
            (CallTableTag.StateWriteCounter, curr.call_state.state_write_counter),
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
