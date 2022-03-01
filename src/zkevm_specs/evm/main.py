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
    # For the last step, the next step is meaningless
    if end_with_last_step:
        steps += [None]

    for idx in range(len(steps) - 1):
        curr, next = steps[idx], steps[idx + 1]

        verify_step(
            Instruction(
                randomness=randomness,
                tables=tables,
                curr=curr,
                next=next,
                is_first_step=begin_with_first_step and idx == 0,
                is_last_step=end_with_last_step and next is None,
            )
        )


def verify_step(instruction: Instruction):
    if instruction.is_first_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.BeginTx)

    if instruction.curr.execution_state in EXECUTION_STATE_IMPL:
        EXECUTION_STATE_IMPL[instruction.curr.execution_state](instruction)
    else:
        raise NotImplementedError

    if instruction.is_last_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.EndBlock)
    else:
        instruction.constrain_execution_state_transition()
