from __future__ import annotations
from enum import IntEnum, auto
from typing import Optional, Sequence, Tuple, Union

from ..util import Array4, Array8, linear_combine, RLCStore
from .opcode import Opcode, OPCODE_INFO_MAP
from .step import StepState
from .table import CallContextFieldTag, Tables, FixedTableTag, TxContextFieldTag, RWTableTag, Tables


class ConstraintUnsatFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class TransitionKind(IntEnum):
    Persistent = auto()
    Delta = auto()
    To = auto()


class Transition:
    kind: TransitionKind
    value: Optional[int]

    def __init__(self, kind: TransitionKind, value: Optional[int] = None) -> None:
        self.kind = kind
        self.value = value

    def persistent() -> Transition:
        return Transition(TransitionKind.Persistent)

    def delta(delta: int):
        return Transition(TransitionKind.Delta, delta)

    def to(to: int):
        return Transition(TransitionKind.To, to)


class Instruction:
    rlc_store: RLCStore
    tables: Tables
    curr: StepState
    next: StepState

    # helper numbers
    cell_offset: int = 0
    rw_counter_offset: int = 0
    program_counter_offset: int = 0
    stack_pointer_offset: int = 0
    state_write_counter_offset: int = 0

    def __init__(self, rlc_store: RLCStore, tables: Tables, curr: StepState, next: StepState) -> None:
        self.rlc_store = rlc_store
        self.tables = tables
        self.curr = curr
        self.next = next

    def constrain_zero(self, value: int):
        assert value == 0

    def constrain_equal(self, lhs: int, rhs: int):
        self.constrain_zero(lhs - rhs)

    def constrain_bool(self, value: int):
        assert value in [0, 1]

    def constrain_word_addition(self, a: int, b: int, c: int):
        a_bytes = self.rlc_to_bytes(a, 32)
        b_bytes = self.rlc_to_bytes(b, 32)
        c_bytes = self.rlc_to_bytes(c, 32)

        a_lo = self.bytes_to_int(a_bytes[:16])
        a_hi = self.bytes_to_int(a_bytes[16:])
        b_lo = self.bytes_to_int(b_bytes[:16])
        b_hi = self.bytes_to_int(b_bytes[16:])
        c_lo = self.bytes_to_int(c_bytes[:16])
        c_hi = self.bytes_to_int(c_bytes[16:])
        carry_lo = (a_lo + b_lo) > c_lo
        carry_hi = (a_hi + b_hi + carry_lo) > c_hi

        self.constrain_equal(a_lo + b_lo, c_lo + carry_lo * (1 << 128))
        self.constrain_equal(a_hi + b_hi + carry_lo, c_hi + carry_hi * (1 << 128))

    def constrain_state_transition(self, **kwargs: Transition):
        for key in [
            'rw_counter',
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
        ]:
            curr, next = getattr(self.curr, key), getattr(self.next, key)
            transition = kwargs.get(key, Transition.persistent())
            if transition.kind == TransitionKind.Persistent:
                assert next == curr, \
                    ConstraintUnsatFailure(f"state {key} should be persistent as {curr}, but got {next}")
            elif transition.kind == TransitionKind.Delta:
                assert next == curr + transition.value, \
                    ConstraintUnsatFailure(f"state {key} should transit to ${curr + transition.value}, but got {next}")
            elif transition.kind == TransitionKind.To:
                assert next == transition.value, \
                    ConstraintUnsatFailure(f"state {key} should transit to ${transition.value}, but got {next}")
            else:
                raise ValueError("unreacheable")

    def constrain_same_context_state_transition(
        self,
        opcode: Opcode,
        rw_counter: Transition = Transition.persistent(),
        program_counter: Transition = Transition.persistent(),
        stack_pointer: Transition = Transition.persistent(),
        memory_size: Transition = Transition.persistent(),
        dynamic_gas_cost: int = 0,
    ):
        gas_cost = OPCODE_INFO_MAP[opcode].constant_gas + dynamic_gas_cost

        self.int_to_bytes(self.curr.gas_left - gas_cost, 8)

        self.constrain_state_transition(
            rw_counter=rw_counter,
            program_counter=program_counter,
            stack_pointer=stack_pointer,
            memory_size=memory_size,
            gas_left=Transition.delta(-gas_cost),
        )

    def is_zero(self, value: int) -> bool:
        return value == 0

    def is_equal(self, lhs: int, rhs: int) -> bool:
        return self.is_zero(lhs - rhs)

    def continuous_selectors(self, t: int, n: int) -> Sequence[int]:
        return [i < t for i in range(n)]

    def select(self, condition: bool, when_true: int, when_false: int) -> int:
        return when_true if condition else when_false

    def pair_select(self, value: int, lhs: int, rhs: int) -> Tuple[bool, bool]:
        return value == lhs, value == rhs

    def rlc_to_bytes(self, value: int, n_bytes: int) -> Sequence[int]:
        bytes = self.rlc_store.to_bytes(value)
        if len(bytes) > n_bytes and any(bytes[n_bytes:]):
            raise ConstraintUnsatFailure(f"{value} is too many bytes to fit {n_bytes} bytes")
        return list(bytes) + (n_bytes - len(bytes)) * [0]

    def bytes_to_rlc(self, bytes: Sequence[int]) -> int:
        return self.rlc_store.to_rlc(bytes)

    def int_to_bytes(self, value: int, n_bytes: int) -> Sequence[int]:
        try:
            return value.to_bytes(n_bytes, 'little')
        except OverflowError:
            raise ConstraintUnsatFailure(f"{value} is too many bytes to fit {n_bytes} bytes")

    def bytes_to_int(self, bytes: Sequence[int]) -> int:
        assert len(bytes) <= 31, "too many bytes to composite an integer in field"
        return linear_combine(bytes, 256)

    def byte_range_lookup(self, input: int):
        self.tables.fixed_lookup([FixedTableTag.Range256, input, 0, 0])

    def fixed_lookup(self, tag: FixedTableTag, inputs: Sequence[int]) -> Array4:
        return self.tables.fixed_lookup([tag] + inputs)

    def tx_lookup(self, tx_id: int, tag: TxContextFieldTag, index: int = 0) -> int:
        return self.tables.tx_lookup([tx_id, tag, index])[3]

    def bytecode_lookup(self, bytecode_hash: int, index: int) -> int:
        return self.tables.bytecode_lookup([bytecode_hash, index])[2]

    def rw_lookup(self, is_write: bool, tag: RWTableTag, inputs: Sequence[int], rw_counter: Optional[int] = None) -> Array8:
        if rw_counter is None:
            rw_counter = self.curr.rw_counter + self.rw_counter_offset
            self.rw_counter_offset += 1

        return self.tables.rw_lookup([rw_counter, is_write, tag] + inputs)

    def r_lookup(self, tag: RWTableTag, inputs: Sequence[int]) -> Array8:
        return self.rw_lookup(False, tag, inputs)

    def w_lookup(
        self,
        tag: RWTableTag,
        inputs: Sequence[int],
        is_persistent: bool = True,
        rw_counter_end_of_reversion: int = 0,
    ) -> Array8:
        if tag.write_only_persistent() and not is_persistent:
            return self.rw_lookup(True, tag, inputs)

        row = self.rw_lookup(True, tag, inputs)

        if tag.write_with_reversion():
            rw_counter = rw_counter_end_of_reversion - self.curr.state_write_counter
            self.curr.state_write_counter += 1

            if not is_persistent:
                # Swap value and value_prev
                inputs = row[3:]
                if tag == RWTableTag.TxAccessListAccount:
                    inputs[2], inputs[3] = inputs[3], inputs[2]
                elif tag == RWTableTag.TxAccessListStorageSlot:
                    inputs[3], inputs[4] = inputs[4], inputs[3]
                elif tag == RWTableTag.Account:
                    inputs[2], inputs[3] = inputs[3], inputs[2]
                elif tag == RWTableTag.AccountStorage:
                    inputs[3], inputs[4] = inputs[4], inputs[3]
                elif tag == RWTableTag.AccountDestructed:
                    inputs[2], inputs[3] = inputs[3], inputs[2]
                self.rw_lookup(True, tag, inputs, rw_counter=rw_counter)

        return row

    def opcode_lookup(self) -> int:
        index = self.curr.program_counter + self.program_counter_offset
        self.program_counter_offset += 1

        return self.opcode_lookup_at(index)

    def opcode_lookup_at(self, index: int) -> int:
        if self.curr.is_root and self.curr.is_create:
            return self.tx_lookup(self.curr.opcode_source, TxContextFieldTag.Calldata, index)
        else:
            return self.bytecode_lookup(self.curr.opcode_source, index)

    def call_context_lookup(self, tag: CallContextFieldTag, is_write: bool = False, call_id: Union[int, None] = None) -> int:
        if call_id is None:
            call_id = self.curr.call_id

        return self.rw_lookup(is_write, RWTableTag.CallContext, [call_id, tag])[5]

    def stack_pop(self) -> int:
        stack_pointer_offset = self.stack_pointer_offset
        self.stack_pointer_offset += 1
        return self.stack_lookup(False, stack_pointer_offset)

    def stack_push(self) -> int:
        self.stack_pointer_offset -= 1
        return self.stack_lookup(True, self.stack_pointer_offset)

    def stack_lookup(self, is_write: bool, stack_pointer_offset: int) -> int:
        stack_pointer = self.curr.stack_pointer + stack_pointer_offset
        return self.rw_lookup(is_write, RWTableTag.Stack, [self.curr.call_id, stack_pointer])[5]
