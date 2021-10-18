from ..common_assert import assert_bool
from ..opcode import Opcode
from ..step import Step
from ..table import FixedTableTag
from .execution_result import ExecutionResult


def push(curr: Step, next: Step, r: int, opcode: Opcode):
    selectors = curr.allocate_bool(32)

    # Verify opcode
    num_pushed = opcode - Opcode.PUSH1 + 1
    curr.fixed_lookup(FixedTableTag.Range32, [num_pushed])

    # Verify gas
    next_gas_left = curr.assert_sufficient_constant_gas(opcode)

    value = curr.stack_push_lookup()
    bytes_value = curr.decompress(value, 32, r)

    assert sum(selectors) == num_pushed
    for i, byte in enumerate(bytes_value):
        if i > 0:
            assert_bool(selectors[i - 1] - selectors[i])
        if selectors[i]:
            assert byte == curr.opcode_lookup(i + 1)
        else:
            assert bytes_value[i] == 0

    curr.assert_step_transition(
        next,
        rw_counter_diff=curr.rw_counter_diff,
        execution_result_not=ExecutionResult.BEGIN_TX,
        program_counter_diff=num_pushed + 1,
        stack_pointer_diff=curr.stack_pointer_diff,
        gas_left=next_gas_left,
    )
