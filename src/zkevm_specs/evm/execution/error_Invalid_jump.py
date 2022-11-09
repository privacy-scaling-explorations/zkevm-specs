from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..execution_state import ExecutionState
from ..opcode import Opcode
from ...util import N_BYTES_PROGRAM_COUNTER


def invalid_jump(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # current executing op code must be JUMP or JUMPI
    instruction.constrain_in(opcode, [FQ(Opcode.JUMP), FQ(Opcode.JUMPI)])
    _, is_jumpi = instruction.pair_select(opcode, Opcode.JUMP, Opcode.JUMPI)
    code_length = instruction.bytecode_length(instruction.curr.code_hash)
    dest = instruction.stack_pop()
    # if `JUMPI`, pop `condition`
    if is_jumpi == FQ(1):
        condition = instruction.stack_pop()
        # if condition is zero, jump will not happen, so constrain condition not zero
        instruction.constrain_not_zero(condition)
    # lookup value from bytecode table
    dest_value = instruction.rlc_to_fq(dest, N_BYTES_PROGRAM_COUNTER)

    within_range, _ = instruction.compare(dest_value, code_length, N_BYTES_PROGRAM_COUNTER)

    # if not out of range, check `dest` is invalid
    if within_range == FQ(1):
        value, is_code = instruction.bytecode_lookup_pair(instruction.curr.code_hash, dest_value)
        # value is not `JUMPDEST` or `is_code` is false
        is_jump_dest = value == Opcode.JUMPDEST
        instruction.constrain_zero(is_code * FQ(is_jump_dest))

    # current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(2 + is_jumpi.n + instruction.curr.reversible_write_counter),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=2 + is_jumpi.n + instruction.curr.reversible_write_counter.n,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
