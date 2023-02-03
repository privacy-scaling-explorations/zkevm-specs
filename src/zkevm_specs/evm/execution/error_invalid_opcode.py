from ...util import FQ
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag


# Gadget for invalid opcodes. It verifies by a fixed lookup for ResponsibleOpcode.
def invalid_opcode(instruction: Instruction):
    # Fixed lookup for invalid opcode.
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode)

    # Current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root.
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    # When it's a root call.
    if instruction.curr.is_root:
        # Do step state transition.
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(1 + instruction.curr.reversible_write_counter),
            call_id=Transition.same(),
        )
    else:
        # When it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState.
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=1 + instruction.curr.reversible_write_counter.n,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
