from ..common_assert import assert_addition
from ..opcode import Opcode
from ..step import Step
from .execution_result import ExecutionResult


def add(curr: Step, next: Step, r: int, opcode: Opcode):
    swap, *carries = curr.allocate_bool(33)

    # Verify opcode
    assert opcode == (Opcode.SUB if swap else Opcode.ADD)

    # Verify gas
    next_gas_left = curr.assert_sufficient_constant_gas(opcode)

    a = curr.stack_pop_lookup()
    b = curr.stack_pop_lookup()
    c = curr.stack_push_lookup()
    bytes_a = curr.decompress(a, 32, r)
    bytes_b = curr.decompress(c if swap else b, 32, r)
    bytes_c = curr.decompress(b if swap else c, 32, r)

    assert_addition(bytes_a, bytes_b, bytes_c, carries)

    curr.assert_step_transition(
        next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
        program_counter_diff=1,
        stack_pointer_diff=curr.stack_pointer_diff,
        gas_left=next_gas_left,
    )
