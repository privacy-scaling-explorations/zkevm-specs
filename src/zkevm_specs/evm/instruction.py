from __future__ import annotations
from enum import IntEnum, auto
from typing import Optional, Sequence, Tuple, Union

from ..util import (
    Array4,
    Array10,
    FQ,
    IntOrFQ,
    RLC,
    MAX_N_BYTES,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_MEMORY_SIZE,
    N_BYTES_GAS,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    MEMORY_EXPANSION_LINEAR_COEFF,
)
from .opcode import Opcode
from .step import StepState
from .table import (
    AccountFieldTag,
    BlockContextFieldTag,
    CallContextFieldTag,
    Tables,
    FixedTableTag,
    TxContextFieldTag,
    RW,
    RWTableTag,
)


class ConstraintUnsatFailure(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class TransitionKind(IntEnum):
    Same = auto()
    Delta = auto()
    To = auto()


class Transition:
    kind: TransitionKind
    value: Optional[int]

    def __init__(self, kind: TransitionKind, value: Optional[int] = None) -> None:
        self.kind = kind
        self.value = value

    def same() -> Transition:
        return Transition(TransitionKind.Same)

    def delta(delta: int):
        return Transition(TransitionKind.Delta, delta)

    def to(to: int):
        return Transition(TransitionKind.To, to)


class Instruction:
    randomness: int
    tables: Tables
    curr: StepState
    next: StepState

    # meta information
    is_first_step: bool
    is_last_step: bool

    # helper numbers
    rw_counter_offset: int = 0
    program_counter_offset: int = 0
    stack_pointer_offset: int = 0
    state_write_counter_offset: int = 0

    def __init__(
        self,
        randomness: int,
        tables: Tables,
        curr: StepState,
        next: StepState,
        is_first_step: bool,
        is_last_step: bool,
    ) -> None:
        self.randomness = randomness
        self.tables = tables
        self.curr = curr
        self.next = next
        self.is_first_step = is_first_step
        self.is_last_step = is_last_step

    def constrain_zero(self, value: FQ):
        assert value == 0, ConstraintUnsatFailure(f"Expected value to be 0, but got {value}")

    def constrain_equal(self, lhs: FQ, rhs: FQ):
        assert lhs == rhs, ConstraintUnsatFailure(f"Expected values to be equal, but got {lhs} and {rhs}")

    def constrain_bool(self, num: FQ):
        assert num.n in [0, 1], ConstraintUnsatFailure(f"Expected value to be a bool, but got {num}")

    def constrain_gas_left_not_underflow(self, gas_left: FQ):
        self.bytes_range_lookup(gas_left, N_BYTES_GAS)

    def constrain_step_state_transition(self, **kwargs: Transition):
        keys = set(
            [
                "rw_counter",
                "call_id",
                "is_root",
                "is_create",
                "code_source",
                "program_counter",
                "stack_pointer",
                "gas_left",
                "memory_size",
                "state_write_counter",
            ]
        )

        assert keys.issuperset(
            kwargs.keys()
        ), f"Invalid keys {list(set(kwargs.keys()).difference(keys))} for step state transition"

        for key, transition in kwargs.items():
            curr, next = getattr(self.curr, key), getattr(self.next, key)
            if transition.kind == TransitionKind.Same:
                assert next == curr, ConstraintUnsatFailure(f"State {key} should be same as {curr}, but got {next}")
            elif transition.kind == TransitionKind.Delta:
                assert next == curr + transition.value, ConstraintUnsatFailure(
                    f"State {key} should transit to {curr + transition.value}, but got {next}"
                )
            elif transition.kind == TransitionKind.To:
                assert next == transition.value, ConstraintUnsatFailure(
                    f"State {key} should transit to {transition.value}, but got {next}"
                )
            else:
                raise ValueError("unreacheable")

    def step_state_transition_to_new_context(
        self,
        rw_counter: Transition,
        call_id: Transition,
        is_root: Transition,
        is_create: Transition,
        code_source: Transition,
        gas_left: Transition,
        state_write_counter: Transition,
    ):
        self.constrain_step_state_transition(
            rw_counter=rw_counter,
            call_id=call_id,
            is_root=is_root,
            is_create=is_create,
            code_source=code_source,
            gas_left=gas_left,
            state_write_counter=state_write_counter,
            # Initailization unconditionally
            program_counter=Transition.to(0),
            stack_pointer=Transition.to(1024),
            memory_size=Transition.to(0),
        )

    def step_state_transition_in_same_context(
        self,
        opcode: int,
        rw_counter: Transition = Transition.same(),
        program_counter: Transition = Transition.same(),
        stack_pointer: Transition = Transition.same(),
        memory_size: Transition = Transition.same(),
        state_write_counter: Transition = Transition.same(),
        dynamic_gas_cost: int = 0,
    ):
        self.responsible_opcode_lookup(opcode)

        gas_cost = Opcode(opcode).constant_gas_cost() + dynamic_gas_cost
        self.constrain_gas_left_not_underflow(self.curr.gas_left - gas_cost)

        self.constrain_step_state_transition(
            rw_counter=rw_counter,
            program_counter=program_counter,
            stack_pointer=stack_pointer,
            gas_left=Transition.delta(-gas_cost),
            memory_size=memory_size,
            state_write_counter=state_write_counter,
            # Always stay same
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_source=Transition.same(),
        )

    def sum(self, values: Sequence[FQ]) -> FQ:
        return sum(values)

    def is_zero(self, value: Union[FQ, RLC]) -> bool:
        return value == 0

    def is_equal(self, lhs: Union[FQ, RLC], rhs: Union[FQ, RLC]) -> bool:
        if isinstance(lhs, RLC):
            lhs = lhs.value
        if isinstance(rhs, RLC):
            rhs = rhs.value
        return self.is_zero(lhs - rhs)

    def continuous_selectors(self, t: IntOrFQ, n: int) -> Sequence[bool]:
        t = t.n if isinstance(t, FQ) else t
        return [i < t for i in range(n)]

    def select(self, condition: bool, when_true: FQ, when_false: FQ) -> FQ:
        return when_true if condition else when_false

    def pair_select(self, value: int, lhs: int, rhs: int) -> Tuple[bool, bool]:
        return value == lhs, value == rhs

    def constant_divmod(self, numerator: IntOrFQ, denominator: IntOrFQ, n_bytes: int) -> Tuple[int, int]:
        quotient, remainder = divmod(FQ(numerator).n, FQ(denominator).n)
        quotient, remainder = FQ(quotient), FQ(remainder)
        self.bytes_range_lookup(quotient, n_bytes)
        return quotient, remainder

    def compare(self, lhs: FQ, rhs: FQ, n_bytes: int) -> Tuple[bool, bool]:
        assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        assert lhs.n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
        assert rhs.n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"

        return lhs.n < rhs.n, lhs.n == rhs.n

    def min(self, lhs: FQ, rhs: FQ, n_bytes: int) -> FQ:
        lt, _ = self.compare(lhs, rhs, n_bytes)
        return self.select(lt, lhs, rhs)

    def max(self, lhs: FQ, rhs: FQ, n_bytes: int) -> FQ:
        lt, _ = self.compare(lhs, rhs, n_bytes)
        return self.select(lt, rhs, lhs)

    def add_words(self, addends: Sequence[RLC]) -> Tuple[RLC, int]:
        addends_lo, addends_hi = list(zip(*map(self.word_to_lo_hi, addends)))

        carry_lo, sum_lo = divmod(self.sum(addends_lo).n, 1 << 128)
        carry_hi, sum_hi = divmod((self.sum(addends_hi) + carry_lo).n, 1 << 128)

        sum_bytes = sum_lo.to_bytes(16, "little") + sum_hi.to_bytes(16, "little")

        return RLC(sum_bytes, self.randomness), carry_hi

    def sub_word(self, minuend: RLC, subtrahend: RLC) -> Tuple[RLC, bool]:
        minuend_lo, minuend_hi = self.word_to_lo_hi(minuend)
        subtrahend_lo, subtrahend_hi = self.word_to_lo_hi(subtrahend)

        borrow_lo = minuend_lo.n < subtrahend_lo.n
        diff_lo = minuend_lo - subtrahend_lo + (1 << 128 if borrow_lo else 0)
        borrow_hi = minuend_hi.n < subtrahend_hi.n + borrow_lo
        diff_hi = minuend_hi - subtrahend_hi - borrow_lo + (1 << 128 if borrow_hi else 0)

        diff_bytes = diff_lo.n.to_bytes(16, "little") + diff_hi.n.to_bytes(16, "little")

        return RLC(diff_bytes, self.randomness), borrow_hi

    def mul_word_by_u64(self, multiplicand: RLC, multiplier: FQ) -> Tuple[RLC, int]:
        multiplicand_lo, multiplicand_hi = self.word_to_lo_hi(multiplicand)

        quotient_lo, product_lo = divmod((multiplicand_lo * multiplier).n, 1 << 128)
        quotient_hi, product_hi = divmod((multiplicand_hi * multiplier + quotient_lo).n, 1 << 128)

        product_bytes = product_lo.to_bytes(16, "little") + product_hi.to_bytes(16, "little")

        return RLC(product_bytes, self.randomness), quotient_hi

    def rlc_to_le_bytes(self, rlc: RLC) -> bytes:
        return rlc.le_bytes

    def rlc_to_int_unchecked(self, rlc: RLC, n_bytes: int) -> int:
        rlc_le_bytes = self.rlc_to_le_bytes(rlc)
        return self.bytes_to_int(rlc_le_bytes[:n_bytes]), self.is_zero(self.sum(rlc_le_bytes[n_bytes:]))

    def rlc_to_int_exact(self, rlc: RLC, n_bytes: int) -> int:
        rlc_le_bytes = self.rlc_to_le_bytes(rlc)

        if sum(rlc_le_bytes[n_bytes:]) > 0:
            raise ConstraintUnsatFailure(f"Value {rlc} has too many bytes to fit {n_bytes} bytes")

        return self.bytes_to_int(rlc_le_bytes[:n_bytes])

    def word_to_lo_hi(self, word: RLC) -> Tuple[Sequence[int], Sequence[int]]:
        word_le_bytes = self.rlc_to_le_bytes(word)
        assert len(word_le_bytes) == 32, "Expected word to contain 32 bytes"
        return self.bytes_to_fq(word_le_bytes[:16]), self.bytes_to_fq(word_le_bytes[16:])

    def int_to_rlc(self, value: int, n_bytes: int) -> RLC:
        return RLC(value, self.randomness, n_bytes)

    def bytes_to_int(self, value: Sequence[int]) -> int:
        assert len(value) <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        return int.from_bytes(value, "little")

    def bytes_to_fq(self, value: Sequence[int]) -> FQ:
        assert len(value) <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        return FQ(int.from_bytes(value, "little"))

    def range_lookup(self, value: FQ, range: int):
        self.tables.fixed_lookup([FixedTableTag.range_table_tag(range), value, 0, 0])

    def byte_range_lookup(self, value: FQ):
        assert isinstance(value, FQ), f"Expect type FQ, but get type {type(value)}"
        self.range_lookup(value, 256)

    def bytes_range_lookup(self, value: FQ, n_bytes: int) -> Sequence[int]:
        assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        assert isinstance(value, FQ)

        try:
            return value.n.to_bytes(n_bytes, "little")
        except OverflowError:
            raise ConstraintUnsatFailure(f"Value {value} has too many bytes to fit {n_bytes} bytes")

    def fixed_lookup(self, tag: FixedTableTag, inputs: Sequence[int]) -> Array4:
        return self.tables.fixed_lookup([tag] + inputs)

    def block_context_lookup(self, tag: BlockContextFieldTag, index: int = 0) -> int:
        return self.tables.block_lookup([tag, index])[2]

    def tx_context_lookup(self, tx_id: int, field_tag: TxContextFieldTag) -> Union[int, RLC]:
        return self.tables.tx_lookup([tx_id, field_tag, 0])[3]

    def tx_calldata_lookup(self, tx_id: int, index: int) -> int:
        return self.tables.tx_lookup([tx_id, TxContextFieldTag.CallData, index])[3]

    def bytecode_lookup(self, bytecode_hash: int, index: int, is_code: int) -> int:
        return self.tables.bytecode_lookup([bytecode_hash, index, Tables._, is_code])[2]

    def tx_gas_price(self, tx_id: int) -> int:
        return self.tx_context_lookup(tx_id, TxContextFieldTag.GasPrice)

    def responsible_opcode_lookup(self, opcode: int):
        self.fixed_lookup(FixedTableTag.ResponsibleOpcode, [self.curr.execution_state, opcode])

    def opcode_lookup(self, is_code: bool) -> int:
        index = self.curr.program_counter + self.program_counter_offset
        self.program_counter_offset += 1

        return self.opcode_lookup_at(index, is_code)

    def opcode_lookup_at(self, index: int, is_code: bool) -> int:
        if self.curr.is_root and self.curr.is_create:
            raise NotImplementedError(
                "The opcode source when is_root and is_create (root creation call) is not determined yet"
            )
        else:
            return self.bytecode_lookup(self.curr.code_source, index, is_code)

    def rw_lookup(self, rw: RW, tag: RWTableTag, inputs: Sequence[int], rw_counter: Optional[int] = None) -> Array10:
        if rw_counter is None:
            rw_counter = self.curr.rw_counter + self.rw_counter_offset
            self.rw_counter_offset += 1

        return self.tables.rw_lookup([rw_counter, rw, tag] + inputs)

    def state_write_only_persistent(
        self,
        tag: RWTableTag,
        inputs: Sequence[int],
        is_persistent: bool,
    ) -> Array10:
        assert tag.write_only_persistent()

        if is_persistent:
            return self.rw_lookup(RW.Write, tag, inputs)

        return 10 * [None]

    def state_write_with_reversion(
        self,
        tag: RWTableTag,
        inputs: Sequence[int],
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> Array10:
        assert tag.write_with_reversion()

        row = self.rw_lookup(RW.Write, tag, inputs)

        if state_write_counter is None:
            state_write_counter = self.curr.state_write_counter + self.state_write_counter_offset
            self.state_write_counter_offset += 1

        rw_counter = rw_counter_end_of_reversion - state_write_counter

        if not is_persistent:
            # Swap value and value_prev
            inputs = list(row[3:])
            inputs[-3], inputs[-4] = inputs[-4], inputs[-3]
            self.rw_lookup(RW.Write, tag, inputs, rw_counter=rw_counter)

        return row

    def call_context_lookup(
        self, field_tag: CallContextFieldTag, rw: RW = RW.Read, call_id: Optional[int] = None
    ) -> int:
        if call_id is None:
            call_id = self.curr.call_id

        return self.rw_lookup(rw, RWTableTag.CallContext, [call_id, field_tag])[-4]

    def stack_pop(self) -> Union[int, RLC]:
        stack_pointer_offset = self.stack_pointer_offset
        self.stack_pointer_offset += 1
        return self.stack_lookup(False, stack_pointer_offset)

    def stack_push(self) -> Union[int, RLC]:
        self.stack_pointer_offset -= 1
        return self.stack_lookup(True, self.stack_pointer_offset)

    def stack_lookup(self, rw: RW, stack_pointer_offset: int) -> Union[FQ, RLC]:
        stack_pointer = self.curr.stack_pointer + stack_pointer_offset
        return self.rw_lookup(rw, RWTableTag.Stack, [self.curr.call_id, stack_pointer])[-4]

    def memory_write(self, memory_address: int, call_id: Optional[int] = None) -> FQ:
        return self.memory_lookup(RW.Write, memory_address, call_id)

    def memory_lookup(self, rw: RW, memory_address: int, call_id: Optional[int] = None) -> FQ:
        if call_id is None:
            call_id = self.curr.call_id

        return self.rw_lookup(rw, RWTableTag.Memory, [call_id, memory_address])[-4]

    def tx_refund_read(self, tx_id) -> FQ:
        row = self.rw_lookup(RW.Read, RWTableTag.TxRefund, [tx_id])
        return row[-4]

    def account_read(self, account_address: int, account_field_tag: AccountFieldTag) -> FQ:
        row = self.rw_lookup(RW.Read, RWTableTag.Account, [account_address, account_field_tag])
        return row[-4]

    def account_write(
        self,
        account_address: int,
        account_field_tag: AccountFieldTag,
    ) -> Tuple[FQ, FQ]:
        row = self.rw_lookup(
            RW.Write,
            RWTableTag.Account,
            [account_address, account_field_tag],
        )
        return row[-4], row[-3]

    def account_write_with_reversion(
        self,
        account_address: int,
        account_field_tag: AccountFieldTag,
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> Tuple[FQ, FQ]:
        row = self.state_write_with_reversion(
            RWTableTag.Account,
            [account_address, account_field_tag],
            is_persistent,
            rw_counter_end_of_reversion,
            state_write_counter,
        )
        return row[-4], row[-3]

    def add_balance(self, account_address: int, values: Sequence[int]) -> Tuple[FQ, FQ]:
        balance, balance_prev = self.account_write(account_address, AccountFieldTag.Balance)
        result, carry = self.add_words([balance_prev, *values])
        self.constrain_equal(balance, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def add_balance_with_reversion(
        self,
        account_address: int,
        values: Sequence[int],
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> Tuple[FQ, FQ]:
        balance, balance_prev = self.account_write_with_reversion(
            account_address, AccountFieldTag.Balance, is_persistent, rw_counter_end_of_reversion, state_write_counter
        )
        result, carry = self.add_words([balance_prev, *values])
        self.constrain_equal(balance, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def sub_balance(self, account_address: int, values: Sequence[int]) -> Tuple[FQ, FQ]:
        balance, balance_prev = self.account_write(account_address, AccountFieldTag.Balance)
        result, carry = self.add_words([balance, *values])
        self.constrain_equal(balance_prev, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def sub_balance_with_reversion(
        self,
        account_address: int,
        values: Sequence[int],
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> Tuple[FQ, FQ]:
        balance, balance_prev = self.account_write_with_reversion(
            account_address, AccountFieldTag.Balance, is_persistent, rw_counter_end_of_reversion, state_write_counter
        )
        result, carry = self.add_words([balance, *values])
        self.constrain_equal(balance_prev, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def add_account_to_access_list(
        self,
        tx_id: int,
        account_address: int,
    ) -> FQ:
        row = self.rw_lookup(
            RW.Write,
            RWTableTag.TxAccessListAccount,
            [tx_id, account_address, 0, 1],
        )
        return row[-4] - row[-3]

    def add_account_to_access_list_with_reversion(
        self,
        tx_id: int,
        account_address: int,
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> FQ:
        row = self.state_write_with_reversion(
            RWTableTag.TxAccessListAccount,
            [tx_id, account_address, 0, 1],
            is_persistent,
            rw_counter_end_of_reversion,
            state_write_counter,
        )
        return row[-4] - row[-3]

    def add_account_storage_to_access_list(
        self,
        tx_id: int,
        account_address: int,
        storage_key: int,
    ) -> bool:
        row = self.rw_lookup(
            RW.Write,
            RWTableTag.TxAccessListAccountStorage,
            [tx_id, account_address, storage_key, 1],
        )
        return row[-4] - row[-3]

    def add_account_storage_to_access_list_with_reversion(
        self,
        tx_id: int,
        account_address: int,
        storage_key: int,
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> bool:
        row = self.state_write_with_reversion(
            RWTableTag.TxAccessListAccountStorage,
            [tx_id, account_address, storage_key, 1],
            is_persistent,
            rw_counter_end_of_reversion,
            state_write_counter,
        )
        return row[-4] - row[-3]

    def transfer_with_gas_fee(
        self,
        sender_address: int,
        receiver_address: int,
        value: int,
        gas_fee: int,
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        sender_balance_pair = self.sub_balance_with_reversion(
            sender_address,
            [value, gas_fee],
            is_persistent,
            rw_counter_end_of_reversion,
        )
        receiver_balance_pair = self.add_balance_with_reversion(
            receiver_address,
            [value],
            is_persistent,
            rw_counter_end_of_reversion,
        )
        return sender_balance_pair, receiver_balance_pair

    def transfer(
        self,
        sender_address: int,
        receiver_address: int,
        value: int,
        is_persistent: bool,
        rw_counter_end_of_reversion: int,
        state_write_counter: Optional[int] = None,
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        sender_balance_pair = self.sub_balance_with_reversion(
            sender_address,
            [value],
            is_persistent,
            rw_counter_end_of_reversion,
            state_write_counter,
        )
        receiver_balance_pair = self.add_balance_with_reversion(
            receiver_address,
            [value],
            is_persistent,
            rw_counter_end_of_reversion,
            None if state_write_counter is None else state_write_counter + 1,
        )
        return sender_balance_pair, receiver_balance_pair

    def memory_offset_and_length_to_int(self, offset: RLC, length: RLC) -> Tuple[int, int]:
        length = self.rlc_to_int_exact(length, N_BYTES_MEMORY_ADDRESS)
        if self.is_zero(length):
            return 0, 0

        offset = self.rlc_to_int_exact(offset, N_BYTES_MEMORY_ADDRESS)
        return offset, length

    def memory_gas_cost(self, memory_size: int) -> int:
        quadratic_cost, _ = self.constant_divmod(
            memory_size * memory_size, MEMORY_EXPANSION_QUAD_DENOMINATOR, N_BYTES_GAS
        )
        linear_cost = MEMORY_EXPANSION_LINEAR_COEFF * memory_size
        return quadratic_cost + linear_cost

    def memory_expansion_constant_length(self, offset: int, length: int) -> Tuple[int, int]:
        memory_size, _ = self.constant_divmod(length + offset + 31, 32, N_BYTES_MEMORY_SIZE)

        next_memory_size = self.max(self.curr.memory_size, memory_size, N_BYTES_MEMORY_SIZE)

        memory_gas_cost = self.memory_gas_cost(self.curr.memory_size)
        memory_gas_cost_next = self.memory_gas_cost(next_memory_size)
        memory_expansion_gas_cost = memory_gas_cost_next - memory_gas_cost

        return next_memory_size, memory_expansion_gas_cost

    def memory_expansion_dynamic_length(
        self,
        cd_offset: int,
        cd_length: int,
        rd_offset: Optional[int] = None,
        rd_length: Optional[int] = None,
    ) -> Tuple[int, int]:
        cd_memory_size, _ = self.constant_divmod(cd_offset + cd_length + 31, 32, N_BYTES_MEMORY_SIZE)
        next_memory_size = self.max(self.curr.memory_size, cd_memory_size, N_BYTES_MEMORY_SIZE)

        if rd_offset is not None:
            rd_memory_size, _ = self.constant_divmod(rd_offset + rd_length + 31, 32, N_BYTES_MEMORY_SIZE)
            next_memory_size = self.max(next_memory_size, rd_memory_size, N_BYTES_MEMORY_SIZE)

        memory_gas_cost = self.memory_gas_cost(self.curr.memory_size)
        memory_gas_cost_next = self.memory_gas_cost(next_memory_size)
        memory_expansion_gas_cost = memory_gas_cost_next - memory_gas_cost

        return next_memory_size, memory_expansion_gas_cost
