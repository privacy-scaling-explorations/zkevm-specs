from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..execution_state import ExecutionState


def stop(instruction: Instruction):
    # Note when transition to STOP, program_counter can only be increased by 1,
    # (JUMP* will always transit to JUMPDEST, then to STOP if any) so when opcode
    # fetching is out of range, the program_counter must be equal to code_length.
    code_length = instruction.bytecode_length(instruction.curr.code_hash)
    is_out_of_range = instruction.is_equal(code_length, instruction.curr.program_counter)
    if is_out_of_range == FQ(0):
        instruction.responsible_opcode_lookup(instruction.opcode_lookup(True))

    # When a call ends with STOP, this call must be successful, but it's not
    # necessary persistent depends on if it's a sub-call of a failed call or not.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess).value()
    instruction.constrain_equal(is_success, FQ(1))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(1),
            call_id=Transition.same(),
        )
    else:
        # There are 2 possible branch for internal call:
        # 1. is_create:
        #   STOP returns empty bytes as deployment code, but when it's an internal creation call,
        #   the code_hash of callee must already be random linear combination of EMPTY_CODE_HASH,
        #   which doesn't need any update here.
        # 2. not is_create:
        #   STOP returns empty bytes as return_data, which doesn't affect caller's memory at all.
        # So we only need to restore caller's state as finishing this call.

        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=1,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
