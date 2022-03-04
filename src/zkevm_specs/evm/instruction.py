from __future__ import annotations
from enum import IntEnum, auto
from typing import Optional, Sequence, Tuple, Union

from ..util import (
    FQ,
    IntOrFQ,
    RLC,
    Expression,
    ExpressionImpl,
    cast_expr,
    MAX_N_BYTES,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_MEMORY_SIZE,
    N_BYTES_GAS,
    GAS_COST_COPY,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    MEMORY_EXPANSION_LINEAR_COEFF,
)
from .execution_state import ExecutionState
from .opcode import Opcode
from .step import StepState
from .table import (
    AccountFieldTag,
    BlockContextFieldTag,
    CallContextFieldTag,
    FixedTableRow,
    RWTableRow,
    Tables,
    FixedTableTag,
    TxContextFieldTag,
    RW,
    RWTableTag,
    TxLogFieldTag,
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
    value: Union[int, FQ, RLC]

    def __init__(self, kind: TransitionKind, value: Union[int, FQ, RLC] = 0) -> None:
        self.kind = kind
        self.value = value

    @staticmethod
    def same() -> Transition:
        return Transition(TransitionKind.Same)

    @staticmethod
    def delta(delta: Union[int, FQ, RLC]):
        return Transition(TransitionKind.Delta, delta)

    @staticmethod
    def to(to: Union[int, FQ, RLC]):
        return Transition(TransitionKind.To, to)


class ReversionInfo:
    rw_counter_end_of_reversion: FQ
    is_persistent: FQ
    state_write_counter: FQ

    def __init__(
        self,
        rw_counter_end_of_reversion: Expression,
        is_persistent: Expression,
        state_write_counter: Expression,
    ) -> None:
        self.rw_counter_end_of_reversion = rw_counter_end_of_reversion.expr()
        self.is_persistent = is_persistent.expr()
        self.state_write_counter = state_write_counter.expr()

    def rw_counter(self) -> FQ:
        rw_counter = self.rw_counter_end_of_reversion - self.state_write_counter
        self.state_write_counter += 1
        return rw_counter


class Instruction:
    randomness: FQ
    tables: Tables
    curr: StepState
    next: Optional[StepState]

    # meta information
    is_first_step: bool
    is_last_step: bool

    # helper numbers
    rw_counter_offset: int = 0
    program_counter_offset: int = 0
    stack_pointer_offset: int = 0
    log_index_offset: int = 0

    def __init__(
        self,
        randomness: FQ,
        tables: Tables,
        curr: StepState,
        next: Optional[StepState],
        is_first_step: bool,
        is_last_step: bool,
    ) -> None:
        self.randomness = randomness
        self.tables = tables
        self.curr = curr
        self.next = next
        self.is_first_step = is_first_step
        self.is_last_step = is_last_step

    def constrain_zero(self, value: Expression):
        assert value.expr() == 0, ConstraintUnsatFailure(f"Expected value to be 0, but got {value}")

    def constrain_equal(self, lhs: Expression, rhs: Expression):
        assert lhs.expr() == rhs.expr(), ConstraintUnsatFailure(
            f"Expected values to be equal, but got {lhs} and {rhs}"
        )

    def constrain_bool(self, num: Expression):
        assert num.expr() in [0, 1], ConstraintUnsatFailure(
            f"Expected value to be a bool, but got {num}"
        )

    def constrain_gas_left_not_underflow(self, gas_left: Expression):
        self.range_check(gas_left, N_BYTES_GAS)

    def constrain_execution_state_transition(self):
        curr, next = self.curr.execution_state, self.next.execution_state

        # ExecutionState transition constraint for special ones
        if curr == ExecutionState.EndTx:
            assert next in [ExecutionState.BeginTx, ExecutionState.EndBlock]
        elif curr == ExecutionState.EndBlock:
            assert next == ExecutionState.EndBlock

        # Negation ExecutionState transition constraint for rest ones
        if next == ExecutionState.BeginTx:
            assert curr == ExecutionState.EndTx
        elif next == ExecutionState.EndTx:
            assert curr.halts() or curr == ExecutionState.BeginTx
        elif next == ExecutionState.EndBlock:
            assert curr in [ExecutionState.EndTx, ExecutionState.EndBlock]
        elif next == ExecutionState.CopyToMemory:
            assert curr in [ExecutionState.CopyToMemory, ExecutionState.CALLDATACOPY]

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
                "log_index",
            ]
        )

        assert keys.issuperset(
            kwargs.keys()
        ), f"Invalid keys {list(set(kwargs.keys()).difference(keys))} for step state transition"

        for key, transition in kwargs.items():
            curr, next = getattr(self.curr, key), getattr(self.next, key)
            if isinstance(curr, int):
                curr = FQ(curr)
            if isinstance(next, int):
                next = FQ(next)
            if transition.kind == TransitionKind.Same:
                assert next.expr() == curr.expr(), ConstraintUnsatFailure(
                    f"State {key} should be same as {curr}, but got {next}"
                )
            elif transition.kind == TransitionKind.Delta:
                if isinstance(transition.value, int):
                    transition.value = FQ(transition.value)
                assert next.expr() == curr.expr() + transition.value.expr(), ConstraintUnsatFailure(
                    f"State {key} should transit to {curr} + {transition.value}, but got {next}"
                )
            elif transition.kind == TransitionKind.To:
                if isinstance(transition.value, int):
                    transition.value = FQ(transition.value)
                assert next.expr() == transition.value.expr(), ConstraintUnsatFailure(
                    f"State {key} should transit to {transition.value}, but got {next}"
                )
            else:
                raise ValueError("Unreacheable")

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
        opcode: Expression,
        rw_counter: Transition = Transition.same(),
        program_counter: Transition = Transition.same(),
        stack_pointer: Transition = Transition.same(),
        memory_size: Transition = Transition.same(),
        state_write_counter: Transition = Transition.same(),
        dynamic_gas_cost: IntOrFQ = 0,
        log_index: Transition = Transition.same(),
    ):
        self.responsible_opcode_lookup(opcode)

        gas_cost = FQ(Opcode(opcode.expr().n).constant_gas_cost() + dynamic_gas_cost)
        self.constrain_gas_left_not_underflow(self.curr.gas_left - gas_cost)

        self.constrain_step_state_transition(
            rw_counter=rw_counter,
            program_counter=program_counter,
            stack_pointer=stack_pointer,
            gas_left=Transition.delta(-gas_cost),
            memory_size=memory_size,
            state_write_counter=state_write_counter,
            log_index=log_index,
            # Always stay same
            call_id=Transition.same(),
            is_root=Transition.same(),
            is_create=Transition.same(),
            code_source=Transition.same(),
        )

    def sum(self, values: Sequence[IntOrFQ]) -> FQ:
        return FQ(sum(values))

    def is_zero(self, value: Expression) -> FQ:
        return FQ(value.expr() == 0)

    def is_equal(self, lhs: Expression, rhs: Expression) -> FQ:
        return self.is_zero(lhs.expr() - rhs.expr())

    def continuous_selectors(self, value: Expression, n: int) -> Sequence[FQ]:
        return [FQ(i < value.expr().n) for i in range(n)]

    def select(
        self, condition: FQ, when_true: ExpressionImpl, when_false: ExpressionImpl
    ) -> ExpressionImpl:
        assert condition in [0, 1], "Condition of select should be a checked bool"
        return when_true if condition == 1 else when_false

    def pair_select(self, value: Expression, lhs: Expression, rhs: Expression) -> Tuple[FQ, FQ]:
        return FQ(value.expr() == lhs.expr()), FQ(value.expr() == rhs.expr())

    def constant_divmod(
        self, numerator: Expression, denominator: Expression, n_bytes: int
    ) -> Tuple[FQ, FQ]:
        quotient, remainder = divmod(numerator.expr().n, denominator.expr().n)
        self.range_check(FQ(quotient), n_bytes)
        return FQ(quotient), FQ(remainder)

    def compare(self, lhs: Expression, rhs: Expression, n_bytes: int) -> Tuple[FQ, FQ]:
        assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        assert lhs.expr().n < 256**n_bytes, f"lhs {lhs} exceeds the range of {n_bytes} bytes"
        assert rhs.expr().n < 256**n_bytes, f"rhs {rhs} exceeds the range of {n_bytes} bytes"
        return FQ(lhs.expr().n < rhs.expr().n), FQ(lhs.expr().n == rhs.expr().n)

    def min(self, lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
        lt, _ = self.compare(lhs, rhs, n_bytes)
        return cast_expr(self.select(lt, lhs, rhs), FQ)

    def max(self, lhs: Expression, rhs: Expression, n_bytes: int) -> FQ:
        lt, _ = self.compare(lhs, rhs, n_bytes)
        return cast_expr(self.select(lt, rhs, lhs), FQ)

    def add_words(self, addends: Sequence[RLC]) -> Tuple[RLC, FQ]:
        addends_lo, addends_hi = list(zip(*map(self.word_to_lo_hi, addends)))

        carry_lo, sum_lo = divmod(self.sum(addends_lo).n, 1 << 128)
        carry_hi, sum_hi = divmod((self.sum(addends_hi) + carry_lo).n, 1 << 128)

        sum_bytes = sum_lo.to_bytes(16, "little") + sum_hi.to_bytes(16, "little")

        return self.rlc_encode(sum_bytes), FQ(carry_hi)

    def sub_word(self, minuend: RLC, subtrahend: RLC) -> Tuple[RLC, FQ]:
        minuend_lo, minuend_hi = self.word_to_lo_hi(minuend)
        subtrahend_lo, subtrahend_hi = self.word_to_lo_hi(subtrahend)

        borrow_lo = minuend_lo.n < subtrahend_lo.n
        diff_lo = minuend_lo - subtrahend_lo + (1 << 128 if borrow_lo else 0)
        borrow_hi = minuend_hi.n < subtrahend_hi.n + borrow_lo
        diff_hi = minuend_hi - subtrahend_hi - borrow_lo + (1 << 128 if borrow_hi else 0)

        diff_bytes = diff_lo.n.to_bytes(16, "little") + diff_hi.n.to_bytes(16, "little")

        return self.rlc_encode(diff_bytes), FQ(borrow_hi)

    def mul_word_by_u64(self, multiplicand: RLC, multiplier: Expression) -> Tuple[RLC, FQ]:
        multiplicand_lo, multiplicand_hi = self.word_to_lo_hi(multiplicand)

        quotient_lo, product_lo = divmod((multiplicand_lo * multiplier.expr()).n, 1 << 128)
        quotient_hi, product_hi = divmod(
            (multiplicand_hi * multiplier.expr() + quotient_lo).n, 1 << 128
        )

        product_bytes = product_lo.to_bytes(16, "little") + product_hi.to_bytes(16, "little")

        return self.rlc_encode(product_bytes), FQ(quotient_hi)

    def rlc_to_fq_unchecked(self, word: RLC, n_bytes: int) -> Tuple[FQ, FQ]:
        return self.bytes_to_fq(word.le_bytes[:n_bytes]), self.is_zero(
            self.sum(word.le_bytes[n_bytes:])
        )

    def rlc_to_fq_exact(self, word: RLC, n_bytes: int) -> FQ:
        if any(word.le_bytes[n_bytes:]):
            raise ConstraintUnsatFailure(f"Word {word} has too many bytes to fit {n_bytes} bytes")

        return self.bytes_to_fq(word.le_bytes[:n_bytes])

    def word_to_lo_hi(self, word: RLC) -> Tuple[FQ, FQ]:
        assert len(word.le_bytes) == 32, "Expected word to contain 32 bytes"
        return self.bytes_to_fq(word.le_bytes[:16]), self.bytes_to_fq(word.le_bytes[16:])

    def bytes_to_fq(self, value: bytes) -> FQ:
        assert len(value) <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        return FQ(int.from_bytes(value, "little"))

    def rlc_encode(self, value: bytes) -> RLC:
        return RLC(value, self.randomness)

    def range_lookup(self, value: Expression, range: int):
        self.fixed_lookup(FixedTableTag.range_table_tag(range), value)

    def byte_range_lookup(self, value: Expression):
        self.range_lookup(value, 256)

    def range_check(self, value: Expression, n_bytes: int) -> bytes:
        assert n_bytes <= MAX_N_BYTES, "Too many bytes to composite an integer in field"
        try:
            return value.expr().n.to_bytes(n_bytes, "little")
        except OverflowError:
            raise ConstraintUnsatFailure(f"Value {value} has too many bytes to fit {n_bytes} bytes")

    def fixed_lookup(
        self,
        tag: FixedTableTag,
        value0: Expression,
        value1: Expression = None,
        value2: Expression = None,
    ) -> FixedTableRow:
        return self.tables.fixed_lookup(FQ(tag), value0, value1, value2)

    def block_context_lookup(
        self, field_tag: BlockContextFieldTag, block_number: Expression = FQ(0)
    ) -> Expression:
        return self.tables.block_lookup(FQ(field_tag), block_number).value

    def tx_context_lookup(self, tx_id: Expression, field_tag: TxContextFieldTag) -> Expression:
        return self.tables.tx_lookup(tx_id, FQ(field_tag)).value

    def tx_calldata_lookup(self, tx_id: Expression, call_data_index: Expression) -> Expression:
        return self.tables.tx_lookup(tx_id, FQ(TxContextFieldTag.CallData), call_data_index).value

    def tx_log_lookup(self, field_tag: TxContextFieldTag, index: int = 0) -> Union[int, RLC]:
        return self.rw_lookup(RW.Write, RWTableTag.TxLog, [self.curr.log_index, index, field_tag])[-4]

    def bytecode_lookup(
        self, bytecode_hash: Expression, index: Expression, is_code: bool
    ) -> Expression:
        return self.tables.bytecode_lookup(bytecode_hash, index, FQ(is_code)).byte

    def tx_gas_price(self, tx_id: Expression) -> RLC:
        return cast_expr(self.tx_context_lookup(tx_id, TxContextFieldTag.GasPrice), RLC)

    def responsible_opcode_lookup(self, opcode: Expression):
        self.fixed_lookup(FixedTableTag.ResponsibleOpcode, FQ(self.curr.execution_state), opcode)

    def opcode_lookup(self, is_code: bool) -> FQ:
        index = self.curr.program_counter + self.program_counter_offset
        self.program_counter_offset += 1
        return self.opcode_lookup_at(index, is_code)

    def opcode_lookup_at(self, index: FQ, is_code: bool) -> FQ:
        if self.curr.is_root and self.curr.is_create:
            raise NotImplementedError(
                "The opcode source when is_root and is_create (root creation call) is not determined yet"
            )
        else:
            return self.bytecode_lookup(self.curr.code_source, index, is_code).expr()

    def rw_lookup(
        self,
        rw: RW,
        tag: RWTableTag,
        key1: Expression = None,
        key2: Expression = None,
        key3: Expression = None,
        value: Expression = None,
        value_prev: Expression = None,
        aux0: Expression = None,
        aux1: Expression = None,
        rw_counter: Expression = None,
    ) -> RWTableRow:
        if rw_counter is None:
            rw_counter = self.curr.rw_counter + self.rw_counter_offset
            self.rw_counter_offset += 1

        return self.tables.rw_lookup(
            rw_counter,
            FQ(rw),
            FQ(tag),
            key1,
            key2,
            key3,
            value,
            value_prev,
            aux0,
            aux1,
        )

    def state_write(
        self,
        tag: RWTableTag,
        key1: Expression = None,
        key2: Expression = None,
        key3: Expression = None,
        value: Expression = None,
        value_prev: Expression = None,
        aux0: Expression = None,
        aux1: Expression = None,
        reversion_info: ReversionInfo = None,
    ) -> RWTableRow:
        assert tag.write_with_reversion()

        row = self.rw_lookup(RW.Write, tag, key1, key2, key3, value, value_prev, aux0, aux1)

        if reversion_info is not None and reversion_info.is_persistent == 0:
            self.tables.rw_lookup(
                rw_counter=reversion_info.rw_counter(),
                rw=FQ(RW.Write),
                tag=FQ(tag),
                key1=row.key1,
                key2=row.key2,
                key3=row.key3,
                # Swap value and value_prev
                value=row.value_prev,
                value_prev=row.value,
                aux0=row.aux0,
                aux1=row.aux1,
            )

        return row

    def call_context_lookup(
        self, field_tag: CallContextFieldTag, rw: RW = RW.Read, call_id: Expression = None
    ) -> Expression:
        if call_id is None:
            call_id = self.curr.call_id
        return self.rw_lookup(rw, RWTableTag.CallContext, call_id, FQ(field_tag)).value

    def reversion_info(self, call_id: Expression = None) -> ReversionInfo:
        rw_counter_end_of_reversion = self.call_context_lookup(
            CallContextFieldTag.RwCounterEndOfReversion, call_id=call_id
        )
        is_persistent = self.call_context_lookup(CallContextFieldTag.IsPersistent, call_id=call_id)
        return ReversionInfo(
            rw_counter_end_of_reversion, is_persistent, self.curr.state_write_counter
        )

    def stack_pop(self) -> RLC:
        stack_pointer_offset = self.stack_pointer_offset
        self.stack_pointer_offset += 1
        return self.stack_lookup(RW.Read, FQ(stack_pointer_offset))

    def stack_push(self) -> RLC:
        self.stack_pointer_offset -= 1
        return self.stack_lookup(RW.Write, FQ(self.stack_pointer_offset))

    def stack_lookup(self, rw: RW, stack_pointer_offset: Expression) -> RLC:
        stack_pointer = self.curr.stack_pointer + stack_pointer_offset
        return cast_expr(
            self.rw_lookup(rw, RWTableTag.Stack, self.curr.call_id, stack_pointer).value, RLC
        )

    def memory_write(self, memory_address: Expression, call_id: Expression = None) -> FQ:
        return self.memory_lookup(RW.Write, memory_address, call_id)

    def memory_read(self, memory_address: int, call_id: Optional[int] = None) -> int:
        return self.memory_lookup(RW.Read, memory_address, call_id)

    def memory_lookup(self, rw: RW, memory_address: Expression, call_id: Expression = None) -> FQ:
        if call_id is None:
            call_id = self.curr.call_id
        return cast_expr(self.rw_lookup(rw, RWTableTag.Memory, call_id, memory_address).value, FQ)

    def tx_refund_read(self, tx_id: Expression) -> FQ:
        return cast_expr(self.rw_lookup(RW.Read, RWTableTag.TxRefund, tx_id).value, FQ)

    def tx_refund_write(
        self,
        tx_id: Expression,
        reversion_info: ReversionInfo = None,
    ) -> Tuple[FQ, FQ]:
        row = self.state_write(
            RWTableTag.TxRefund,
            tx_id,
            reversion_info=reversion_info,
        )
        return cast_expr(row.value, FQ), cast_expr(row.value_prev, FQ)

    def account_read(self, account_address: Expression, account_field_tag: AccountFieldTag) -> RLC:
        return cast_expr(
            self.rw_lookup(
                RW.Read, RWTableTag.Account, account_address, FQ(account_field_tag)
            ).value,
            RLC,
        )

    def account_write(
        self,
        account_address: Expression,
        account_field_tag: AccountFieldTag,
        reversion_info: ReversionInfo = None,
    ) -> Tuple[Expression, Expression]:
        row = self.state_write(
            RWTableTag.Account,
            account_address,
            FQ(account_field_tag),
            reversion_info=reversion_info,
        )
        return row.value, row.value_prev

    def add_balance(
        self,
        account_address: Expression,
        values: Sequence[RLC],
        reversion_info: ReversionInfo = None,
    ) -> Tuple[RLC, RLC]:
        value, value_prev = self.account_write(
            account_address, AccountFieldTag.Balance, reversion_info
        )
        balance, balance_prev = cast_expr(value, RLC), cast_expr(value_prev, RLC)
        result, carry = self.add_words([balance_prev, *values])
        self.constrain_equal(balance, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def sub_balance(
        self,
        account_address: Expression,
        values: Sequence[RLC],
        reversion_info: ReversionInfo = None,
    ) -> Tuple[RLC, RLC]:
        value, value_prev = self.account_write(
            account_address, AccountFieldTag.Balance, reversion_info
        )
        balance, balance_prev = cast_expr(value, RLC), cast_expr(value_prev, RLC)
        result, carry = self.add_words([balance, *values])
        self.constrain_equal(balance_prev, result)
        self.constrain_zero(carry)
        return balance, balance_prev

    def account_storage_read(
        self, account_address: Expression, storage_key: Expression, tx_id: Expression
    ) -> RLC:
        row = self.rw_lookup(
            RW.Read,
            RWTableTag.AccountStorage,
            account_address,
            storage_key,
            aux0=tx_id,
        )
        return cast_expr(row.value, RLC)

    def account_storage_write(
        self,
        account_address: Expression,
        storage_key: Expression,
        tx_id: Expression,
        reversion_info: ReversionInfo = None,
    ) -> Tuple[RLC, RLC, RLC]:
        row = self.state_write(
            RWTableTag.AccountStorage,
            account_address,
            storage_key,
            aux0=tx_id,
            reversion_info=reversion_info,
        )
        return cast_expr(row.value, RLC), cast_expr(row.value_prev, RLC), cast_expr(row.aux1, RLC)

    def add_account_to_access_list(
        self, tx_id: Expression, account_address: Expression, reversion_info: ReversionInfo = None
    ) -> FQ:
        row = self.state_write(
            RWTableTag.TxAccessListAccount,
            tx_id,
            account_address,
            value=FQ(1),
            reversion_info=reversion_info,
        )
        return row.value_prev.expr()

    def add_account_storage_to_access_list(
        self,
        tx_id: Expression,
        account_address: Expression,
        storage_key: Expression,
        reversion_info: ReversionInfo = None,
    ) -> FQ:
        row = self.state_write(
            RWTableTag.TxAccessListAccountStorage,
            tx_id,
            account_address,
            storage_key,
            value=FQ(1),
            reversion_info=reversion_info,
        )
        return row.value_prev.expr()

    def transfer_with_gas_fee(
        self,
        sender_address: Expression,
        receiver_address: Expression,
        value: RLC,
        gas_fee: RLC,
        reversion_info: ReversionInfo = None,
    ) -> Tuple[Tuple[RLC, RLC], Tuple[RLC, RLC]]:
        sender_balance_pair = self.sub_balance(sender_address, [value, gas_fee], reversion_info)
        receiver_balance_pair = self.add_balance(receiver_address, [value], reversion_info)
        return sender_balance_pair, receiver_balance_pair

    def transfer(
        self,
        sender_address: Expression,
        receiver_address: Expression,
        value: RLC,
        reversion_info: ReversionInfo = None,
    ) -> Tuple[Tuple[RLC, RLC], Tuple[RLC, RLC]]:
        sender_balance_pair = self.sub_balance(sender_address, [value], reversion_info)
        receiver_balance_pair = self.add_balance(receiver_address, [value], reversion_info)
        return sender_balance_pair, receiver_balance_pair

    def memory_offset_and_length(self, offset_word: RLC, length_word: RLC) -> Tuple[FQ, FQ]:
        length = self.rlc_to_fq_exact(length_word, N_BYTES_MEMORY_ADDRESS)
        if self.is_zero(length) == 1:
            return FQ(0), FQ(0)
        offset = self.rlc_to_fq_exact(offset_word, N_BYTES_MEMORY_ADDRESS)
        return offset, length

    def memory_gas_cost(self, memory_size: Expression) -> FQ:
        quadratic_cost, _ = self.constant_divmod(
            memory_size.expr() * memory_size.expr(),
            FQ(MEMORY_EXPANSION_QUAD_DENOMINATOR),
            N_BYTES_GAS,
        )
        linear_cost = memory_size.expr() * MEMORY_EXPANSION_LINEAR_COEFF
        return quadratic_cost + linear_cost

    def memory_expansion_constant_length(
        self, offset: Expression, length: Expression
    ) -> Tuple[FQ, FQ]:
        memory_size, _ = self.constant_divmod(
            length.expr() + offset.expr() + 31, FQ(32), N_BYTES_MEMORY_SIZE
        )

        next_memory_size = self.max(self.curr.memory_size, memory_size, N_BYTES_MEMORY_SIZE)

        memory_gas_cost = self.memory_gas_cost(self.curr.memory_size)
        memory_gas_cost_next = self.memory_gas_cost(next_memory_size)
        memory_expansion_gas_cost = memory_gas_cost_next - memory_gas_cost

        return cast_expr(next_memory_size, FQ), cast_expr(memory_expansion_gas_cost, FQ)

    def memory_expansion_dynamic_length(
        self,
        cd_offset: Expression,
        cd_length: Expression,
        rd_offset: Optional[Expression] = None,
        rd_length: Optional[Expression] = None,
    ) -> Tuple[FQ, FQ]:
        cd_memory_size, _ = self.constant_divmod(
            cd_offset.expr() + cd_length.expr() + FQ(31), FQ(32), N_BYTES_MEMORY_SIZE
        )
        next_memory_size = self.max(self.curr.memory_size, cd_memory_size, N_BYTES_MEMORY_SIZE)

        if rd_offset is not None and rd_length is not None:
            rd_memory_size, _ = self.constant_divmod(
                rd_offset.expr() + rd_length.expr() + FQ(31), FQ(32), N_BYTES_MEMORY_SIZE
            )
            next_memory_size = self.max(next_memory_size, rd_memory_size, N_BYTES_MEMORY_SIZE)

        memory_gas_cost = self.memory_gas_cost(self.curr.memory_size)
        memory_gas_cost_next = self.memory_gas_cost(next_memory_size)
        memory_expansion_gas_cost = memory_gas_cost_next - memory_gas_cost

        return cast_expr(next_memory_size, FQ), cast_expr(memory_expansion_gas_cost, FQ)

    def memory_copier_gas_cost(
        self, length: Expression, memory_expansion_gas_cost: Expression
    ) -> FQ:
        word_size, _ = self.constant_divmod(length + FQ(31), FQ(32), N_BYTES_MEMORY_SIZE)
        gas_cost = word_size * GAS_COST_COPY + memory_expansion_gas_cost
        self.range_check(gas_cost, N_BYTES_GAS)
        return gas_cost
