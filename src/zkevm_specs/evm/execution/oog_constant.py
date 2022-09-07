from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..execution_state import ExecutionState
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def oog_constant(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.curr.aux_data

    # check gas left is less than const gas required
    gas_not_enough, _ = instruction.compare(
        instruction.curr.gas_left, FQ(Opcode(opcode.expr().n).constant_gas_cost()), N_BYTES_GAS
    )
    instruction.constrain_equal(gas_not_enough, FQ(1))

    # current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    if instruction.curr.is_root:
        # When a transaction ends with this error state, this call must not be persistent
        is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
        instruction.constrain_equal(is_persistent, FQ(0))
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(2),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=1,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
