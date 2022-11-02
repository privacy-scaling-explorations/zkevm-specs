from ...util import FQ
from ..instruction import Instruction, Transition, FixedTableTag
from ..table import CallContextFieldTag
from ..execution_state import ExecutionState
from ..opcode import Opcode
from ...util import N_BYTES_GAS, N_BYTES_STACK


def stack_error(instruction: Instruction):
    # retrieve op code associated to stack error
    opcode = instruction.opcode_lookup(True)
    # TODO: lookup min or max stack pointer
    max_stack_pointer = FQ(Opcode(opcode.expr().n).max_stack_pointer())
    min_stack_pointer = Opcode(opcode.expr().n).min_stack_pointer()
    min_stack_pointer = FQ(min_stack_pointer if min_stack_pointer > 0 else 0)
    instruction.fixed_lookup(
        FixedTableTag.OpcodeStack, opcode, min_stack_pointer, max_stack_pointer
    )

    # check stack pointer is underflow or overflow
    is_overflow, _ = instruction.compare(
        instruction.curr.stack_pointer, FQ(min_stack_pointer), N_BYTES_STACK
    )
    is_underflow, _ = instruction.compare(
        FQ(max_stack_pointer), instruction.curr.stack_pointer, N_BYTES_STACK
    )
    instruction.constrain_bool(is_underflow)
    instruction.constrain_bool(is_overflow)

    # constrain one of [is_underflow, is_overflow] must be true when stack error happens
    instruction.constrain_equal(is_underflow + is_overflow, FQ(1))

    # current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(1 + instruction.curr.reversible_write_counter),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=1 + instruction.curr.reversible_write_counter.n,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
