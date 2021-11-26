from typing import Optional, Sequence

from ..util.arithmetic import RLCStore
from .execution import (
    add,
    begin_tx,
    push,
    # call,
    # error_invalid_opcode,
    # error_stack_overflow,
    # error_stack_underflow,
    # error_depth,
)
from .execution_result import ExecutionResult
from .instruction import Instruction
from .step import StepState
from .table import Tables


def verify_steps(
    rlc_store: RLCStore,
    tables: Tables,
    steps: Sequence[StepState],
    begin_with_first_step: bool = False,
    end_with_final_step: bool = False,
):
    for idx in range(len(steps)-1):
        verify_step(
            Instruction(rlc_store=rlc_store, tables=tables, curr=steps[idx], next=steps[idx+1]),
            begin_with_first_step and idx == 0,
            end_with_final_step and idx == len(steps)-2,
        )


def verify_step(
    instruction: Instruction,
    is_first_step: bool = False,
    is_final_step: bool = False,
):
    if is_first_step:
        instruction.constrain_equal(instruction.curr.execution_result, ExecutionResult.BEGIN_TX)

    if instruction.curr.execution_result == ExecutionResult.BEGIN_TX:
        begin_tx(instruction, is_first_step)
    # opcode's successful cases
    elif instruction.curr.execution_result == ExecutionResult.ADD:
        add(instruction)
    elif instruction.curr.execution_result == ExecutionResult.PUSH:
        push(instruction)
    # elif instruction.curr.execution_result == ExecutionResult.CALL:
    #     call(instruction)
    # error cases
    # elif instruction.curr.execution_result == ExecutionResult.ERROR_INVALID_CODE:
    #     error_invalid_opcode(instruction)
    # elif instruction.curr.execution_result == ExecutionResult.ERROR_STACK_OVERFLOW:
    #     error_stack_overflow(instruction)
    # elif instruction.curr.execution_result == ExecutionResult.ERROR_STACK_UNDERFLOW:
    #     error_stack_underflow(instruction)
    # elif instruction.curr.execution_result == ExecutionResult.ERROR_DEPTH:
    #     error_depth(instruction)
    else:
        raise NotImplementedError

    if is_final_step:
        # Verify no malicious insertion
        assert instruction.curr.rw_counter == len(instruction.tables.rw_table)

        # TODO: Verify final step has the tx_id identical to the amount in tx_table
