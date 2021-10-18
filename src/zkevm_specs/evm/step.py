from typing import Any, Sequence, Tuple, Union

from ..util import fp_mul, le_to_int, linear_combine
from .common_assert import assert_bool, assert_addition
from .execution_result.execution_result import ExecutionResult
from .table import Tables, FixedTableTag, TxTableTag, CallTableTag, RWTableTag, Tables
from .opcode import Opcode, OPCODE_INFO_MAP


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
        memory_size: int = 0,
        state_write_counter: int = 0,
        last_callee_id: int = 0,
        last_callee_returndata_offset: int = 0,
        last_callee_returndata_length: int = 0,
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

        for i in range(n):
            assert_bool(allocation[i])

        return allocation

    def allocate_byte(self, n: int) -> Sequence[int]:
        allocation = self.allocate(n)

        for i in range(n):
            self.byte_range_lookup(allocation[i])

        return allocation

    def is_zero(self, value: int) -> bool:
        value_inv = self.allocate(1)[0]
        is_zero = 1 - fp_mul(value, value_inv)

        assert value * is_zero == 0
        assert value_inv * is_zero == 0

        return is_zero

    def is_equal(self, lhs: int, rhs: int) -> bool:
        return self.is_zero(lhs - rhs)

    def decompress(self, value: int, n: int, r: int) -> Sequence[int]:
        allocation = self.allocate(n)

        assert value == linear_combine(allocation, r)
        for i in range(n):
            self.byte_range_lookup(allocation[i])

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

    def call_lookup(self, tag: CallTableTag, call_id: Union[int, None] = None) -> int:
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

        if tag in [
            RWTableTag.TxAccessListAccount,
            RWTableTag.TxAccessListStorageSlot,
            RWTableTag.TxRefund,
            RWTableTag.AccountNonce,
            RWTableTag.AccountBalance,
            RWTableTag.AccountCodeHash,
            RWTableTag.AccountStorage,
            RWTableTag.AccountDestructed,
        ]:
            allocation_revert = self.allocate(8)

            if rw_counter_end_of_revert is not None:
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
                elif tag == RWTableTag.AccountDestructed:
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
                # TODO: Add offset and verify creation code length when dealing with create
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

    def assert_sufficient_constant_gas(self, opcode: Opcode) -> int:
        next_gas_left = self.call_state.gas_left - OPCODE_INFO_MAP[opcode].constant_gas
        self.bytes_range_lookup(next_gas_left, 8)
        return next_gas_left

    def assert_transfer(
        self,
        caller_address: int,
        callee_address: int,
        bytes_value: Sequence[int],
        r: int,
        rw_counter_end_of_revert: Union[int, None] = None,
    ):
        caller_new_balance, caller_prev_balance = self.w_lookup(
            RWTableTag.AccountBalance, [caller_address], rw_counter_end_of_revert)[:2]
        callee_new_balance, callee_prev_balance = self.w_lookup(
            RWTableTag.AccountBalance, [callee_address], rw_counter_end_of_revert)[:2]

        # Verify caller's new balance is subtracted by value and not underflow
        bytes_caller_prev_balance = self.decompress(caller_prev_balance, 32, r)
        bytes_caller_new_balance = self.decompress(caller_new_balance, 32, r)
        caller_carries = self.allocate_bool(32)
        assert_addition(bytes_caller_new_balance, bytes_value, bytes_caller_prev_balance, caller_carries)
        assert caller_carries[31] == 0

        # Verify callee's new balance is added by value and not overflow
        bytes_callee_prev_balance = self.decompress(callee_prev_balance, 32, r)
        bytes_callee_new_balance = self.decompress(callee_new_balance, 32, r)
        callee_carries = self.allocate_bool(32)
        assert_addition(bytes_callee_prev_balance, bytes_value, bytes_callee_new_balance, callee_carries)
        assert callee_carries[31] == 0

    def assert_memory_expansion(
        self,
        bytes_cd_offset: Sequence[int],
        bytes_cd_length: Sequence[int],
        bytes_rd_offset: Sequence[int],
        bytes_rd_length: Sequence[int],
    ) -> Tuple[int, int]:
        cd_offset = le_to_int(bytes_cd_offset[:5])
        cd_length = le_to_int(bytes_cd_length)
        rd_offset = le_to_int(bytes_rd_offset[:5])
        rd_length = le_to_int(bytes_rd_length)

        next_memory_size = self.allocate(1)[0]

        has_cd_length = not self.is_zero(cd_length)
        has_rd_length = not self.is_zero(rd_length)
        bytes_next_memory_size_cd = self.allocate_byte(4)
        bytes_next_memory_size_rd = self.allocate_byte(4)
        next_memory_size_cd = has_cd_length * le_to_int(bytes_next_memory_size_cd)
        next_memory_size_rd = has_rd_length * le_to_int(bytes_next_memory_size_rd)

        # Verify next_memory_size_cd is correct
        if has_cd_length:
            assert sum(bytes_cd_offset[5:]) == 0
        self.fixed_lookup(FixedTableTag.Range32, [32 * next_memory_size_cd - has_cd_length * (cd_offset + cd_length)])

        # Verify next_memory_size_rd is correct
        if has_rd_length:
            assert sum(bytes_rd_offset[5:]) == 0
        self.fixed_lookup(FixedTableTag.Range32, [32 * next_memory_size_rd - has_rd_length * (rd_offset + rd_length)])

        # Verify next_memory_size == \
        #   max(self.call_state.memory_size, next_memory_size_cd, next_memory_size_rd)
        assert next_memory_size in [self.call_state.memory_size, next_memory_size_cd, next_memory_size_rd]
        self.bytes_range_lookup(next_memory_size - self.call_state.memory_size, 4)
        self.bytes_range_lookup(next_memory_size - next_memory_size_cd, 4)
        self.bytes_range_lookup(next_memory_size - next_memory_size_rd, 4)

        # Verify memory_gas_cost is correct
        curr_quad_memory_gas_cost = le_to_int(self.allocate_byte(8))
        next_quad_memory_gas_cost = le_to_int(self.allocate_byte(8))
        self.fixed_lookup(FixedTableTag.Range512,
                          [self.call_state.memory_size * self.call_state.memory_size - 512 * curr_quad_memory_gas_cost])
        self.fixed_lookup(FixedTableTag.Range512,
                          [next_memory_size * next_memory_size - 512 * next_quad_memory_gas_cost])
        memory_gas_cost = next_quad_memory_gas_cost - curr_quad_memory_gas_cost + \
            3 * (next_memory_size - self.call_state.memory_size)

        return next_memory_size, memory_gas_cost

    def assert_step_transition(self, next, **kwargs):
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

        assert_transition(self, next, ['rw_counter', 'execution_result'])
        assert_transition(self.call_state, next.call_state, [
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
