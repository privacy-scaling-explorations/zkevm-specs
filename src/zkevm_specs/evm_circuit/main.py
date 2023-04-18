from typing import List

from ..util import FQ
from .execution import EXECUTION_STATE_IMPL
from .execution_state import ExecutionState
from .instruction import Instruction
from .step import StepState
from .table import Tables


DUMMY_STEP_STATE = StepState(ExecutionState.EndBlock, rw_counter=-1)


def verify_steps(
    tables: Tables,
    steps: List[StepState],
    begin_with_first_step: bool = False,
    end_with_last_step: bool = False,
    success: bool = True,
):
    if end_with_last_step:
        steps.append(DUMMY_STEP_STATE)

    exception = None
    for idx, (curr, next) in enumerate(zip(steps, steps[1:])):
        try:
            verify_step(
                Instruction(
                    tables=tables,
                    curr=curr,
                    next=next,
                    is_first_step=begin_with_first_step and idx == 0,
                    is_last_step=end_with_last_step and idx == len(steps) - 2,
                )
            )
        except AssertionError as e:
            exception = e
            break
    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


def verify_step(instruction: Instruction):
    if instruction.is_first_step:
        instruction.constrain_in(
            instruction.curr.execution_state,
            [FQ(ExecutionState.BeginTx), FQ(ExecutionState.EndBlock)],
        )
        instruction.constrain_equal(instruction.curr.rw_counter, FQ(1))

    if instruction.is_last_step:
        instruction.constrain_equal(instruction.curr.execution_state, ExecutionState.EndBlock)
    else:
        instruction.constrain_execution_state_transition()

    if instruction.curr.execution_state in EXECUTION_STATE_IMPL:
        EXECUTION_STATE_IMPL[instruction.curr.execution_state](instruction)
    else:
        raise NotImplementedError
