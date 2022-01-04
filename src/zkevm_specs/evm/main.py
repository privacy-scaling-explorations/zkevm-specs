from typing import Sequence

from ..util.arithmetic import RLCStore
from .execution import (
    add,
    begin_tx,
    push,
    jump,
    jumpi,
    sload,
    sstore
)
from .execution_state import ExecutionState
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
    for idx in range(len(steps) - 1):
        verify_step(
            Instruction(rlc_store=rlc_store, tables=tables, curr=steps[idx], next=steps[idx + 1]),
            begin_with_first_step and idx == 0,
            end_with_final_step and idx == len(steps) - 2,
        )


def verify_step(
    instruction: Instruction,
    is_first_step: bool = False,
    is_final_step: bool = False,
):
    if is_first_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.BeginTx)

    if instruction.curr.execution_state == ExecutionState.BeginTx:
        begin_tx(instruction, is_first_step)
    # Opcode's successful cases
    elif instruction.curr.execution_state == ExecutionState.ADD:
        add(instruction)
    elif instruction.curr.execution_state == ExecutionState.PUSH:
        push(instruction)
    elif instruction.curr.execution_state == ExecutionState.JUMP:
        jump(instruction)
    elif instruction.curr.execution_state == ExecutionState.JUMPI:
        jumpi(instruction)
    elif instruction.curr.execution_state == ExecutionState.SLOAD:
        sload(instruction)
    elif instruction.curr.execution_state == ExecutionState.SSTORE:
        sstore(instruction)
    # Error cases
    else:
        raise NotImplementedError

    if is_final_step:
        # Verify no malicious insertion
        assert instruction.curr.rw_counter == len(instruction.tables.rw_table)

        # TODO: Verify final step has the tx_id identical to the amount in tx_table
