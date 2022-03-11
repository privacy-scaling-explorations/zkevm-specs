from ...util import FQ, N_BYTES_PROGRAM_COUNTER
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def jumpi(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.JUMPI)

    # Do not check 'dest' is within MaxCodeSize(24576) range in successful case
    # as byte code lookup can ensure it.
    dest = instruction.stack_pop()
    cond = instruction.stack_pop()

    # check `cond` is zero or not
    if instruction.is_zero(cond):
        pc_diff = FQ(1)
    else:
        # Get `dest` raw value in max 8 bytes
        dest_value = instruction.rlc_to_fq_exact(dest, N_BYTES_PROGRAM_COUNTER)
        pc_diff = dest_value - instruction.curr.program_counter
        # assert Opcode.JUMPDEST == instruction.opcode_lookup_at(dest_value, True)
        instruction.constrain_equal(Opcode.JUMPDEST, instruction.opcode_lookup_at(dest_value, True))

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(2),
        program_counter=Transition.delta(pc_diff),
        stack_pointer=Transition.delta(2),
    )
