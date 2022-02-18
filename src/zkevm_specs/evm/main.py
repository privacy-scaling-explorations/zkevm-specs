from typing import Sequence

from ..util import FQ
from .execution import EXECUTION_STATE_IMPL
from .execution_state import ExecutionState
from .instruction import Instruction
from .step import StepState
from .table import Tables


def verify_steps(
    randomness: FQ,
    tables: Tables,
    steps: Sequence[StepState],
    begin_with_first_step: bool = False,
    end_with_last_step: bool = False,
):
    # TODO: Enforce general ExecutionState transition constraint

    for idx in range(len(steps) if end_with_last_step else len(steps) - 1):
        verify_step(
            Instruction(
                randomness=randomness,
                tables=tables,
                curr=steps[idx],
                next=steps[idx + 1] if idx + 1 < len(steps) else None,
                is_first_step=begin_with_first_step and idx == 0,
                is_last_step=idx + 1 == len(steps),
            ),
        )


def verify_step(
    instruction: Instruction,
):
    if instruction.is_first_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.BeginTx)

    if instruction.curr.execution_state in EXECUTION_STATE_IMPL:
        EXECUTION_STATE_IMPL[instruction.curr.execution_state](instruction)
    else:
        raise NotImplementedError

    if instruction.is_last_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.EndBlock)
