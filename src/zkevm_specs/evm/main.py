from .step import Step
from .execution_result import (
    ExecutionResult,
    add,
    begin_tx,
    push,
    call,
    error_invalid_opcode,
    error_stack_overflow,
    error_stack_underflow,
    error_depth,
)


def main(curr: Step, next: Step, r: int, is_first_step: bool, is_final_step: bool):
    if is_first_step or curr.core.execution_result == ExecutionResult.BEGIN_TX:
        begin_tx(curr, next, r, is_first_step)
    else:
        opcode = curr.opcode_lookup()

        # opcode's successful cases
        if curr.core.execution_result == ExecutionResult.ADD:
            add(curr, next, r, opcode)
        elif curr.core.execution_result == ExecutionResult.PUSH:
            push(curr, next, r, opcode)
        elif curr.core.execution_result == ExecutionResult.CALL:
            call(curr, next, r, opcode)
        # error cases
        elif curr.core.execution_result == ExecutionResult.ERROR_INVALID_CODE:
            error_invalid_opcode(curr, next, r, opcode)
        elif curr.core.execution_result == ExecutionResult.ERROR_STACK_OVERFLOW:
            error_stack_overflow(curr, next, r, opcode)
        elif curr.core.execution_result == ExecutionResult.ERROR_STACK_UNDERFLOW:
            error_stack_underflow(curr, next, r, opcode)
        elif curr.core.execution_result == ExecutionResult.ERROR_DEPTH:
            error_depth(curr, next, r, opcode)
        else:
            raise NotImplementedError

    if is_final_step:
        # Verify no malicious insertion
        assert curr.core.rw_counter == len(curr.tables.rw_table)

        # TODO: Verify final step has the tx_id identical to the amount in tx_table
